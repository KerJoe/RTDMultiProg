# RTDMultiProg
Python based programmer for RTD2660/RTD2662 with support for multiple backends (interfaces).
```
usage: rtdmultiprog.py [-h] [-a] [-i INTERFACE] [-n] [-s SETTINGS] [-l]
                       [-d DEV] [-r READ_FILE] [-e] [-w WRITE_FILE]
                       [-z READ_SIZE] [-t]

Multi-interface RTD2660/RTD2662 firmware progammer.

options:
  -h, --help            show this help message and exit
  -a, --available-interfaces
                        list all available programming interfaces
  -i INTERFACE, --interface INTERFACE
                        select what programming interface to use
  -n, --interface-info  show interface description and information
  -s SETTINGS, --settings SETTINGS
                        set up interface settings
  -l, --list-devices    list available interface-devices and whether the
                        controller was detected on them
  -d DEV, --device DEV  select which interface-device to use
  -r READ_FILE, --read-output READ_FILE
                        read flash into this file
  -e, --erase           erase flash of the controller
  -w WRITE_FILE, --write-input WRITE_FILE
                        write flash from this binary file
  -z READ_SIZE, --read-size READ_SIZE
                        Set the number of bytes to read from flash
  -t, --trace           output full exception trace
```

## Interface list
- [X] i2cdev : Linux - a Linux module for accessing I2C master devices from userspace, via the /dev interface
- [X] ch341 : Windows - Cheap USB-I2C bridge
- [X] mcp2221 : All - USB-to-UART/I2C serial converter 
- [X] mcp2221_c : All - Same as above but using a compiled C library for extra speed
- [X] nvapi : Windows - This interface uses NVAPI library for I2C communication through NVIDIA GPU's \
**NOTE: Only works with preprogrammed controllers or with dummy EDID emulators**
- [ ] lpt : Windows - Bitbangs the parrallel port via "inpout" library
- [ ] lpt_old : Windows - Bitbangs the parrallel port via "i2cinterface" library from ROVA Tool https://www.mattmillman.com/info/lcd/rovatools
- [ ] uart_bitbang : All - Bitbangs the status pins of the COM port

## Adding new interfaces
1. Create new folder in `./interfaces/` directory with your interface name
2. Create file named `./interfaces/{INTERFACE_NAME}/main.py`
3. Add a class named `I2C` inheriting `InterfaceBase`
```
from interfaces.interface_base import InterfaceBase

class I2C(InterfaceBase):
  pass
```
4. Implement basic functions: `list_i2c`, `init_i2c`, `deinit_i2c`, `read_i2c`, `write_i2c` (read `./interface/interface_base.py` for more info)
5. Run `./rtdmultiprog_test.py {INTERFACE_NAME}` to test the new interface (you may need to manualy comment out the tests from `test_interface` and `test_device` functions)

## Usage examples

### List available interfaces
```
> ./rtdmultiprog.py -a
Available interfaces:
  * ch341
  * i2cdev
  * mcp2221
  * mcp2221_c
  * nvapi
```

### List available devices of an interface i2cdev
```
> ./rtdmultiprog.py -i i2cdev -l
 Device Number | Controller detected | Device Name 
       0       |         No          | NVIDIA i2c adapter 3 at 1:00.0
       1       |         Yes         | NVIDIA i2c adapter 5 at 1:00.0
       2       |         Yes         | NVIDIA i2c adapter 6 at 1:00.0
       3       |         No          | NVIDIA GPU I2C adapter
       4       |         No          | SMBus I801 adapter at f000
```

### Read firmware from first available device
```
> ./rtdmultiprog.py -i i2cdev "/path/to/firmware/file.bin"
No device passed, using first available...
Found controller on device 1!
FLASH ID: 0xffff
WARNING: '-z READ_SIZE' not set, default read amount of 512 KiB used
Will read 512.0 KiB
Progress: |#########################| 100.0%
File CRC: 0xb4
Chip CRC: 0xb4
```

### Write firmware to device number 2
```
> rtdmultiprog.py -i i2cdev -d 2 -w "/path/to/firmware/file.bin"
FLASH ID: 0xffff
Erasing... done
Will write 64.0 KiB
Progress: |#########################| 100.0%
File CRC: 0x4f
Chip CRC: 0x4f
```
