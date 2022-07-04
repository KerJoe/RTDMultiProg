import time
from ..misc.funcs import *

class SoftwareI2C:
	I2C_FREQ = 100000 # I2C clock max frequency 100kHz

	I2C_READ  = 1
	I2C_WRITE = 0

	I2C_ACK   = 0
	I2C_NACK  = 1

	I2C_HALFPERIOD = (1e6 / I2C_FREQ) / 2000

	I2C_SET_PIN_INPUT  = 0
	I2C_SET_PIN_OUTPUT = 1

	SDA = 0
	SCL = 1


	def __init__(
			self,
			set_sda_callback, get_sda_callback,
			set_scl_callback, get_scl_callback=lambda: 1): # getSCLCallback isn't a must for Master->Slave comunication
		self.set_sda = set_sda_callback
		self.get_sda = get_sda_callback
		self.set_scl = set_scl_callback
		self.get_scl = get_scl_callback

		self._reset()

	def __del__(self):
		self._reset()

	def _pull(self, pin):
		"""Drive the line to level LOW"""
		if pin == self.SDA:
			self.setSDAMode(self.I2C_SET_PIN_OUTPUT)
			self.set_sda(0)
		else:
			self.setSCLMode(self.I2C_SET_PIN_OUTPUT)
			self.set_scl(0)
		time.sleep(self.I2C_HALFPERIOD)

	def _release(self,pin):
		"""Release the line and return line status"""
		if pin == self.SDA:
			self.setSDAMode(self.I2C_SET_PIN_INPUT)
			self.set_sda(1)
			time.sleep(self.I2C_HALFPERIOD)
			return self.get_sda()
		else:
			self.setSCLMode(self.I2C_SET_PIN_INPUT)
			self.set_scl(1)
			time.sleep(self.I2C_HALFPERIOD)
			return self.get_scl()

	def _release_wait(self):
		"""In case of clock stretching or busy bus we must wait"""
		poll(lambda: not self.get_scl(), "SCL stuck low")
		time.sleep(self.I2C_HALFPERIOD)

	def _reset(self):
		"""Reset bus sequence"""
		self._release(self.SDA)
		while True:
			for _ in range(9):
				self._pull(self.SCL)
				self._release(self.SCL)
			if not self.get_sda():
				break

		self._pull(self.SCL)
		self._pull(self.SDA)

		self._stop()

	def _start(self):
		"""Pull SDA while SCL is up
		Best practice is to ensure the bus is not busy before start"""
		if not self._release(self.SDA):
			self._reset()
		self._release_wait(self.SCL)

		self._pull(self.SDA)
		self._pull(self.SCL)

	def _stop(self):
		"""Release SDA while SCL is up"""
		self._release_wait(self.SCL)
		if not self._release(self.SDA):
			self._reset()

	def _write_bit(self, bit):
		"""Send 0 or 1:
		Clock down, send bit, clock up, wait, clock down again
		In clock stretching, slave holds the clock line down in order
		to force master to wait before send more data """
		if bit:
			self._release(self.SDA)
		else:
			self._pull(self.SDA)

		self._release_wait(self.SCL)
		self._pull(self.SCL)

		self._pull(self.SDA)

	def _read_bit(self):
		"""Read a bit from sda"""
		self._release(self.SDA)
		self._release_wait(self.SCL)
		bit = self.get_sda()
		self._pull(self.scl)
		self._pull(self.sda)
		return bit

	def _write_byte(self, byte):
		"""Send 8 bits in a row, MSB first and reads ACK.
		Returns I2C_ACK if device ack'ed"""
		for _ in range(8):
			self._write_bit(byte & 0x80)
			byte = byte << 1
		return bool(self._read_bit())

	def _read_byte(self):
		"""Read a byte, MSB first"""
		byte = 0x00
		for _ in range(8):
			byte = (byte << 1) | self._read_bit()
		return byte


	def write(self, address, data):
		"""Write data to I2C bus"""
		self._start()
		self._write_byte(address)
		for byte in data:
			self._write_byte(byte)
		self._stop()

	def read(self, address, count):
		"""Read data from I2C bus"""
		self._start()
		self._write_byte(address)
		data = []
		for _ in range(count):
			data += self._read_byte()
		self._stop()
