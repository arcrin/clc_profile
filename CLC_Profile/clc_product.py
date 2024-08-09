from .test_firmware.firmwareutil.resourceshell.py.GPIOResource import GPIOResource
from .test_firmware.firmwareutil.resourceshell.py.ADCResource import ADCResource
from .test_firmware.firmwareutil.resourceshell.py.CANResource import CANResource
from .test_firmware.firmwareutil.resourceshell.py.UARTTestShell import UARTTestShell
from pyDAQ.UART import DAQ_UART

class CLCProduct:
    def __init__(self, daq_uart: DAQ_UART):
        self._test_shell = UARTTestShell(daq_uart,
                                         max_command_length=512,
                                         max_response_length=2048,
                                         debug=True,
                                         default_retries=2)
        self._can = CANResource(self._test_shell, "CAN")

        self.button = {

        }


    @property
    def can(self):
        return self._can