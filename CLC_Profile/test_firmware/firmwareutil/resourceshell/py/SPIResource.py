from pyDAQ.SPI import BaseSPI
from .BaseTestShell import BaseTestShell
import codecs
import struct


class SPIResource(BaseSPI):
	def __init__(self, test_shell: BaseTestShell, spi_port: str, *args, **kwargs):
		self._port = spi_port
		self._peripheral_name = f"{self.__class__.__name__}<{self._port}>"
		super().__init__(*args, **kwargs)
		self._shell = test_shell


	@property
	def peripheral_name(self):
		return self._peripheral_name

	def configure(self, config_name):
		self._shell.query(f"spi conf {self._port} {config_name}")

	def _reconfigure(self):
		pass

	def transfer(self, data: bytes, read_length: int = 0, finish: bool = True, assert_per_byte: bool = False) -> bytes:
		"""
		Transfer data with the device
		:param data: Data to write
		:param read_length: Non-zero implies two half duplex transfers, a write followed by a read
		:param finish: True to de-assert CS at the end of the transfer. False to leave it asserted
		:param assert_per_byte: True to briefly de-assert CS after each byte. False to keep CS asserted for the entire transfer
		:return: The data that was read back. If `read_length` == 0, a full-duplex transfer occurs, so the
			response length is equal to the data length
		"""
		prefix = f"spi wr {self._port} {int(read_length)} {int(finish)} {int(assert_per_byte)} "
		# TODO _shell may add some bytes to the message. Subtract a few here to be safe
		assert (len(data) * 2 + len(prefix) + 10) <= self._shell.max_command_length
		hexdata = codecs.encode(bytearray(data), "hex").decode("utf-8")

		resp = self._shell.query(f"{prefix}{hexdata}")
		resp = codecs.decode(resp, "hex")

		if len(resp) != len(data):
			raise Exception("SPI returned less data than expected")

		return resp