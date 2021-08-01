from ctypes import *
from posixpath import basename
import sys
import os
from . import queryCodes
from .._common_.interfaceBase import interfaceBase

class I2C(interfaceBase):
    nvapi = None

    NVAPI_MAX_PHYSICAL_GPUS = 64
    NVAPI_MAX_DISPLAY_HEADS = 2
    NVAPI_MAX_DISPLAYS = NVAPI_MAX_PHYSICAL_GPUS * NVAPI_MAX_DISPLAY_HEADS
    NVAPI_I2C_SPEED_DEPRECATED = 0xFFFF

    NvPhysicalGpuHandle__ = c_int
    NvPhysicalGpuHandle = POINTER(NvPhysicalGpuHandle__)
    PNvPhysicalGpuHandle = POINTER(NvPhysicalGpuHandle)
    NvDisplayHandle__ = c_int
    NvDisplayHandle = POINTER(NvDisplayHandle__)
    PNvDisplayHandle = POINTER(NvDisplayHandle)
    PNvU32 = POINTER(c_uint32)
    PNvU16 = POINTER(c_uint16)
    PNvU8  = POINTER(c_uint8)
    NvU32 = c_uint32
    NvU16 = c_uint16
    NvU8  = c_uint8
    NV_I2C_SPEED = c_int
    class NV_I2C_INFO__(Structure):
        _fields_ = [("version",         c_uint32), # NvU32
                    ("displayMask",     c_uint32), # NvU32
                    ("bIsDDCPort",      c_uint8),  # NvU8
                    ("i2cDevAddress",   c_uint8),  # NvU8
                    ("pbI2cRegAddress", POINTER(c_uint8)), # PNvU8
                    ("regAddrSize",     c_uint32), # NvU32
                    ("pbData",          POINTER(c_uint8)),  # PNvU8
                    ("cbSize",          c_uint32), # NvU32
                    ("i2cSpeed",        c_uint32)] # NvU32
    NV_I2C_INFO = POINTER(NV_I2C_INFO__)

    i2cInfo = NV_I2C_INFO__()

    hGpus = (NvPhysicalGpuHandle * NVAPI_MAX_PHYSICAL_GPUS)()
    gpuCount = NvU32(0)
    hGpu  = NvPhysicalGpuHandle()

    hDisplays = (NvDisplayHandle * NVAPI_MAX_DISPLAYS)()
    displayCount = 0

    outputIDs = None

    nvapiFunc = {}
    nvapiFuncQuery = {
        "NvAPI_Initialize":
            [ queryCodes._NvAPI_Initialize, [] ],
        "NvAPI_EnumNvidiaDisplayHandle":
            [ queryCodes._NvAPI_EnumNvidiaDisplayHandle, [ NvU32, PNvDisplayHandle ] ],
        "NvAPI_GetPhysicalGPUsFromDisplay":
            [ queryCodes._NvAPI_GetPhysicalGPUsFromDisplay, [ NvDisplayHandle, PNvPhysicalGpuHandle, PNvU32 ] ],
        "NvAPI_GetAssociatedDisplayOutputId":
            [ queryCodes._NvAPI_GetAssociatedDisplayOutputId, [ NvDisplayHandle, PNvU32 ] ],
        "NvAPI_I2CWrite":
            [ queryCodes._NvAPI_I2CWrite, [ NvPhysicalGpuHandle, NV_I2C_INFO ] ],
        "NvAPI_I2CRead":
            [ queryCodes._NvAPI_I2CRead, [ NvPhysicalGpuHandle, NV_I2C_INFO ] ]
    }

    AvailableSystems = [ "Windows" ]
    AvailableArchitectures = [ "32bit", "64bit" ]

    def getNvapiFunction(self, code, argTypes):
        self.nvapi.nvapi_QueryInterface.restype = c_void_p
        funcPtr = self.nvapi.nvapi_QueryInterface(c_uint(code))
        functype = CFUNCTYPE(c_int, *argTypes)
        return functype(funcPtr)

    def __init__(self):
        if (sys.maxsize > 2**32): # System is 64 bit
            self.nvapi = cdll.LoadLibrary("nvapi64.dll")
        else: # System is 32 bit
            self.nvapi = cdll.LoadLibrary("nvapi.dll")

        for func in self.nvapiFuncQuery:
            self.nvapiFunc[func] = self.getNvapiFunction(self.nvapiFuncQuery[func][0], self.nvapiFuncQuery[func][1])

        retCode = self.nvapiFunc["NvAPI_Initialize"]()
        if retCode != 0:
            raise ConnectionError("NvAPI_Initialize error. Return code: {0}".format(retCode))

        while True:
            retCode = self.nvapiFunc["NvAPI_EnumNvidiaDisplayHandle"](self.NvU32(self.displayCount), cast(byref(self.hDisplays, sizeof(self.NvDisplayHandle) * self.displayCount), self.PNvDisplayHandle))
            if retCode == 0:
                self.displayCount = self.displayCount + 1
            else:
                if retCode == -7: # NVAPI_END_ENUMERATION
                    break
                else:
                    raise ConnectionError("NvAPI_EnumNvidiaDisplayHandle error. Return code: {0}".format(retCode))

        self.outputIDs = (self.NvU32 * self.displayCount)()
        for i in range(self.displayCount):
            retCode = self.nvapiFunc["NvAPI_GetPhysicalGPUsFromDisplay"](self.hDisplays[i], byref(self.hGpu), byref(self.gpuCount))
            if retCode != 0:
                raise ConnectionError("NvAPI_GetPhysicalGPUsFromDisplay error. Return code: {0}".format(retCode))
            retCode = self.nvapiFunc["NvAPI_GetAssociatedDisplayOutputId"](self.hDisplays[i], cast(byref(self.outputIDs, sizeof(self.NvU32) * i), self.PNvU32))
            if retCode != 0:
                raise ConnectionError("NvAPI_GetAssociatedDisplayOutputId error. Return code: {0}".format(retCode))

        self.i2cInfo.version         = 0x10030 # Possible values: 1 - 0x10030, 2 - 0x20038, 3 - 0x30040
        self.i2cInfo.bIsDDCPort      = True
        self.i2cInfo.i2cDevAddress   = 0x4A << 1
        self.i2cInfo.pbI2cRegAddress = cast(pointer((c_uint8 * 2)(0x6F, 0x80)), POINTER(c_uint8))
        self.i2cInfo.regAddrSize     = 0
        self.i2cInfo.pbData          = cast(pointer((c_uint8 * 2)(0x6F, 0x80)), POINTER(c_uint8))
        self.i2cInfo.cbSize          = 2
        self.i2cInfo.i2cSpeed        = 27

    def ListI2C(self):
        return { k:("Display" + str(k)) for k in range(self.displayCount) }

    def InitI2C(self, device):
        self.i2cInfo.displayMask = self.outputIDs[device]

    def WriteI2C(self, address, data):
        self.i2cInfo.i2cDevAddress = address << 1
        dat = (c_uint8 * len(data))(*data)
        self.i2cInfo.pbData = dat
        self.i2cInfo.cbSize = len(data)

        retCode = self.nvapiFunc["NvAPI_I2CWrite"](self.hGpu, byref(self.i2cInfo))
        if retCode != 0:
            raise ConnectionError("NvAPI_I2CWrite error. Return code: {0}".format(retCode))

    def ReadI2C(self, address, count):
        dat  = (c_ubyte * count)(*([0] * count))
        self.i2cInfo.pbData = dat
        self.i2cInfo.cbSize = count

        retCode = self.nvapiFunc["NvAPI_I2CRead"](self.hGpu, byref(self.i2cInfo))
        if retCode != 0:
            raise ConnectionError("NvAPI_I2CRead error. Return code: {0}".format(retCode))

        return self.i2cInfo.pbData