import logging
import re
import typing
from test_jig_util.Lockable import Lockable
from test_jig_util.evaluation import retry_func
import crcmod

_TestShell_crc_func = crcmod.mkCrcFun(poly=0x11021, initCrc=0xFFFF, rev=False, xorOut=0)


class BaseTestShell(Lockable):
    class SHELL_ERROR(Exception): pass
    class IMPLEMENTATION_ERROR(SHELL_ERROR): pass
    class EXECUTION_ERROR(SHELL_ERROR): pass
    class RESOURCE_ERROR(SHELL_ERROR): pass
    class ARGUMENT_ERROR(SHELL_ERROR): pass
    class CHECKSUM_ERROR(SHELL_ERROR): pass

    # class UNKNOWN_ERROR(Exception): pass

    _ERROR_DICT = {
        "IMPLEMENTATION": IMPLEMENTATION_ERROR,
        "EXECUTION": EXECUTION_ERROR,
        "RESOURCE": RESOURCE_ERROR,
        "ARGUMENT": ARGUMENT_ERROR,
        "CHECKSUM": CHECKSUM_ERROR,
    }

    _CHECKSUM_INDICATOR = "~"
    _INTERRUPT_INDICATOR = "\x05"

    class AsyncQuery:
        def __init__(self, shell: 'BaseTestShell', command: str, timeout: typing.Optional[float] = None):
            self._shell = shell
            self._command = self._shell._convert_command(command)
            self._resp_timeout = timeout
            self._result = ""

        def result(self) -> str:
            return self._result

        def __enter__(self):
            # Lock the shell so no other queries are run before __exit__ is called
            self._shell.lock.__enter__()
            self._shell._aquery_start_impl(command=self._command)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            try:
                resp = self._shell._aquery_end_impl(timeout=self._resp_timeout)
            finally:
                self._shell.lock.__exit__(None, None, None)
            self._result = self._shell._validate_response(self._command, resp)

    def __init__(self, max_command_length: int, max_response_length: int, checksum: bool = True, debug: bool = False,
                 exception_handler: typing.Optional[callable] = None, default_retries: int = 0):
        """
        :param max_command_length: Set this to match `RESOURCE_SHELL_INPUT_SIZE` in `resource_shell_config.h` in the test firmware
        :param max_response_length: Set this to match `RESOURCE_SHELL_OUTPUT_SIZE` in `resource_shell_config.h` in the test firmware
        :param debug:
        :param exception_handler:
        """
        super(BaseTestShell, self).__init__()
        self.checksum = checksum
        self.debug = debug
        self.exception_handler = exception_handler
        self.logger = logging.getLogger(str(self))
        self.logger.setLevel(logging.NOTSET if debug else logging.WARNING)
        self._max_command_length = max_command_length
        self._max_response_length = max_response_length
        self.default_retries = default_retries

    def __str__(self) -> str:
        return f"{self.__class__.__name__}<>"

    @property
    def max_command_length(self):
        return self._max_command_length - (5 if self.checksum else 0)

    @property
    def max_response_length(self):
        return self._max_response_length - (5 if self.checksum else 0)

    def _compute_crc(self, data: bytes):
        return _TestShell_crc_func(data)

    def _convert_command(self, command: str):
        if self.checksum:
            crc = self._compute_crc(command.encode())
            command += f"{self._CHECKSUM_INDICATOR}{crc:04x}"
        return command

    def query(self, command: str, timeout: typing.Optional[float] = None, retries: typing.Optional[int] = None) -> str:
        """
        Send out a command message and receive the response. This base class method takes care of handling retries
        and checking the response for TestShell specific error strings.
        NOTE: Do not override this in subclasses. Instead, implement `_query_impl`
        :param command: Command message to send
        :param timeout: Maximum time to wait for response. If None, timeout of the serial port will be used
        :param retries: Number of times to retry if an exception occurs. If None, `self.default_retries` will be used
        :return: Response message
        """

        def query_and_validate():
            r = self._query_impl(command=command, timeout=timeout)
            r = self._validate_response(command, r)
            return r

        if retries is None:
            retries = self.default_retries

        command = self._convert_command(command)

        resp = retry_func(retries)(query_and_validate)()

        return resp

    def aquery(self, command: str, timeout: typing.Optional[float] = None) -> AsyncQuery:
        """
        Create an AsyncQuery instance to be used as a context manager. The command is sent when the context manager
        is entered. The command is terminated when the context manged is exited. For example:
        ```py
        # Create the query
        async_query = shell.aquery(command, timeout)

        # The command is started by entering the `with` statement
        with async_query:
            # Do something while the command is running

        # The command is terminated by exiting the `with` statement

        # Fetch the result of the query
        result = async_query.result()
        ```
        NOTE: Do not override this in subclasses. Instead, implement `_aquery_start_impl` and `_aquery_end_impl`
        :param command: Command message to send
        :param timeout: Maximum time to wait for response. If None, timeout of the serial port will be used
        :return: AsyncQuery context manager object
        """
        return self.AsyncQuery(shell=self, command=command, timeout=timeout)

    def _aquery_start_impl(self, command: str) -> None:
        """
        Send out a command and return immediately, without receiving the response
        :param command: Command message to send
        :return: None
        """
        raise NotImplementedError()

    def _aquery_end_impl(self, timeout: typing.Optional[float] = None) -> str:
        """
        End the async query and receive the response
        :param timeout: Maximum time to wait for response. If None, timeout of the serial port will be used
        :return: Response message
        """
        raise NotImplementedError()

    def _query_impl(self, command: str, timeout: typing.Optional[float] = None) -> str:
        """
        Subclass implementation of `query`. A subclass can either implement _aquery_impl and _read_impl and leave this
        method alone, or implement _query_impl only (aquery will not be available), or implement all three.
        """
        with self.lock:
            self._aquery_start_impl(command)
            response = self._aquery_end_impl(timeout)
        return response

    def _validate_response(self, command: str, response: str) -> str:
        """
        Decode the response and handle error messages specific to ResourceShell
        :param command: The command message that was sent out
        :param response: The response that was received
        :return: None
        """
        try:
            if self.checksum:
                if len(response) < 5 or response[-5] != self._CHECKSUM_INDICATOR:
                    raise self.CHECKSUM_ERROR(f"Checksum not found in response: {response}")

                expected_crc = int(response[-4:], 16)
                actual_crc = self._compute_crc(response[:-5].encode())

                if expected_crc != actual_crc:
                    raise self.CHECKSUM_ERROR(f"Incorrect checksum in response: {actual_crc:04x} != {expected_crc:04x}: {response}")

                response = response[:-5]

            if "ERROR" in response:
                # try to determine error type. Format should be "...ERROR: TYPE - ..."
                match = re.search(r".*ERROR: (.+?) .*", response, re.MULTILINE)

                error_class = None
                error_message = f"'{command}' returned '{response}'"
                if match is not None:
                    error_class = self._ERROR_DICT.get(match.group(1), None)

                if error_class is None:
                    error_message = f"Unknown communication error. {error_message}"
                    error_class = Exception

                raise error_class(error_message)

            return response

        except Exception as e:
            if not isinstance(e, self.SHELL_ERROR) and self.exception_handler:
                self.exception_handler(e)
            else:
                raise
