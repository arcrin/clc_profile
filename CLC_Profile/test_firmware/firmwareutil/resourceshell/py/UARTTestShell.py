from serial import SerialBase
import typing
from test_jig_util.timing import Timeout
from .BaseTestShell import BaseTestShell


class UARTTestShell(BaseTestShell):
    ENDING = b"\n"
    PROMPT = b"\n>"

    def __init__(self, ser: SerialBase, max_command_length: int, max_response_length: int, checksum: bool = True,
                 debug: bool = False, exception_handler: typing.Optional[callable] = None, default_retries: int = 0):
        """
        :param ser:
        :param debug:
        :param exception_handler:
        :param default_retries:
        """
        self.ser = ser
        super(UARTTestShell, self).__init__(max_command_length=max_command_length, max_response_length=max_response_length, checksum=checksum,
                                            debug=debug, exception_handler=exception_handler, default_retries=default_retries)
        self._current_msg = b""

    def __str__(self) -> str:
        return f"{self.__class__.__name__}<{self.ser.port}>"

    def _send_command(self, command: str) -> bytes:
        """Return the encoded message for future use"""
        msg = command.encode() + self.ENDING

        if len(command) > self.max_command_length:
            raise self.SHELL_ERROR(f"Command too long: {command}")

        resp = b""
        while self.ser.inWaiting():
            resp += self.ser.read_all()

        if resp:
            self.logger.warning(f"Query --: {resp.decode(errors='replace')}")

        self.logger.debug(f"Query ->: {command}")
        self.ser.write(msg)
        return msg

    def _receive_response(self, command: bytes, timeout: typing.Optional[float] = None) -> str:
        resp = bytearray()
        _timeout = Timeout(timeout if timeout else self.ser.timeout)

        while not _timeout.expired():
            resp += self.ser.read(1)

            promptPos = resp.find(self.PROMPT)
            if promptPos >= 0:
                self.logger.debug(f"Query <-: {resp.decode(errors='replace')}")

                if (resp[:len(command)]) != command:
                    raise Exception(f"Query strict failure (command): {resp.decode(errors='replace')}")

                if promptPos + 2 != len(resp):
                    raise Exception(f"Query strict failure (response): {resp.decode(errors='replace')}")

                resp = resp[len(command):promptPos].decode(errors="replace")
                return resp

        self.logger.error(f"Query fail (timeout): {resp.decode(errors='replace')}")
        raise Exception(f"Query failed (timeout): {resp.decode(errors='replace')}")

    def _aquery_start_impl(self, command: str) -> None:
        self._current_msg = self._send_command(command)

    def _aquery_end_impl(self, timeout: typing.Optional[float] = None) -> str:
        # Finish the async query
        self.ser.write(self._INTERRUPT_INDICATOR.encode())
        resp = self._receive_response(self._current_msg, timeout)
        return resp

    def _query_impl(self, command: str, timeout: typing.Optional[float] = None) -> str:
        msg = self._send_command(command)
        resp = self._receive_response(msg, timeout)
        return resp
