# SPI flash opcodes
WREN = 0x06
WRDI = 0x04
RDSR = 0x05
EWSR = 0x50
WRSR = 0x01
READ = 0x03
PRGM = 0x02
ERAS = 0x60
RDID = 0x9F

PAGE_SIZE = 128

# Default read size 512 KiB
READ_SIZE = 512 * 2**10
