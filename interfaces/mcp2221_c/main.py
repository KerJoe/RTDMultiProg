import usb, platform, os, re
from interfaces.interface_base import InterfaceBase
from ctypes import *

class I2C(InterfaceBase):
    HELP_TEXT = ("The MCP2221 is a USB-to-UART/I2C serial converter "
                 "which enables USB connectivity in applications that "
                 "have a UART and I2C interfaces.\n"
                 "NOTE: This implementation uses a compiled C library.\n"
                 "NOTE: This implementation bypasses the HID interface "
                 "and accesses device directly using libusb,")
    MAXIMUM_READ_AMOUNT  = 60
    MAXIMUM_WRITE_AMOUNT = 60


    _lib = None
    _handle = c_void_p()

    _MCP2221_VID = 0x04D8
    _MCP2221_PID = 0x00DD


    def __init__(self):
        # Create list of libraries in the interface folder
        libs = [ fn for fn in os.listdir(os.path.dirname(__file__)) if re.match('main\..+\.(so|dll)', fn)]
        # Windows machine to GNU triplet dictionary
        win_dict = { "AMD64":"x86_64", "x86":"i386" }
        # Find one according to our system
        lib_name = None
        for name in libs:
            if platform.system() == "Windows":
                if f'{win_dict[platform.machine()]}-' in name:
                    if "mingw" in name:
                        lib_name = name
                        break
            else:
                if f'{platform.machine()}-' in name:
                    if platform.system().lower() in name:
                        lib_name = name
                        break
        if lib_name == None:
            raise FileNotFoundError("Unable to find the library for current the architecture.")

        self._lib = cdll.LoadLibrary(f"{os.path.dirname(__file__)}{os.sep}{lib_name}")
        self._lib.begin()

    def __del__(self):
        self._lib.end()

    def list_i2c(self):
        dev_list_ = usb.core.find(idVendor=self._MCP2221_VID, idProduct=self._MCP2221_PID, find_all=True)
        dev_list  = {}
        for dev_n, dev in enumerate(sorted(dev_list_)):
            dev_list[dev_n] = f"MCP2221 on bus {dev.bus} device {dev.address}"
        return dev_list

    def init_i2c(self, device, settings):
        dev_adr = sorted(usb.core.find(idVendor=self._MCP2221_VID, idProduct=self._MCP2221_PID, find_all=True))[device].address
        r = self._lib.init_i2c(byref(self._handle), dev_adr)
        if r:
            raise ConnectionError(f"Runtime library error: {r}")

    def deinit_i2c(self):
        self._lib.deinit_i2c(self._handle)

    def write_i2c(self, address, data):
        dat = (c_uint8 * len(data))(*data)
        r = self._lib.write_i2c(self._handle, c_uint8(address), dat, c_uint16(len(data)))
        if r:
            raise ConnectionError(f"Runtime library error: {r}")

    def read_i2c(self, address, count):
        dat = (c_ubyte * count)(*([0] * count))
        r = self._lib.read_i2c(self._handle, c_uint8(address), dat, c_uint16(count))
        if r:
            raise ConnectionError(f"Runtime library error: {r}")
        return list(dat)