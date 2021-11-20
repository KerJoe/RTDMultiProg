from .._common_.interfaceBase import interfaceBase
import posix
import os
import re
import serial
import serial.tools.list_ports

class I2C(interfaceBase):
    AvailableSystems = [ "" ] # Unsure if Mac OS Darwin is supported
    AvailableArchitectures = [ "" ]

    def ListI2C(self):
        devDict = {}
        devList = serial.tools.list_ports.comports()
        for dev in devList:
            num  = int(dev.name)
            name = dev.description
            devDict.update({ num: name })
        return devDict


    def InitI2C(self, device):
        self.fi2c = posix.open("/dev/i2c-"+str(device), posix.O_RDWR)

    def DeinitI2C(self):
        posix.close(self.fi2c)

    def WriteI2C(self, address, data):
        if type(data) == int:
            data = [data]
        data = bytes([(i & 0xFF) for i in data]) # Avoid bytes must be in range(0, 256) error
        ioctl(self.fi2c, self.I2C_SLAVE, address)
        try:
            posix.write(self.fi2c, data)
        except IOError:
            raise ConnectionError("No ACK from device")

    def ReadI2C(self, address, count):
        return list(posix.read(self.fi2c, count))