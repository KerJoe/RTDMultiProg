import usb, platform, time
from interfaces.interface_base import InterfaceBase
from misc.funcs import *

class I2C(InterfaceBase):
    HELP_TEXT = ("The MCP2221 is a USB-to-UART/I2C serial converter "
                 "which enables USB connectivity in applications that "
                 "have a UART and I2C interfaces.\n"
                 "NOTE: This implementation bypasses the HID interface "
                 "and accesses device directly using libusb.")
    MAXIMUM_READ_AMOUNT  = 60
    MAXIMUM_WRITE_AMOUNT = 60


    _MCP2221_SPEED = 400000
    _MCP2221_DELAY = 0.000 # Delay before reading from HID endpoint, sometimes prevents chip lockup


    _mcp2221 = None
    _epo = None
    _epi = None

    _MCP2221_VID = 0x04D8
    _MCP2221_PID = 0x00DD

    _MCP2221_HID_INTERFACE = 2
    _MCP2221_BUFFER_SIZE   = 64

    _MCP2221_ENDPOINT_IN   = 0
    _MCP2221_ENDPOINT_OUT  = 1

    # From http://ww1.microchip.com/downloads/en/DeviceDoc/mcp2221_0_1.tar.gz
    state_machine = {
        0x00: "RESP_I2C_IDLE",
        0x25: "RESP_ADDR_NACK",
        0x7F: "RESP_READ_ERR",
        0x55: "RESP_READ_COMPL",
        0x12: "RESP_I2C_START_TOUT",
        0x17: "RESP_I2C_RSTART_TOUT",
        0x23: "RESP_I2C_WRADDRL_TOUT",
        0x21: "RESP_I2C_WRADDRL_WSEND",
        0x25: "RESP_I2C_WRADDRL_NACK",
        0x44: "RESP_I2C_WRDATA_TOUT",
        0x52: "RESP_I2C_RDDATA_TOUT",
        0x62: "RESP_I2C_STOP_TOUT"
    }

    def _wait_till_ready(self):
        try:
            poll(lambda: self._exch_hid([0x10])[8] in [0x00, 0x55], step=0)
        except TimeoutError as e:
            raise TimeoutError(f"Stuck in state {self._exch_hid([0x10])[8]}: {self.state_machine.get(self._exch_hid([0x10])[8])}") from e


    def _cancel_transfer(self):
        self._exch_hid([
            0x10, # Status/Set Parameters (command)
            0x00, # Don't care
            0x10, # Cancel current I2C/SMBus transfer (sub-command)
            0x00, # Don't set I2C/SMBus communication speed (sub-command)
        ])
        # Wait till the transfer is canceled
        poll(lambda: self._exch_hid([
            0x10, # Status/Set Parameters (command)
            0x00, # Don't care
            0x00, # Don't cancel current I2C/SMBus transfer (sub-command)
            0x00, # Don't set I2C/SMBus communication speed (sub-command)
        ])[2] != 0x10)

    def _reset_chip(self):
        self._exch_hid([
            0x70,
            0xAB,
            0xCD,
            0xEF
        ])

    def _exch_hid(self, data):
        self._epo.write(data)
        time.sleep(self._MCP2221_DELAY)
        return self._epi.read(self._MCP2221_BUFFER_SIZE)


    def list_i2c(self):
        dev_list_ = usb.core.find(idVendor=self._MCP2221_VID, idProduct=self._MCP2221_PID, find_all=True)
        dev_list  = {}
        for dev_n, dev in enumerate(sorted(dev_list_)):
            dev_list[dev_n] = f"MCP2221 on bus {dev.bus} device {dev.address}"
        return dev_list

    def init_i2c(self, device, settings):
        self._mcp2221 = sorted(usb.core.find(idVendor=self._MCP2221_VID, idProduct=self._MCP2221_PID, find_all=True))[device]
        if platform.system() != "Windows": # is_kernel_driver_active() not implemented for Windows
            if self._mcp2221.is_kernel_driver_active(self._MCP2221_HID_INTERFACE):
                try:
                    self._mcp2221.detach_kernel_driver(self._MCP2221_HID_INTERFACE)
                except Exception:
                    raise ConnectionError("Failed to detach HID kernel driver from device.")
        usb.util.claim_interface(self._mcp2221, self._MCP2221_HID_INTERFACE)

        # On windows, interface number may not be equal to it's index in the array
        # if only one interface was assigned a libusb driver, so we search for it.
        hid_iface = None
        for usb_iface in self._mcp2221[0]:
            if usb_iface.bInterfaceNumber == self._MCP2221_HID_INTERFACE:
                hid_iface = usb_iface
                break
        self._epo = hid_iface[self._MCP2221_ENDPOINT_OUT]
        self._epi = hid_iface[self._MCP2221_ENDPOINT_IN]

        self._cancel_transfer()
        buffer = self._exch_hid([
            0x10, # Status/Set Parameters (command)
            0x00, # Don't care
            0x00, # Don't cancel current I2C/SMBus transfer (sub-command)
            0x20, # Set I2C/SMBus communication speed (sub-command)
            # The I2C/SMBus system clock divider that will be used to establish the communication speed
            (12000000 // self._MCP2221_SPEED) - 3
        ])
        if (buffer[22] == 0):
            raise ConnectionError("SCL stuck low.")
        if (buffer[23] == 0):
            raise ConnectionError("SDA stuck low.")

    def deinit_i2c(self):
        if self._mcp2221 is not None:
            # try:
            #     self.mcp2221.attach_kernel_driver(self.MCP2221_HID_INTERFACE)
            # except Exception:
            #     raise ConnectionError("Failed to reattach HID kernel driver to device.")
            usb.util.release_interface(self._mcp2221, self._MCP2221_HID_INTERFACE)
            self._mcp2221 = None

    def write_i2c(self, address, data):
        buffer = [
            0x90,                    # I2C Write Data (command)
            len(data) & 0xFF,        # Requested I2C transfer length – 16-bit value – low byte
            (len(data) >> 8) & 0xFF, # Requested I2C transfer length – 16-bit value – high byte
            address << 1,            # 8-bit value representing the I2C slave address to communicate with (even – address to write, odd – address to read)
        ]
        buffer += data
        self._wait_till_ready()
        buffer = self._exch_hid(buffer)
        if buffer[1]:
            raise ConnectionError("I2C Engine is busy (command not completed)")

    def read_i2c(self, address, count):
        self._wait_till_ready()
        buffer = self._exch_hid([
            0x91,                # I2C Read Data (command)
            count & 0xFF,        # Requested I2C transfer length – 16-bit value – low byte
            (count >> 8) & 0xFF, # Requested I2C transfer length – 16-bit value – high byte
            (address << 1) | 1   # 8-bit value representing the I2C slave address to communicate with (even – address to write, odd – address to read)
        ])
        if buffer[1]:
            raise ConnectionError("I2C Engine is busy (command not completed)")
        self._wait_till_ready()
        buffer = self._exch_hid([
            0x40, # I2C Read Data – Get I2C Data (command)
        ])
        if buffer[1]:
            raise ConnectionError("Error reading the I2C slave data from the I2C engine")
        read_byte_count = buffer[3]
        return list(buffer[4:4+read_byte_count])

    def __del__(self):
        if self._mcp2221 is not None:
            self.deinit_i2c()
