class interfaceBase:
    AvailableSystems = [ "" ]       # Values: [ "Windows", "Darwin", "Linux", ... ]
    AvailableArchitectures = [ "" ] # Values: [ "AMD64", "i386", ... ]
    HelpText = "" # Text discribing the interface

    def ListI2C(self):
        """
        List all devices belonging to this interface

        Returns: {deviceNum: deviceName, ...}
            deviceNum - number to be passed to InitI2C
            deviceName - human readable device name associated with the number
        """
        return {}

    def InitI2C(self, device):
        """
        Initialize I2C interface

        Arguments: device
            device - Which device implementing the interface to initialize
        """
        pass

    def DeinitI2C(self):
        """
        Deinitialize I2C interface
        """
        pass

    def WriteI2C(self, address, data):
        """
        Write buffer to I2C interface

        Arguments: address, data
            address - Address on I2C bus
            data - data to be written
        """
        pass

    def ReadI2C(self, address, count):
        """
        Read buffer from I2C interface

        Arguments: address
            address - Address on I2C bus
            count - Number of bytes to read

        Returns: [data]
            data - data read from I2C
        """
        return [0] * count