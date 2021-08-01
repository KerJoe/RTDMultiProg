from .._common_.interfaceBase import interfaceBase
from ctypes import *
import os
import sys

class I2C(interfaceBase):
    HelpText = "Test interface"

    def ListI2C(self):
        return {0: "Test0", 1: "Test1"}

    def InitI2C(self, device):
        pass

    def WriteI2C(self, address, data):
        pass

    def ReadI2C(self, address, count):
        return [ 0xFF for i in range(count) ]