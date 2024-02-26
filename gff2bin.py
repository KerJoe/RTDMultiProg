#!/usr/bin/env python3
# WARNING: UNTESTED

import sys

class BitStream():
    def __init__(self, data):
        self.mask = 0x80
        self.data = data
        self.data_ptr = 0
        self.data_len = len(data)

    def has_data(self):
        return self.mask != 0 or self.data_len != 0

    def data_size(self):
        return self.data_len

    def read_bit(self):
        if not self.mask:
            self._next_mask()

        bres = self.data[self.data_ptr] & self.mask
        self.mask >>= 1
        return bres

    def _next_mask(self):
        if self.data_len:
            self.mask = 0x80
            self.data_ptr += 1
            self.data_len -= 1

class Nibble(BitStream):
    def decode(self):
        zero_cnt = 0
        while zero_cnt < 6:
            if not self.has_data():
                return 0xF0
            if self.read_bit():
                break
            zero_cnt += 1
        if zero_cnt > 5:
            if self.data_size() == 1:
                return 0xF0
            return 0xFF

        if zero_cnt == 0:
            return 0x0
        elif zero_cnt == 1:
            return 0xF if self.read_bit() else 0x1
        elif zero_cnt == 2:
            return 0x8 if self.read_bit() else 0x2
        elif zero_cnt == 3:
            return 0x7 if self.read_bit() else 0xC
        elif zero_cnt == 4:
            if self.read_bit():
                return 0x9 if self.read_bit() else 0x4
            elif self.read_bit():
                return 0x5 if self.read_bit() else 0xA
            else:
                return 0xB if self.read_bit() else 0x3
        elif zero_cnt == 5:
            if self.read_bit():
                return 0xD if self.read_bit() else 0xE
            else:
                return 0x6 if self.read_bit() else 0xFF
        return 0xFF

def compute_gff_decoded_size(data):
    nb = Nibble(data)
    cnt = 0
    while nb.has_data():
        b = nb.decode()
        if b == 0xFF:
            return 0
        elif b == 0xf0:
            return cnt
        if nb.decode() > 0xF:
            return 0
        cnt += 1
    return cnt

def decode_gff(data):
    nb = Nibble(data)
    output = []
    while nb.has_data():
        n1 = nb.decode()
        if n1 == 0xF0:
            return (True, ''.join(chr(i) for i in output))
        elif n1 == 0xFF:
            return (False, None)
        n2 = nb.decode()
        if n2 > 0xF:
            return (False, None)
        output.append ( (n1<<4)|n2 )
    return (True, ''.join(chr(i) for i in output))

if __name__ == "__main__":
    if any(item in ['-h', '--help', '-?'] for item in sys.argv):
        print("Convert encoded GFF firmware files into plain bin.\n"
              "Usage: 'gff2bin.py < input.gff > output.bin' ")
        exit(0)

    try:
        data = sys.stdin.buffer.read()
        if data[0:12] == "GMI GFF V1.0":
            if len(data) < 256:
                raise ValueError(f"This file looks too small {len(data)}")
            result, out = decode_gff(data[256:])
            if not result:
                raise ValueError("GFF decoding failed")
        else:
            raise ValueError("Failed to find GFF signature")
    except ValueError as err:
        print(err, file=sys.stderr)
        exit(1)

    sys.stdout.buffer.write(data)
