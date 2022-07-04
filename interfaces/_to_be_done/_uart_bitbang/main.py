from argparse import ArgumentError
from tokenize import ContStr
from ..InterfaceBase import InterfaceBase
from ..SoftwareI2C import SoftwareI2C
import posix
import os
import re
import serial
import serial.tools.list_ports
import platform

class I2C(InterfaceBase):
    AvailableSystems = [ "" ]
    AvailableArchitectures = [ "" ]

    HIGH = True; LOW = True

    CTS = 0; DSR = 1; RI = 2; CD = 3    # Inputs
    DTR = 4; RTS = 5                    # Outputs

    SCL_INPUT = CTS; SCL_OUTPUT = RTS
    SDA_INPUT = DSR; SDA_OUTPUT = DTR

    # NOTE: Although the status pins of uart are by default active low (True -> Low level)
    # Setting false here will effectivly invert it (e.g to make line low, a True value will be passed)
    SCL_INPUT_INVERT = False; SCL_OUTPUT_INVERT = False
    SDA_INPUT_INVERT = False; SDA_OUTPUT_INVERT = False

    def setSCL(self, pinVal):
        if self.SCL_OUTPUT == self.DTR:
            self.ser.setDTR(pinVal ^ (not self.SCL_OUTPUT_INVERT))
        elif self.SCL_OUTPUT == self.RTS:
            self.ser.setRTS(pinVal ^ (not self.SCL_OUTPUT_INVERT))
        else:
            raise ArgumentError("Incorrect SCL output pin")

    def setSDA(self, pinVal):
        if self.SDA_OUTPUT == self.DTR:
            self.ser.setDTR(pinVal ^ (not self.SDA_OUTPUT_INVERT))
        elif self.SDA_OUTPUT == self.RTS:
            self.ser.setRTS(pinVal ^ (not self.SDA_OUTPUT_INVERT))
        else:
            raise ArgumentError("Incorrect SDA output pin")

    def getSCL(self):
        if self.SCL_INPUT == self.CTS:
            return self.ser.getCTS() ^ (not self.SCL_INPUT_INVERT)
        if self.SCL_INPUT == self.DSR:
            return self.ser.getDSR() ^ (not self.SCL_INPUT_INVERT)
        if self.SCL_INPUT == self.RI:
            return self.ser.getRI()  ^ (not self.SCL_INPUT_INVERT)
        if self.SCL_INPUT == self.CD:
            return self.ser.getCD()  ^ (not self.SCL_INPUT_INVERT)
        else:
            raise ArgumentError("Incorrect SCL input pin")

    def getSDA(self):
        if self.SDA_INPUT == self.CTS:
            return self.ser.getCTS() ^ (not self.SDA_INPUT_INVERT)
        if self.SDA_INPUT == self.DSR:
            return self.ser.getDSR() ^ (not self.SDA_INPUT_INVERT)
        if self.SDA_INPUT == self.RI:
            return self.ser.getRI()  ^ (not self.SDA_INPUT_INVERT)
        if self.SDA_INPUT == self.CD:
            return self.ser.getCD()  ^ (not self.SDA_INPUT_INVERT)
        else:
            raise ArgumentError("Incorrect SDA input pin")

    def list_i2c(self):
        devDict = {}
        devList = serial.tools.list_ports.comports()
        for itt, dev in enumerate(devList):
            if (platform.system() == "Windows"): # In Windows dev.name gives the # in COM#
                num = int(dev.name)
            else: # In *NIX it gives its full name (e.g. ttyUSB0), so use the itterator instead
                num = itt
            name = dev.description
            devDict.update({ num: name })
        return devDict


    def init_i2c(self, device):
        self.ser = serial.Serial()
        self.ser.port = serial.tools.list_ports.comports()[device].device
        self.ser.rtscts=False; self.ser.dsrdtr=False
        self.setSDA(self.HIGH); self.setSCL(self.HIGH)
        try:
            self.ser.close() # TODO: Remove ?
            self.ser.open()
        except serial.SerialException as e:
            raise ConnectionError(e) # Rethrow with built-in type
        self.i2c = SoftwareI2C(self.setSDA, self.getSDA, self.setSCL, self.getSCL)

    def deinit_i2c(self):
        self.setSDA(self.HIGH); self.setSCL(self.HIGH)
        self.ser.close()

    def write_i2c(self, address, data):
        self.i2c.sendMessage(address, data)

    def read_i2c(self, address, count):
        return self.i2c.readMessage(address, count)