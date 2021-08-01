from .._common_.interfaceBase import interfaceBase
import posix
import os
import re
from fcntl import ioctl

class I2C(interfaceBase):
    AvailableSystems = [ "Linux", "Darwin" ] # Unsure if Mac OS Darwin is supported
    AvailableArchitectures = [ "" ]

    fi2c = None

    I2C_SLAVE = 0x0703

    def ListI2C(self):
        try:
            devList = os.listdir("/sys/bus/i2c/devices")
        except FileNotFoundError:
            raise FileNotFoundError("I2C devices directory not found")
        devDict = {}
        for dev in devList:
            match = re.match("i2c-.*", dev)
            if match:
                num  = int(re.sub("i2c-", "", dev))
                fn = open("/sys/bus/i2c/devices/"+match.string+"/name", 'r'); name = fn.readline(); fn.close()
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