class InterfaceBase:
    AVAILABLE_SYSTEMS = [ "" ]       # Values: [ "Windows", "Darwin", "Linux", ... ] # If [ "" ] then all systems
    AVAILABLE_ARCHITECTURES = [ "" ] # Values: [ "AMD64", "i386", ... ]              # If [ "" ] then all architectures
    HELP_TEXT = "" # Text discribing the interface

    MAXIMUM_READ_AMOUNT  = 0 # Maximum amount of bytes that can be read from the I2C bus in one transaction (Minimum is 2).  # If 0 then Unlimited
    MAXIMUM_WRITE_AMOUNT = 0 # Maximum amount of bytes that can be written to the I2C bus in one transaction (Minimum is 2). # If 0 then Unlimited

    def list_i2c(self):
        """
        List all devices belonging to this interface

        Returns: {device_id: "device_name", ...}
            device_id - number to be passed to init_i2c;
            device_name - human readable device name associated with the number;
        """
        return {}

    def init_i2c(self, device, settings):
        """
        Initialize the I2C interface

        Arguments: device, "settings"
            device - which device implementing this interface should be initialized;
            settings - string containing parameters for the interface;
        """
        pass

    def deinit_i2c(self):
        """
        Deinitialize the I2C interface
        """
        pass

    def detect_i2c(self, address):
        """
        Detect availability of a device on the I2C bus

        Arguments: device
            address - 7-bit address on the I2C bus;

        Returns: detected
            detected - boolean whether the device was found on the I2C bus;
        """
        try:
            self.read_i2c(address, 1)
            return True
        except Exception:
            return False

    def write_i2c(self, address, data):
        """
        Write buffer to the I2C interface

        Arguments: address, [data]
            address - 7-bit address on the I2C bus;
            data - data to be written to the device;
        """
        pass

    def read_i2c(self, address, count):
        """
        Read buffer from the I2C interface

        Arguments: address, count
            address - 7-bit address on the I2C bus;
            count - number of bytes to read;

        Returns: [data]
            data - data read from the device;
        """
        return [0] * count