import posix, os, re, time
from argparse                  import ArgumentParser
from fcntl                     import ioctl
from interfaces.interface_base import InterfaceBase

# NOTE: Some implementations may requre smaller data chunks
class I2C(InterfaceBase):
    HELP_TEXT = ("i2c-dev is a Linux module for accessing I2C master devices "
                 "from userspace, via the /dev interface.\n"
                 "OPTIONS: \"-z n\": Set maximum transaction size")
    AVAILABLE_SYSTEMS = [ "Linux" ]
    MAXIMUM_READ_AMOUNT = 16
    MAXIMUM_WRITE_AMOUNT = 16

    _fi2c = None

    _I2C_SLAVE = 0x0703 # Set I2C slave address ioctl call


    def list_i2c(self):
        try:
            dev_list = os.listdir("/sys/bus/i2c/devices")
        except FileNotFoundError:
            raise FileNotFoundError("I2C device directory not found")
        dev_dict = {}
        for dev in dev_list:
            match = re.match("i2c-\d+", dev)
            if match:
                num = int(re.sub("i2c-", "", dev))
                with open("/sys/bus/i2c/devices/"+match.string+"/name", 'r') as fname:
                    name = fname.readline()
                dev_dict.update({num: name})
        return dev_dict

    def init_i2c(self, device, settings):
        self._fi2c = posix.open("/dev/i2c-"+str(device), posix.O_RDWR)
        # Set exchange size
        if settings is not None:
            parser = ArgumentParser(add_help=False)
            parser.add_argument('-z', type=int, dest="exch_size")
            args = parser.parse_args(settings.split())
            if args.exch_size is not None:
                self.MAXIMUM_READ_AMOUNT  = args.exch_size
                self.MAXIMUM_WRITE_AMOUNT = args.exch_size

    def deinit_i2c(self):
        posix.close(self._fi2c)

    def detect_i2c(self, address):
        try:
            ioctl(self._fi2c, self._I2C_SLAVE, address)
            posix.write(self._fi2c, bytes(0))
            return True
        except Exception:
            return False

    def write_i2c(self, address, data):
        ioctl(self._fi2c, self._I2C_SLAVE, address)
        try:
            posix.write(self._fi2c, bytes(data))
        except IOError:
            raise ConnectionError("No ACK from device")

    def read_i2c(self, address, count):
        ioctl(self._fi2c, self._I2C_SLAVE, address)
        return list(posix.read(self._fi2c, count))
