#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include "libusb-1.0/libusb.h"


// Check and return error
#define CHECK if (r < 0) { printf("Error \"%i %s\" in function \"%s\" at line %i\n", r, libusb_error_name(r), __FUNCTION__, __LINE__); return r; }

#define MCP2221_VID 0x04D8
#define MCP2221_PID 0x00DD

// I2C bit rate
#define MCP2221_SPEED 400000

// Endpoints are of type INTERRUPT
#define MCP2221_HID_ENDPOINT_IN  0x83
#define MCP2221_HID_ENDPOINT_OUT 0x03
#define MCP2221_HID_INTERFACE 2

// In ms
#define ENDPOINT_TIMEOUT 1000


int write_hid(libusb_device_handle *handle, uint8_t* data)
{
    return libusb_interrupt_transfer(handle, MCP2221_HID_ENDPOINT_OUT, data, 64, NULL, ENDPOINT_TIMEOUT);
}

int read_hid(libusb_device_handle *handle, uint8_t* data)
{
    return libusb_interrupt_transfer(handle, MCP2221_HID_ENDPOINT_IN, data, 64, NULL, ENDPOINT_TIMEOUT);
}


int begin()
{
    int r;
    r = libusb_init(NULL); CHECK
    return 0;
}

int end()
{
    libusb_exit(NULL);
    return 0;
}


int init_i2c(libusb_device_handle **handle_p, uint8_t dev_adr)
{
    libusb_device **dev_list;
    int r, dev_n;

    r = libusb_get_device_list(NULL, &dev_list); CHECK
    if (r < 0) return r;
    dev_n = r;

    *handle_p = NULL;
    for (int i = 0; i < dev_n; i++)
        if (libusb_get_device_address(dev_list[i]) == dev_adr)
        {
            r = libusb_open(dev_list[i], handle_p);
            break;
        }
    // HACK: On Windows using libusbK: libusb_open fails, but libusb_open_device_with_vid_pid works
    // TODO: Rewrite list_i2c in C to get winUSB backend support?
    if (r == LIBUSB_ERROR_NOT_SUPPORTED)
    {
        *handle_p = libusb_open_device_with_vid_pid(NULL, 0x04D8, 0x00DD);
        r = 0;
    } CHECK // Checks status of libusb_open()
    libusb_device_handle *handle = *handle_p;

    libusb_free_device_list(dev_list, 1);

    if (!handle) { printf("No device found\n"); return LIBUSB_ERROR_NO_DEVICE; }

    r = libusb_kernel_driver_active(handle, MCP2221_HID_INTERFACE);
    if (r != LIBUSB_ERROR_NOT_SUPPORTED) // If error, then on windows, skip detaching
    {
        CHECK
        if (r) // Kernel driver is active
        {
            r = libusb_detach_kernel_driver(handle, MCP2221_HID_INTERFACE); CHECK
        }
    }
    r = libusb_claim_interface(handle, MCP2221_HID_INTERFACE); CHECK


    uint8_t buf[64] = {
        0x10, // Status/Set Parameters (command)
        0x00, // Don't care
        0x00, // Don't cancel current I2C/SMBus transfer (sub-command) //TODO: Why does cancelling, lock up I2C?
        0x20, // Set I2C/SMBus communication speed (sub-command)
        // The I2C/SMBus system clock divider that will be used to establish the communication speed
        (12000000 / MCP2221_SPEED) - 3
    };
    r = write_hid(handle, buf); CHECK
    r = read_hid(handle, buf); CHECK
    if (buf[22] == 0)
        return 1; // SCL stuck low
    if (buf[23] == 0)
        return 2; // SDA stuck low

    return 0;
}

int deinit_i2c(libusb_device_handle *handle)
{
    int r;
    r = libusb_release_interface(handle, MCP2221_HID_INTERFACE); CHECK
    libusb_close(handle);
    return 0;
}

int write_i2c(libusb_device_handle *handle, uint8_t address, uint8_t *data, uint16_t data_n)
{
    int r;
    uint8_t buf[64] = {
            0x90,                 // I2C Write Data (command)
            data_n & 0xFF,        // Requested I2C transfer length – 16-bit value – low byte
            (data_n >> 8) & 0xFF, // Requested I2C transfer length – 16-bit value – high byte
            address << 1,         // 8-bit value representing the I2C slave address to communicate with (even – address to write, odd – address to read)
    };
    memcpy(&buf[4], data, 60);

    r = write_hid(handle, buf); CHECK
    r = read_hid(handle, buf); CHECK
    if (buf[1])
        return 1; // I2C Engine is busy (command not completed)

    return 0;
}

int read_i2c(libusb_device_handle *handle, uint8_t address, uint8_t *data, uint16_t data_n)
{
    int r;
    uint8_t buf[64] = {
            0x91,                 // I2C Read Data (command)
            data_n & 0xFF,        // Requested I2C transfer length – 16-bit value – low byte
            (data_n >> 8) & 0xFF, // Requested I2C transfer length – 16-bit value – high byte
            (address << 1) | 1,   // 8-bit value representing the I2C slave address to communicate with (even – address to write, odd – address to read)
    };

    r = write_hid(handle, buf); CHECK
    r = read_hid(handle, buf); CHECK
    if (buf[1])
        return 1; // I2C Engine is busy (command not completed)

    buf[0] = 0x40;
    r = write_hid(handle, buf); CHECK
    r = read_hid(handle, buf); CHECK
    if (buf[1])
        return 2; // Error reading the I2C slave data from the I2C engine

    //*data_read = buf[3]; // Return amount of data that was actualy read
    memcpy(data, &buf[4], 60);

    return 0;
}


// Test function
void main()
{
    begin();
    libusb_device_handle* h;
    init_i2c(&h, 21);
    uint8_t buf[64];
    buf[0] = 0x6f;
    buf[1] = 0x80;
    write_i2c(h, 0x4a, &buf[0], 2);
    buf[0] = 0x6f;
    write_i2c(h, 0x4a, &buf[0], 1);
    read_i2c(h, 0x4a, &buf[0], 1);
    printf("%i\n", (int)buf[0]);
    deinit_i2c(h);
    end();
}
