import time

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



	def __init__(self, setSDACallback, getSDACallback, setSCLCallback, getSCLCallback=lambda: 1, setSDAMode=lambda: None, setSCLMode=lambda: None): # getSCLCallback is not requered for Master->Slave comunication
		self.setSDA = setSDACallback
		self.getSDA = getSDACallback
		self.setSCL = setSCLCallback
		self.getSCL = getSCLCallback		

		self.reset()



	def pull(self, pin):
		"""Drives the line to level LOW"""
		if pin == self.SDA:
			self.setSDAMode(self.I2C_SET_PIN_OUTPUT)
			self.setSDA(0)
		else:
			self.setSCLMode(self.I2C_SET_PIN_OUTPUT)
			self.setSCL(0)
		time.sleep(self.I2C_HALFPERIOD)

	def release(self,pin):
		"""Releases the line and returns line status"""
		if pin == self.SDA:
			self.setSDAMode(self.I2C_SET_PIN_INPUT)
			self.setSDA(1)
			time.sleep(self.I2C_HALFPERIOD)
			return self.getSDA()
		else:
			self.setSCLMode(self.I2C_SET_PIN_INPUT)
			self.setSCL(1)
			time.sleep(self.I2C_HALFPERIOD)
			return self.getSCL()

	def release_wait(self):
		"""In case of clock stretching or busy bus we must wait"""				
		while(not(self.getSCL())):
			time.sleep(0.1) # TODO: add timeout
		time.sleep(self.I2C_HALFPERIOD)



	def reset(self):
		"""Reset bus sequence"""
		self.release(self.SDA)
		while True:
			for i in range(9):
				self.pull(self.SCL)
				self.release(self.SCL)
			if(not(self.getSDA())):
				break

		self.pull(self.SCL)
		self.pull(self.SDA)

		self.stop()

	def start(self):
		"""Pull SDA while SCL is up
		Best practice is to ensure the bus is not busy before start"""
		if (not(self.release(self.SDA))):
			self.reset()
		self.release_wait(self.SCL)

		self.pull(self.SDA)
		self.pull(self.SCL)		

	def stop(self):
		"""Release SDA while SCL is up"""
		self.release_wait(self.SCL)
		if(not(self.release(self.SDA))):
			self.reset()

	def send_bit(self, bit):
		"""Sends 0 or 1: 
		Clock down, send bit, clock up, wait, clock down again 
		In clock stretching, slave holds the clock line down in order
		to force master to wait before send more data """
		if(bit):
			self.release(self.SDA)
		else:
			self.pull(self.SDA)

		self.release_wait(self.SCL)
		self.pull(self.SCL)

		self.pull(self.SDA)

	def read_bit(self):
		"""Reads a bit from sda"""
		self.release(self.SDA)
		self.release_wait(self.SCL)
		s = self.getSDA()
		self.pull(self.scl)
		self.pull(self.sda)
		return s

	def send_byte(self, byte):
		"""Sends 8 bits in a row, MSB first and reads ACK.
		Returns I2C_ACK if device ack'ed"""
		for i in range(8):
			self.send_bit(byte & 0x80)
			byte = byte << 1

		self.read_bit()

	def read_byte(self):
		"""Reads a byte, MSB first"""
		byte = 0x00
		for i in range(8):
			byte = (byte << 1) | self.read_bit()

		return byte