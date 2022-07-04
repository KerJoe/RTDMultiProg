from ..InterfaceBase import InterfaceBase
from ..SoftwareI2C import SoftwareI2C
from ctypes import *
import os
import sys

class I2C(InterfaceBase):
    AvailableSystems = [ "Windows" ]
    AvailableArchitectures = [ "32bit", "64bit" ]
    HelpText = [ "Bitbangs the parrallel port.\n" +
                 "Settings:\n" +
                 "  -s \"SDAOutputPin SCLOutputPin SDAInputPin SCLInputpin\"\n" +
                 "Possible output pin values:\n" +
                 "  D0, D1, D2, D3, D3, D4, D5, D6, D7, STROBE, FEED, SELPRINTER, RESET\n" +
                 "Possible input pin values:\n" +
                 "  ACK, BUSY, PAPER, SELIN, ERROR\n"
                 "Default:\n" +
                 "  -s \"D7 SELPRINTER BUSY ERROR\"" ]


    DATA_PORT_OFFSET    = 0
    STATUS_PORT_OFFSET  = 1
    CONTROL_PORT_OFFSET = 2

    PIN_MAP =  {
        # 1 - Offset, 2 - Bit, 3 - If False then invert
        "D0": (DATA_PORT_OFFSET, 0, True),
        "D1": (DATA_PORT_OFFSET, 1, True),
        "D2": (DATA_PORT_OFFSET, 2, True),
        "D3": (DATA_PORT_OFFSET, 3, True),
        "D4": (DATA_PORT_OFFSET, 4, True),
        "D5": (DATA_PORT_OFFSET, 5, True),
        "D6": (DATA_PORT_OFFSET, 6, True),
        "D7": (DATA_PORT_OFFSET, 7, True),

        "ERROR": (STATUS_PORT_OFFSET, 3, True),
        "SELIN": (STATUS_PORT_OFFSET, 4, True),
        "PAPER": (STATUS_PORT_OFFSET, 5, True),
        "ACK":   (STATUS_PORT_OFFSET, 6, True),
        "BUSY":  (STATUS_PORT_OFFSET, 7, False),

        "STROBE":     (DATA_PORT_OFFSET, 0, False),
        "FEED":       (DATA_PORT_OFFSET, 1, False),
        "RESET":      (DATA_PORT_OFFSET, 2, True),
        "SELPRINTER": (DATA_PORT_OFFSET, 3, False),
    }

    In32  = None
    Out32 = None
    si2c  = SoftwareI2C()
    lptAddress = 0

    SDAOutputPin = "D7"
    SCLOutputPin = "SELPRINTER"
    SDAInputPin  = "BUSY"
    SCLInputPin  = "ERROR"


    def SetPin(self, pin, state):
        value = self.In32(self.lptAddress + pin[0]) & ~(1 << pin[1]) | ((state ^ (not pin[2])) << pin[1])
        self.Out32(c_short(self.lptAddress + pin[0]), value)

    def GetPin(self, pin):
        value = ((self.In32(self.lptAddress + pin[0]) >> pin[1]) & 1) ^ (not pin[2])
        return bool(value)

    def __init__(self):
        if (sys.maxsize > 2**32): # System is 64 bit
            inpout = cdll.LoadLibrary(os.path.dirname(__file__) + "\\inpoutx64.dll")
        else: # System is 32 bit
            inpout = cdll.LoadLibrary(os.path.dirname(__file__) + "\\inpout32.dll")
        retval = self.inpout.IsInpOutDriverOpen()
        if (retval == 0):
            raise SystemError("Failed to install/find INPOUT driver. Try running: \"" + os.path.dirname(__file__) + "\\InstallDriver.exe\"")
        self.In32 = inpout.In32
        self.In32.argtypes = [ c_short ]
        self.In32.restype  = c_short
        self.Out32 = inpout.Out32
        self.Out32.argtypes = [ c_short, c_short ]

    def list_i2c(self):
        return { 0x3BC: "LPT1", 0x378: "LPT2", 0x278: "LPT3" }

    def init_i2c(self, device, settings):
        retval = self.i2ci.I2CInit(device, 0)
        if (retval == 0):
            raise ConnectionError("Failed to initialize I2C")

    def write_i2c(self, address, data):
        if (type(data) == int):
            data = [ data ]
        dat  = (c_ubyte * len(data))(*data)
        retval = self.i2ci.I2CWrite(c_ubyte(address << 1), dat, c_uint32(len(data)))
        pass

    def read_i2c(self, address, count):
        dat  = (c_ubyte * count)(*([0] * count)) #
        retval = self.i2ci.I2CRead(c_ubyte((address << 1) | 1), dat, c_uint32(count))
        data = [i for i in dat]
        return data
        pass