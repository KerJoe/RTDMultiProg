from .._common_.interfaceBase import interfaceBase
import posix
import os
import re
import serial
import serial.tools.list_ports

class I2C(interfaceBase):
    AvailableSystems = [ "" ] # Unsure if Mac OS Darwin is supported
    AvailableArchitectures = [ "" ]

    def list_i2c(self):
        devDict = {}
        devList = serial.tools.list_ports.comports()
        for dev in devList:
            num  = int(dev.name)
            name = dev.description
            devDict.update({ num: name })
        return devDict


    def init_i2c(self, device):
        self.fi2c = posix.open("/dev/i2c-"+str(device), posix.O_RDWR)

    def deinit_i2c(self):
        posix.close(self.fi2c)

    def write_i2c(self, address, data):
        if type(data) == int:
            data = [data]
        data = bytes([(i & 0xFF) for i in data]) # Avoid bytes must be in range(0, 256) error
        ioctl(self.fi2c, self.I2C_SLAVE, address)
        try:
            posix.write(self.fi2c, data)
        except IOError:
            raise ConnectionError("No ACK from device")

    def read_i2c(self, address, count):
        return list(posix.read(self.fi2c, count))