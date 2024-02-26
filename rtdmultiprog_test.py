#!/usr/bin/env python3

import sys, os, platform, traceback, random
import rtdmultiprog
from misc.funcs import *


RIGHT_ADDRESS = 0x4A # RTD2660 address
WRONG_ADDRESS = 0x7F # Unused address used to check if detectI2C always returns True

FLASH_TEST_SIZE = 1 * 1024

class Color:
    black   = "\u001b[30m"
    red     = "\u001b[31m"
    green   = "\u001b[32m"
    yellow  = "\u001b[33m"
    blue    = "\u001b[34m"
    magenta = "\u001b[35m"
    cyan    = "\u001b[36m"
    white   = "\u001b[37m"
if platform.system() == "Windows":
    os.system('color') # Enable ANSI color
print(Color.white, end='')


def input_yes_no(message):
    while True:
        choice = input(message)
        if choice.capitalize() == 'Y':
            return True
        elif choice.capitalize() == 'N' or choice == '':
            return False

def input_valid_value(message, valid_value_list):
    while True:
        choice = input(message)
        if choice in valid_value_list:
            return choice

def hex_dump_compare(original, result):
    print("         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F", end='')
    for val_n, val in enumerate(result):
        if val_n % 16 == 0:
            print(f"\n{val_n//16*16:06x}: ", end='')
        if original[val_n] != result[val_n]:
            print(f"{Color.red}{val:2x}{Color.white} ", end='')
        else:
            print(f"{val:2x} ", end='')
    print()


def test_interface(iface, dev_sel=None):
    try:

        print("Load test... ", end='')
        rtdmultiprog.load_interface(iface)
        print(f"{Color.green}success{Color.white}")

        print("List test... ", end='')
        dev_list = rtdmultiprog.iface.list_i2c()
        print(f"{Color.green}success{Color.white}")

    except Exception:
        print(f"{Color.red}fail -> {Color.white}{traceback.format_exc()}")
        return False

    if dev_sel is None:
        while True:
            for dev in dev_list:
                print(f"{dev:3}: {dev_list[dev].strip()}")
            dev_sel = int(input_valid_value("Select device: ", [str(i) for i in dev_list.keys()]))
            if not test_device(dev_sel):
                if not input_yes_no("Try another device [y/N]? "):
                    break
            else:
                break
    else:
        while True:
            if not test_device(dev_sel):
                if not input_yes_no("Try again [y/N]? "):
                    break
            else:
                break

    return True

def test_device(dev):
    try:

        print("Init test... ", end='')
        rtdmultiprog.iface.init_i2c(dev, "")
        print(f"{Color.green}success{Color.white}")

        print("Right address access test... ", end='')
        if not rtdmultiprog.iface.detect_i2c(RIGHT_ADDRESS):
            raise Exception("Device not found")
        print(f"{Color.green}success{Color.white}")

        # print("Wrong address access test... ", end='')
        # if rtdmultiprog.iface.detect_i2c(WRONG_ADDRESS):
            # raise Exception("Detected non-existent device")
        # print(f"{Color.green}success{Color.white}")
        
        print("Write I2C test... ", end='')
        rtdmultiprog.iface.write_i2c(RIGHT_ADDRESS, [0x6F, 0x80])
        print(f"{Color.green}success{Color.white}")
        input()
        print("Read I2C test... ", end='')
        rtdmultiprog.iface.write_i2c(RIGHT_ADDRESS, [0x6F])
        recv = rtdmultiprog.iface.read_i2c(RIGHT_ADDRESS, 1)[0]
        if not rtdmultiprog.iface.read_i2c(RIGHT_ADDRESS, 1)[0] & 0x80:
            raise Exception(f"Write failed to set bit or Read failed to get bit. Sent: 0x80, Received: {recv:#04x}")
        print(f"{Color.green}success{Color.white}")

        print("Deinit test... ", end='')
        rtdmultiprog.iface.deinit_i2c()
        print(f"{Color.green}success{Color.white}")

        print("Start interface test... ", end='')
        rtdmultiprog.start_interface(dev)
        print(f"{Color.green}success{Color.white}")

        print("Setup flash test... ", end='')
        rtdmultiprog.setup_flash()
        print(f"{Color.green}success{Color.white}")

        print("Erase flash test... ", end='')
        rtdmultiprog.erase_flash()
        print(f"{Color.green}success{Color.white}")

        print("Write flash test... ", end='')
        #write_data = [random.randint(0,255) for i in range(FLASH_TEST_SIZE)]
        write_data = [0 for i in range(FLASH_TEST_SIZE)]
        start = time.time()
        recv = rtdmultiprog.program_flash(write_data, lambda s, e, c: progress_bar(c/(e-s)))
        stop = time.time()
        print(f"Bitrate: {FLASH_TEST_SIZE / (stop - start):.0f} Byte/s")
        if not recv:
            recv, _ = rtdmultiprog.read_flash(FLASH_TEST_SIZE)
            hex_dump_compare(write_data, recv)
            raise Exception(f"CRC mismatch")
        print(f"{Color.green}success{Color.white}")

        print("Read flash test... ", end='')
        start = time.time()
        read_data, recv = rtdmultiprog.read_flash(FLASH_TEST_SIZE, lambda s, e, c: progress_bar(c/(e-s)))
        stop = time.time()
        print(f"Bitrate: {FLASH_TEST_SIZE / (stop - start):.0f} Byte/s")
        if not recv:
            hex_dump_compare(write_data, read_data)
            raise Exception(f"CRC mismatch")
        print(f"{Color.green}success{Color.white}")

        print("Reboot test... ", end='')
        rtdmultiprog.reboot_controller()
        print(f"{Color.green}success{Color.white}")

    except Exception:
        print(f"{Color.red}fail{Color.white}\n{Color.yellow}{traceback.format_exc()}{Color.white}")
        return False
    return True


if len(sys.argv) >= 2:
    test_interface(sys.argv[1], None if len(sys.argv) < 3 else int(sys.argv[2]))
else:
    ifaces = rtdmultiprog.get_interface_list()
    for iface in ifaces:
        if not input_yes_no(f"Test {iface} interface [y/N]? "):
            continue
        test_interface(iface)
