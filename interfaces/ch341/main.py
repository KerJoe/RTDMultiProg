from interfaces.interface_base import InterfaceBase
from argparse import ArgumentParser
from ctypes   import *
import os

class I2C(InterfaceBase):
    AVAILABLE_SYSTEMS = [ "Windows" ]
    AVAILABLE_ARCHITECTURES = [ "i386" ]
    HELP_TEXT = ("OPTIONS: \"-s n\": Set transaction speed\n"
                 "0 = low speed / 20KHz, 1 = standard / 100KHz (default), 2 = fast / 400KHz, 3 = high speed / 750KHz")

    _ch341 = None
    _index = -1

    def __init__(self):
        self._ch341 = cdll.LoadLibrary(os.path.dirname(__file__) + "\\ch341.dll")

    def list_i2c(self):
        devList = {}
        for i in range(256):
            if (self._ch341.CH341OpenDevice(c_ulong(i)) >= 0):
                devList[i] = f"CH341 ID {i}"
        return devList

    def init_i2c(self, device, settings):
        if (self._ch341.CH341OpenDevice(c_ulong(device)) < 0):
            raise ConnectionError
        self._index = device
        # Set exchange speed
        if settings is not None:
            parser = ArgumentParser(add_help=False)
            parser.add_argument('-s', type=int, dest="exch_speed")
            args = parser.parse_args(settings.split())
            if args.exch_speed is not None and args.exch_speed in [0,1,2,3]:
                self._ch341.CH341SetStream(c_ulong(self._index), c_ulong(args.exch_speed))


    def detect_i2c(self, address):
        dat = (c_ubyte*1)(*[0])
        if (not self._ch341.CH341StreamI2C(c_ulong(self._index), 1, pointer(c_ulong(address << 1 | 1)), c_ulong(1), dat)):
            return False
        if dat[0] == 255:
            return False
        return True

    def deinit_i2c(self):
        retval = self._ch341.CH341CloseDevice(c_ulong(self._index))
        self._index = -1
        if (not retval):
            raise ConnectionError

    def write_i2c(self, address, data):
        data.insert(0, address << 1)
        dat  = (c_ubyte * len(data))(*data)
        if (not self._ch341.CH341StreamI2C(c_ulong(self._index), c_ulong(len(data)), dat, 0, 0)):
            raise ConnectionError

    def read_i2c(self, address, count):
        dat  = (c_ubyte * count)(*([0] * count))
        if (not self._ch341.CH341StreamI2C(c_ulong(self._index), 1, pointer(c_ulong(address << 1 | 1)), c_ulong(count), dat)):
            raise ConnectionError
        data = [i for i in dat]
        return data