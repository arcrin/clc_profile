from .test_firmware.firmwareutil.resourceshell.py.GPIOResource import GPIOResource
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

        self.led_green = GPIOResource(self.test_shell, "LED_GREEN")
        self.led_red = GPIOResource(self.test_shell, "LED_RED")
        self.led_sys_green = GPIOResource(self.test_shell, "LED_SYS_GREEN")
        self.led_sys_red = GPIOResource(self.test_shell, "LED_SYS_RED")
        self.led_can_err = GPIOResource(self.test_shell, "LED_CAN_ERR")

        self.tens_address_pins = [
            GPIOResource(self.test_shell, "ADDR_1"),
            GPIOResource(self.test_shell, "ADDR_2"),
            GPIOResource(self.test_shell, "ADDR_3"),
            GPIOResource(self.test_shell, "ADDR_4"),
        ]

        self.ones_address_pins = [
            GPIOResource(self.test_shell, "ADDR_5"),
            GPIOResource(self.test_shell, "ADDR_6"),
            GPIOResource(self.test_shell, "ADDR_7"),
            GPIOResource(self.test_shell, "ADDR_8"),
        ]

    @property
    def can(self):
        return self._can

    @property
    def test_shell(self):
        return self._test_shell