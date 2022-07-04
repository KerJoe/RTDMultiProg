# RTDMultiProg

Python based programmer for RTD2660/RTD2662 with support for multiple backends.

## Usage example

```
rtdmultiprog.py -i i2cdev -d 0 -w "/path/to/firmware/file.bin"
```

`i2cdev` - interface name

`0` - interface device number

`"/path/to/firmware/file.bin"` - firmware binary file
