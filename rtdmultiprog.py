#!/usr/bin/env python3

import os, platform, sys
from misc.flashparams import *
from misc.funcs       import *
from importlib        import import_module
from genericpath      import exists
from argparse         import ArgumentParser

script_folder = os.path.dirname(os.path.abspath(__file__))

# If `None`, parse from command line;
# else if strings, parse from this variable
parameters = None

# Global definition of the current interface
iface = None

# Alias for os.sep
SEP = os.sep

# Controller's address on I2C bus
RTD_ISP_ADR         = 0x4A
RTD_ISP_AUTOINC_ADR = RTD_ISP_ADR | 1

# Custom instruction types
CI_NOP   = 0
CI_WRITE = 1
CI_READ  = 2
CI_WRITE_AFTER_WREN = 3
CI_WRITE_AFTER_EWSR = 4
CI_ERASE = 5


def calculate_crc(data):
    """ Calculate CRC-8-CCITT (Poly: x^8 + x^2 + x + 1) """
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07 if crc & 0x80 else crc << 1) & 0xFF
    return crc

def is_empty_page(data):
    """ Test if page only contains 0xFF """
    for value in data:
        if value != 0xFF:
            return False
    return True


def write_reg(address, data, is_autoinc=False):
    # Single int to list of one element
    if isinstance(data, int):
        data = [data]
    # Cap integers to byte range
    data = [(i & 0xFF) for i in data]
    # Divide list into chunks with address appended
    if iface.MAXIMUM_WRITE_AMOUNT == 0:
        data = [[address] + data]
    else:
        data = [[address] + i for i in div_to_chunks(data, iface.MAXIMUM_WRITE_AMOUNT-1)]
    for chunk in data:
        iface.write_i2c(RTD_ISP_AUTOINC_ADR if is_autoinc else RTD_ISP_ADR, chunk)

def read_reg(address, count=1, is_autoinc=False):
    if iface.MAXIMUM_READ_AMOUNT == 0:
        bytes_per_trans = count
    else:
        bytes_per_trans = iface.MAXIMUM_READ_AMOUNT
    data = []
    for byte_n in range(0, count, bytes_per_trans):
        iface.write_i2c(RTD_ISP_ADR, [address])
        data += iface.read_i2c(RTD_ISP_AUTOINC_ADR if is_autoinc else RTD_ISP_ADR,
                               min(count - byte_n, bytes_per_trans))
    return data


def enter_isp():
    """ Enable In-System Programming mode, Disable internal MCU """
    write_reg(0x6F, 0x80)
    if not (read_reg(0x6F)[0] & 0x80):
        raise ConnectionError("Failed to enter into ISP mode")

def reboot_controller():
    """ Disable In-System Programming mode, Restart internal MCU """
    try:
        write_reg(0xEE, 0x02)
        #write_reg(0x6F, 0x00)
    except ConnectionError:
        pass

def isp_custom_instruction(cmd_type, cmd_code, read_n, write_n, write_value):
    if   write_n == 1:
        write_reg(0x64, write_value)
    elif write_n == 2:
        write_reg(0x64, write_value >> 8)
        write_reg(0x65, write_value)
    elif write_n == 3:
        write_reg(0x64, write_value >> 16)
        write_reg(0x65, write_value >> 8)
        write_reg(0x66, write_value)

    # Execute custom instruction and wait until done
    write_reg(0x61, cmd_code)
    write_reg(0x60, (cmd_type<<5) | (write_n<<3) | (read_n<<1) | 1)
    timeout = 20 if cmd_code == ERAS else 2
    poll(lambda: not read_reg(0x60)[0] & 0x01, "Custom Instruction Timeout", timeout)

    if   read_n == 1:
        return  read_reg(0x67)[0]
    elif read_n == 2:
        return (read_reg(0x67)[0] << 8)  |  read_reg(0x68)[0]
    elif read_n == 3:
        return (read_reg(0x67)[0] << 16) | (read_reg(0x68)[0] << 8) | read_reg (0x69)[0]
    else:
        return None

def isp_get_crc(start_address, end_address):
    write_reg(0x64, start_address >> 16)
    write_reg(0x65, start_address >> 8)
    write_reg(0x66, start_address)

    write_reg(0x72, end_address >> 16)
    write_reg(0x73, end_address >> 8)
    write_reg(0x74, end_address)

    # Start CRC calculation and wait until done
    write_reg(0x6F, 0x84)
    poll(lambda: read_reg(0x6F)[0] & 0x02, "CRC Read Timeout")

    return read_reg(0x75)[0]

def get_flash_id():
    return isp_custom_instruction(CI_READ, RDID, 2, 0, 0x00)

def erase_flash():
    print("Erasing... ", end='')
    isp_custom_instruction(CI_WRITE_AFTER_WREN, WRSR, 0, 1, 0x00) # Unprotect the flash
    isp_custom_instruction(CI_ERASE, ERAS, 0, 0, 0x00)            # Erase the flash
    isp_custom_instruction(CI_WRITE_AFTER_WREN, WRSR, 0, 1, 0x1C) # Protect the flash
    print("done")

def program_flash(data, progress_callback=lambda s, e, c: None):
    print(f"Will write {len(data) / 1024:.1f} KiB")

    isp_custom_instruction(CI_WRITE_AFTER_WREN, WRSR, 0, 1, 0x00) # Unprotect the flash
    pages = list(div_to_chunks(data, PAGE_SIZE))
    for page_n, page in enumerate(pages):
        progress_callback(0, len(pages), page_n)

        if not is_empty_page(page): # If page is filled with 0xFF, then don't write to it
            poll(lambda: not read_reg (0x6F)[0] & 0x40, "Programming done timeout")
            # Set write size
            write_reg(0x71, len(page) - 1)
            # Set the programming address
            write_reg(0x64, page_n*PAGE_SIZE >> 16)
            write_reg(0x65, page_n*PAGE_SIZE >> 8)
            write_reg(0x66, page_n*PAGE_SIZE)
            # Write the content to on chip buffer
            write_reg(0x70, page)
            # Begin flash programming
            write_reg(0x6F, 0xA0)

    progress_callback(0, len(data), len(data)) # Signal 100% to progress function

    poll(lambda: not read_reg (0x6F)[0] & 0x40, "Programming done timeout")
    isp_custom_instruction(CI_WRITE_AFTER_WREN, WRSR, 0, 1, 0x1C)  # Protect the flash

    data_crc = calculate_crc(data)
    chip_crc = isp_get_crc(0, len(data) - 1)
    print(f"File CRC: {data_crc:#04x}")
    print(f"Chip CRC: {chip_crc:#04x}")
    return data_crc == chip_crc

def read_flash(chip_size, progress_callback=lambda s, e, c: None):
    print(f"Will read {chip_size / 1024:.1f} KiB")
    data = []

    isp_custom_instruction(CI_READ, READ, 3, 3, 0)
    poll(lambda: not read_reg(0x60)[0] & 0x01, "Read Instruction Timeout")
    for address in range(0, chip_size, PAGE_SIZE):
        progress_callback(0, chip_size, address)
        data += read_reg(0x70, min(chip_size - address, PAGE_SIZE)) # If amount to read is more than PAGE_SIZE byte then read PAGE_SIZE, else read remaining amount

    progress_callback(0, chip_size, chip_size) # Signal 100% to progress function

    data_crc = calculate_crc(data)
    chip_crc = isp_get_crc(0, chip_size - 1)
    print(f"File CRC: {data_crc:#04x}")
    print(f"Chip CRC: {chip_crc:#04x}")
    return ( data, data_crc == chip_crc )


def get_interface_list():
    """ Return string list of all available interfaces """
    iface_list_ = os.listdir(script_folder+SEP+"interfaces")
    iface_list  = []
    for interface in iface_list_:
        # Add folders with main.py file
        # and folders not starting with an underscore
        if exists(script_folder+SEP+"interfaces"+SEP+interface+SEP+"main.py") \
           and not interface.startswith('_'):
            iface_list.append(interface)
    return iface_list

def load_interface(interface):
    try:
        iface_module = import_module(f"interfaces.{interface}.main").I2C
    except ModuleNotFoundError as e: # Rethrow exception with our message
        raise ModuleNotFoundError(f"Interface \"{interface}\" not found or is incorrect.") from e

    # Test if all systems are supported or we are running on a supported system
    if not (iface_module.AVAILABLE_SYSTEMS == [""] or platform.system() in iface_module.AVAILABLE_SYSTEMS):
        raise SystemError(f"Interface supports {', '.join(iface_module.AVAILABLE_SYSTEMS)}; not {platform.system()}")

    # # Test if all architectures are supported orwe are running on a supported architecture
    # mach_to_bits = { "x86_64": "64bit", "x86": "32bit" } # Machine name to executable bitness
    # win_to_gnu   = { "AMD64": "x86_64", "x86": "i386" }  # Windows machine to GNU triplet conversion
    # if not (iface_module.AVAILABLE_ARCHITECTURES == [""] or \
    #         ((platform.machine() in iface_module.AVAILABLE_ARCHITECTURES or \
    #         win_to_gnu.get(platform.machine()) in iface_module.AVAILABLE_ARCHITECTURES) and \
    #         mach_to_bits.get(iface_module.AVAILABLE_ARCHITECTURES) == platform.architecture[0])):
    #     raise SystemError(f"Interface supports {', '.join(iface_module.AVAILABLE_ARCHITECTURES)}; not {platform.machine()}\n" +
    #                        "If the interface doesn't support 32 or 64 bit architecture, try running it with 64 or 32 bit python interpreter.")

    global iface
    iface = iface_module()

def get_device_list(settings=None):
    dev_dict_ = iface.list_i2c()
    dev_dict  = {}
    for dev in dev_dict_:
        is_present = False
        try:
            iface.init_i2c(dev, settings)
            is_present = iface.detect_i2c(RTD_ISP_ADR)
            iface.deinit_i2c()
        except ConnectionError:
            pass # isPresent = False
        dev_dict.update({ dev: ( dev_dict_[dev], is_present )})
    return dev_dict

def start_interface(device, settings=None):
    iface.init_i2c(device, settings)
    enter_isp()

def setup_flash():
    flash_id = get_flash_id()
    print(f"FLASH ID: {flash_id:#04x}")
    write_reg(0x62, WREN)  # Write Enable opcode
    write_reg(0x63, EWSR)  # Enable Write Status Register opcode
    write_reg(0x6A, READ)  # Read opcode
    write_reg(0x6D, PRGM)  # Program opcode
    write_reg(0x6E, RDSR)  # Read Status Register opcode

def stop_interface():
    reboot_controller()
    iface.deinit_i2c()


def read_flash_file(filename, callback=None):
    with open(filename, "wb") as fr:
        buf, crc_ok = read_flash(READ_SIZE, callback)
        fr.write(bytearray(buf))
        return crc_ok

def write_flash_file(filename, callback=None):
    with open(filename, "rb") as fw:
        data = list(fw.read())
        return program_flash(data, callback)

def interface_get_help():
    return iface.HELP_TEXT


if __name__ == "__main__":
    parser = ArgumentParser(description="Multi-interface RTD2660/RTD2662 firmware progammer.")
    parser.add_argument('-a', '--available-interfaces', action="store_true", dest="list_iface",
                        help='list all available programming interfaces')
    parser.add_argument('-i', '--interface', type=str, dest="interface",
                        help='select what programming interface to use')
    parser.add_argument('-n', '--interface-info', action="store_true", dest="help_iface",
                        help='show interface description and information')
    parser.add_argument('-s', '--settings', type=str, dest="settings",
                        help="set up interface settings")
    parser.add_argument('-l', '--list-devices', action="store_true", dest="list_dev",
                        help='list available interface-devices and whether the controller was detected on them')
    parser.add_argument('-d', '--device', type=str, dest="dev",
                        help='select which interface-device to use')
    parser.add_argument('-r', '--read-output', type=str, dest="read_file",
                        help='read flash into this file')
    parser.add_argument('-e', '--erase', action="store_true", dest="erase",
                        help='erase flash of the controller')
    parser.add_argument('-w', '--write-input', type=str, dest="write_file",
                        help='write flash from this binary file')
    parser.add_argument('-z', '--read-size', type=str, dest="read_size",
                        help='Set the number of bytes to read from flash')
    parser.add_argument('-t', '--trace', action="store_true", dest="trace",
                        help='output full exception trace')
    # TODO: Add read faking, allowing a use of unidirectional interfaces
    args = parser.parse_args(parameters.split(' ') if len(sys.argv) <= 1 and parameters else None)

    try:
        if args.list_iface:
            print("Available interfaces:", end="\n  * ")
            print('\n  * '.join(get_interface_list()))
            exit(0)

        if not args.interface: # If no interface was passed, show help
            parser.print_help()
            exit(0)

        load_interface(args.interface)

        if args.help_iface:
            print(interface_get_help())
            exit(0)

        if args.list_dev:
            dev_list = get_device_list()
            print(" Device Number | Controller detected | Device Name ")
            for dev in sorted(dev_list):
                print(f"{dev:^15}|{'Yes' if dev_list[dev][1] else 'No':^21}| {dev_list[dev][0].strip()}")
            exit(0)

        if not args.dev:
            print("No device passed, using first available...")
            dev_list  = get_device_list()
            dev_found = None
            for dev in dev_list:
                if dev_list[dev][1]:
                    dev_found = dev
                    break
            if dev_found is None:
                print("No device with controller found!")
                exit(1)
            print(f"Found controller on device {dev_found}!")
            args.dev = str(dev_found)

        start_interface(int(args.dev, 0), args.settings) # Interpret the base from the string
        setup_flash()

        if args.erase:
            erase_flash()

        if args.write_file:
            erase_flash()
            if not write_flash_file(args.write_file, lambda s, e, c: progress_bar(c/(e-s))):
                raise ValueError("CRC MISMATCH DETECTED!!!")

        if args.read_file:
            if args.read_size:
                READ_SIZE = int(args.read_size, 0)
            else:
                print(f"WARNING: '-z READ_SIZE' not set, default read amount of {READ_SIZE // 1024} KiB used")
            if not read_flash_file(args.read_file, lambda s, e, c: progress_bar(c/(e-s))):
                raise ValueError("CRC MISMATCH DETECTED!!!!")

        stop_interface()
    except Exception as e:
        if args.trace or len(str(e)) == 0:
            raise e
        else:
            print(e)
            exit(1)
