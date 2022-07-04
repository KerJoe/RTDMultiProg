from ..InterfaceBase import InterfaceBase
from ctypes import *
import os

class I2C(InterfaceBase):
    ch341 = None
    index = -1

    AvailableSystems = [ "Windows" ]
    AvailableArchitectures = [ "32bit" ]

    def __init__(self):
        self.ch341 = cdll.LoadLibrary(os.path.dirname(__file__) + "\\ch341.dll")

    def list_i2c(self):
        devList = {}
        for i in range(256):
            if (self.ch341.CH341OpenDevice(c_ulong(i)) >= 0):
                devList[i] = f"CH341 ID {i}"
        return devList

    def init_i2c(self, device):
        if (self.ch341.CH341OpenDevice(c_ulong(device)) < 0):
            raise ConnectionError
        self.index = device

    def deinit_i2c(self):
        retval = self.ch341.CH341CloseDevice(c_ulong(self.index))
        self.index = -1
        if (not retval):
            raise ConnectionError

    def write_i2c(self, address, data):
        data.insert(0, address << 1)
        dat  = (c_ubyte * len(data))(*data)
        if (not self.ch341.CH341StreamI2C(c_ulong(self.index), c_ulong(len(data)), dat, 0, 0)):
            raise ConnectionError

    def read_i2c(self, address, count):
        dat  = (c_ubyte * count)(*([0] * count))
        if (not self.ch341.CH341StreamI2C(c_ulong(self.index), 1, pointer(c_ulong(address << 1 | 1)), c_ulong(count), dat)):
            raise ConnectionError
        data = [i for i in dat]
        return data