#!/usr/bin/python3

from genericpath import exists
from importlib   import import_module
from argparse    import ArgumentParser
import os, sys, time
import configparser
import platform

scriptFolder = os.path.dirname(os.path.abspath(__file__)) # Folder where the RTDMultiProg resides
sys.path.insert(0, scriptFolder) # Add RTDMultiProg folder to path for imports

iface  = None
config = None

# Controller's address on I2C bus
RTD2660_ISP_ADR         = 0x4A
RTD2660_ISP_AUTOINC_ADR = RTD2660_ISP_ADR | 1

# Common instructions
CI_NOP   = 0
CI_WRITE = 1
CI_READ  = 2
CI_WRITE_AFTER_WREN = 3
CI_WRITE_AFTER_EWSR = 4
CI_ERASE = 5



def WriteReg(address, data, isAutoinc=False):
    if (type(data) == int):
        data = [ address, data ]
    else:
        data.insert(0, address)
    iface.WriteI2C(RTD2660_ISP_ADR if isAutoinc else RTD2660_ISP_AUTOINC_ADR, data)

def ReadReg(address, count=1):
    iface.WriteI2C(RTD2660_ISP_ADR, [ address ])
    return iface.ReadI2C(RTD2660_ISP_ADR, count)



def EnterISP():
    """ Enable ISP, Disable internal MCU """
    try:
        WriteReg(0x6F, 0x80)
    except IOError:
        pass # Controller doesn't acknowledge the first transaction?
    if ((ReadReg(0x6F)[0] & 0x80) != 0x80):
        raise ConnectionError("Failed to enter into ISP mode")

def RebootController():
    """ Disable ISP, Restart internal MCU """
    WriteReg(0xEE, 0x02)
    WriteReg(0x6F, 0x01)

def GetJedecID():
    return ISPCommonInstruction(CI_READ, 0x9F, 3, 0, 0)



def ISPCommonInstruction(cmd_type, cmd_code, nreads, nwrites, wvalue):
    nreads    = nreads  & 3
    nwrites   = nwrites & 3
    wvalue    = wvalue  & 0xFFFFFF
    reg_value = (cmd_type<<5) | (nwrites<<3) | (nreads<<1)

    WriteReg(0x60, reg_value)
    WriteReg(0x61, cmd_code)
    if nwrites==3:
        WriteReg(0x64, wvalue >> 16)
        WriteReg(0x65, wvalue >> 8)
        WriteReg(0x66, wvalue)
    elif nwrites==2:
        WriteReg(0x64, wvalue >> 8)
        WriteReg(0x65, wvalue)
    elif nwrites==1:
        WriteReg(0x64, wvalue)

    WriteReg(0x60, reg_value | 1)

    while ReadReg(0x60)[0] & 1:
        time.sleep(.001)
        continue

    if   nreads==0:
        return 0
    elif nreads==1:
        return  ReadReg(0x67)[0]
    elif nreads==2:
        return (ReadReg(0x67)[0] << 8)  |  ReadReg(0x68)[0]
    elif nreads==3:
        return (ReadReg(0x67)[0] << 16) | (ReadReg(0x68)[0] << 8) | ReadReg (0x69)[0]
    return 0

# TODO: Merge with ProgramFlash
def ISPRead(address, length, progressCallback=lambda s, e, c: None):
    WriteReg(0x60, 0x46)
    WriteReg(0x61, 0x3)
    WriteReg(0x64, address >> 16)
    WriteReg(0x65, address >> 8)
    WriteReg(0x66, address)
    WriteReg(0x60, 0x47) # Execute the command

    attempts = 0
    while (ReadReg(0x60)[0] & 1):
        time.sleep(.001) # // TODO: add timeout and reset the controller
        if attempts == 100:
            raise TimeoutError("Timed out reading chip")

    data = []
    while length > 0:
        read_len = length
        if read_len > 64:
            read_len = 64
        data += ReadReg(0x70, read_len)
        length -= read_len

    return data

def ISPGetCRC(start, end):
    WriteReg(0x64, start >> 16)
    WriteReg(0x65, start >> 8)
    WriteReg(0x66, start)

    WriteReg(0x72, end >> 16)
    WriteReg(0x73, end >> 8)
    WriteReg(0x74, end)

    WriteReg(0x6F, 0x84)

    attempts = 0
    while not (ReadReg(0x6F)[0] & 2):
        time.sleep(.001)
        if attempts == 100:
            raise TimeoutError("Timed out reading CRC chip")

    return ReadReg(0x75)[0]



def EraseFlash():
    print("Erasing...")
    ISPCommonInstruction(CI_WRITE_AFTER_EWSR, 1, 0, 1, 0) # Unprotect the Status Register
    ISPCommonInstruction(CI_WRITE_AFTER_WREN, 1, 0, 1, 0) # Unprotect the flash
    ISPCommonInstruction(CI_ERASE, 0xC7, 0, 0, 0)         # Erase the flash
    print("done")

def ProgramFlash(chip_size, data, progressCallback=lambda s, e, c: None):
    print("Will write {0:.1f} Kib".format(len(data) / 1024))
    addr = 0
    data_len = len(data)
    data_ptr = 0
    crc = CRC()
    while addr < chip_size and data_len:
        attempts = 0
        while ReadReg (0x6F)[0] & 0x40:
            time.sleep(.001)
            if attempts == 100:
                raise TimeoutError("Timed out reading ready chip")

        #print("Writting addr {0:#04x}".format(addr))
        progressCallback(0, len(data), addr)

        lng = 256
        if lng > data_len:
            lng = data_len
        buff = []
        for i in range(lng):
            buff.append(data[data_ptr+i])

        data_ptr += lng
        data_len -= lng

        if ShouldProgramPage(buff):
            # Set program size-1
            WriteReg(0x71, lng - 1)

            # Set the programming address
            WriteReg(0x64, addr >> 16)
            WriteReg(0x65, addr >> 8)
            WriteReg(0x66, addr)

            # Write the content to register 0x70
            lngtowrite = lng
            startbit = 0
            while lngtowrite > 0:
                prl = 255
                if prl > lngtowrite:
                    prl = lngtowrite
                WriteReg(0x70, buff[startbit:startbit + prl], True)
                startbit   += prl
                lngtowrite -= prl

            WriteReg(0x6F, 0xa0)

        crc.ProcessCRC(buff)
        addr += lng

    progressCallback(0, len(data), len(data)) # Signal done

    attempts = 0
    while ReadReg (0x6F)[0] & 0x40:
        time.sleep(.001)
        if attempts == 100:
            raise TimeoutError("Timed out reading ready chip")

    ISPCommonInstruction(CI_WRITE_AFTER_EWSR, 1, 0, 1, 0x1C)  # Unprotect the Status Register
    ISPCommonInstruction(CI_WRITE_AFTER_WREN, 1, 0, 1, 0x1C)  # Protect the flash

    data_crc = crc.GetCRC()
    chip_crc = ISPGetCRC (0, addr - 1)
    print("Received data CRC {0:#04x}".format(data_crc))
    print("Chip CRC {0:#04x}".format(chip_crc))
    return data_crc == chip_crc

def ReadFlash(chip_size, progressCallback=lambda s, e, c: None):
    data = []
    crc  = CRC()
    addr = 0
    chip_crc = ISPGetCRC(0, chip_size-1)
    while addr < chip_size:
        progressCallback(0, chip_size, addr)

        buf = ISPRead(addr, 1024, progressCallback)
        data.extend(buf)

        crc.ProcessCRC(buf)
        addr += 1024

    progressCallback(0, chip_size, chip_size) # Signal done
    data_crc = crc.GetCRC()
    print("Received data CRC {0:#04x}".format(data_crc))
    print("Chip CRC {0:#04x}".format(chip_crc))
    return (data, data_crc==chip_crc)

def ShouldProgramPage(buff):
    chff = chr(0xff)
    for ch in buff:
        if ch != chff:
            return True
    return False



def SetupChipCommands():
    print("Setup chip commands for Winbond...")
    # These are the codes for Winbond
    WriteReg ( 0x62, 0x06 )  #// Write Enable opcode
    WriteReg ( 0x63, 0x50 )  #// Write Status Register Enable opcode
    WriteReg ( 0x6a, 0x03 )  #// Read opcode
    WriteReg ( 0x6b, 0x0b )  #// Fast Read opcode
    WriteReg ( 0x6d, 0x02 )  #// Program opcode
    WriteReg ( 0x6e, 0x05 )  #// Read Status Register opcode


class CRC():
    """Computes CRC in the memory"""

    def __init__(self):
        self.gCrc = 0

    def ProcessCRC(self, data):
        for byte in data:
            self.gCrc ^= byte << 8
            for i in range(8):
                if self.gCrc & 0x8000:
                    self.gCrc ^= 0x1070 << 3
                self.gCrc <<= 1

    def GetCRC(self):
        return (self.gCrc >> 8) & 0xFF



class BitStream():
    def __init__(self, data):
        self.mask = 0x80
        self.data = data
        self.dataptr = 0
        self.datalen = len(data)

    def HasData(self):
        return self.mask != 0 or self.datalen != 0

    def DataSize(self):
        return self.datalen

    def ReadBit(self):
        if not self.mask:
            self.__NextMask()

        bres = ord(self.data[self.dataptr]) & self.mask
        self.mask >>= 1
        return bres

    def __NextMask(self):
        if self.datalen:
            self.mask = 0x80
            self.dataptr += 1
            self.datalen -= 1

class Nibble(BitStream):
    def Decode(self):
        zerocnt = 0
        while zerocnt < 6:
            if not self.HasData():
                return 0xF0
            if self.ReadBit():
                break
            zerocnt += 1
        if zerocnt > 5:
            if self.DataSize() == 1:
                return 0xF0
            return 0xFF

        if zerocnt == 0:
            return 0x0
        elif zerocnt == 1:
            return 0xF if self.ReadBit() else 0x1
        elif zerocnt == 2:
            return 0x8 if self.ReadBit() else 0x2
        elif zerocnt == 3:
            return 0x7 if self.ReadBit() else 0xC
        elif zerocnt == 4:
            if self.ReadBit():
                return 0x9 if self.ReadBit() else 0x4
            elif self.ReadBit():
                return 0x5 if self.ReadBit() else 0xA
            else:
                return 0xB if self.ReadBit() else 0x3
        elif zerocnt == 5:
            if self.ReadBit():
                return 0xD if self.ReadBit() else 0xE
            else:
                return 0x6 if self.ReadBit() else 0xFF
        return 0xFF

def ComputeGffDecodedSize(data):
    nb = Nibble(data)
    cnt = 0
    while nb.HasData():
        b = nb.Decode()
        if b == 0xFF:
            return 0
        elif b == 0xf0:
            return cnt
        if nb.Decode() > 0xF:
            return 0
        cnt += 1
    return cnt

def DecodeGff(data):
    nb = Nibble (data)
    output = []
    while nb.HasData():
        n1 = nb.Decode()
        if n1 == 0xF0:
            return (True, ''.join(chr(i) for i in output))
        elif n1 == 0xFF:
            return (False, None)
        n2 = nb.Decode()
        if n2 > 0xF:
            return (False, None)
        output.append ( (n1<<4)|n2 )
    return (True, ''.join(chr(i) for i in output))



def GetInterfaceList():
    """ Get string array of all available interfaces """
    ifList = os.listdir(scriptFolder+os.sep+"interfaces")
    for interface in ifList: # Remove folders without main.py file
        if not exists(scriptFolder+os.sep+"interfaces" + os.sep + interface + os.sep + "main.py"):
            ifList.pop(ifList.index(interface))
    return ifList

def LoadInterface(interface):
    try:
        ifaceModule = import_module("interfaces."+interface+"."+"main").I2C
    except ModuleNotFoundError: # Rethrow exception with our message
        raise ModuleNotFoundError("Interface \"{0}\" not found or is incorrect.".format(interface))

    # Test if all systems are supported or we are in supported systems
    if not (ifaceModule.AvailableSystems == [""] or platform.system() in ifaceModule.AvailableSystems):
        raise SystemError("Interface supports {0}; not {1}".format(', '.join(ifaceModule.AvailableSystems), platform.system()))
    # Test if all architectures are supported or we are in supported architectures
    if not (ifaceModule.AvailableArchitectures == [""] or platform.architecture()[0] in ifaceModule.AvailableArchitectures):
        raise SystemError("Interface supports {0}; not {1}\n{2}".format(', '.join(ifaceModule.AvailableArchitectures), platform.architecture()[0],
                          "If the interface doesn't support 32 or 64 bit architecture, try running it with 64 or 32 bit python."))

    global iface
    iface = ifaceModule()

def GetDeviceList():
    devDict_ = iface.ListI2C()
    devDict = {}
    for dev in devDict_:
        isPresent = False
        try:
            iface.InitI2C(dev)
            WriteReg(0x6F, 0x80)
            if ReadReg(0x6F)[0] & 0x80: # If no device on bus then, addressing them will result in pulled up sda
                isPresent = True
            WriteReg(0x6F, 0x00)
            iface.DeinitI2C()
        except ConnectionError:
            pass # isPresent = False
        devDict.update({ dev: ( devDict_[dev], isPresent )})
    return devDict

def StartInterface(device):
    iface.InitI2C(device)
    EnterISP()

    configs = configparser.ConfigParser()
    configs.read(scriptFolder+os.sep+"flashDevices.cfg")

    jedecID = ISPCommonInstruction(CI_READ, 0x9f, 3, 0, 0)
    print("JEDEC ID: 0x%x" % jedecID)

    SetupChipCommands()

    global config
    for config_ in configs:
        if (config_ == "DEFAULT"):
            continue
        if int(configs[config_]["Signature"], 16) == jedecID:
            config = configs[config_]
            break
    if not config:
        print("No matching device for ID {0:#010x} found, try adding device parameters to flashDevices.cfg".format(jedecID))
        return 1

    print("DEVICE:   " + config_)
    return 0

def StopInterface():
    RebootController()
    iface.DeinitI2C()

def ReadFlashFile(filename, callback=None):
    fr = open(filename, "wb")
    (buf, crcOK) = ReadFlash(int(config["Size"], 16), callback)
    fr.write(bytearray(buf))

def WriteFlashFile(filename, callback=None):
    fsize = os.stat(filename).st_size
    with open (filename, "rb") as fl:
        data = fl.read()
    if data[0:12] == "GMI GFF V1.0":
        print("Detected GFF image")
        if fsize < 256:
            print("This file looks too small {0}".format(fsize))
            return None
        result, out = DecodeGff(data[256:])
        if result:
            return out
        else:
            return None
    ProgramFlash(int(config["Size"], 16), data, callback)

def InterfaceGetHelp():
    return iface.HelpText

def ProgresssBar(value):
    """Print progress line. Value is from 0 to 1"""
    print("Progress: |{0}| {1:6.1%}".format(
        ("#" * int(value * 25)).ljust(25),
        value),
        end="\r") # Go back to the beggining of line
    if (value == 1):
        print() # Auto new line on 100%

if __name__ == "__main__":
    parser = ArgumentParser(description="Multi-interface RTD266X firmware progammer.")
    parser.add_argument('-a', '--available-interfaces', action="store_true", dest="listIface",
                        help='List all interfaces')
    parser.add_argument('-n', '--interface-info', action="store_true", dest="helpInterface",
                        help='Description of the interface')
    parser.add_argument('-i', '--interface', type=str, dest="interface",
                        help='Programming interface')
    parser.add_argument('-l', '--list-devices', action="store_true", dest="listDev",
                        help='List devices from interface')
    parser.add_argument('-d', '--device', type=str, dest="dev",
                        help='Select device from interface')
    parser.add_argument('-e', '--erase', action="store_true", dest="erase",
                        help='Erase flash of the controller')
    parser.add_argument('-w', '--write-input', type=str, dest="writeFile",
                        help='Write flash from file (Binary or GFF)')
    parser.add_argument('-r', '--read-output', type=str, dest="readFile",
                        help='Read flash and write to file')
    parser.add_argument('-t', '--trace', action="store_true", dest="trace",
                        help='Output full exception trace')
    args = parser.parse_args()
    #args.interface = "i2cdev"
    try:
        if args.listIface or (not args.interface):
            print("Available interfaces:", end="\n  * ")
            print('\n  * '.join(GetInterfaceList()))
            exit(0)
        LoadInterface(args.interface)

        if args.helpInterface:
            InterfaceGetHelp()

        if args.listDev or not args.dev:
            devList = GetDeviceList()
            print(" Device Number | Controller detected | Device Name ")
            for dev in devList:
                print("{0:^15}|{1:^21}| {2}".format(dev, "Yes" if devList[dev][1] else "No", devList[dev][0].strip()))
            exit(0)
        StartInterface(int(args.dev, 0)) # Interpret the base from the string as an integer literal.

        if args.erase:
            EraseFlash()

        if args.writeFile != None:
            EraseFlash()
            WriteFlashFile(args.writeFile, lambda s, e, c: ProgresssBar(c/(e-s)))

        if args.readFile != None:
            ReadFlashFile(args.readFile, lambda s, e, c: ProgresssBar(c/(e-s)))

        StopInterface()
    except Exception as e:
        if args.trace:
            raise e
        else:
            print(e)
