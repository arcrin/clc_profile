from framework.components.front_panel.front_panel import FrontPanel
from framework.components.test_jig import TestJig
from pyDAQ.UniversalIO import UniversalIO, I2C, DAQ
from pyDAQ.UART import DAQ_UART
from pyDAQ.Sensors import TCS3472
from pyDAQ.Expanders import PCA9535A_GPIO, TCA9546A_I2C
from .test_firmware.firmwareutil.resourceshell.py.GPIOResource import GPIOResource
from .test_firmware.firmwareutil.resourceshell.py.ADCResource import ADCResource
from .test_firmware.firmwareutil.resourceshell.py.UARTTestShell import UARTTestShell
from interface.OpenOCD.OpenOCD import OpenOCD
from interface.wdi_simple import install_programmer_hub
from enum import Enum
from time import sleep
from abc import ABC, abstractmethod
import logging
import typing
import os


class CLC_Jig(TestJig, ABC):

    def __init__(self):
        install_programmer_hub()
        daq_ports = DAQ.FindDAQs()

        assert len(daq_ports) == 2, "Expected 2 DAQs, found {}".format(len(daq_ports))

        _daqs = [UniversalIO(port=port.device) for port in daq_ports]
        _a: typing.Dict[int, UniversalIO] = {int(daq.write("address")): daq for daq in _daqs}
        self.daq1 = _a[1]
        self.daq2 = _a[2]
        top_pneumatic_control_expansion = self.daq2.EXP3
        self.rms6_button_control = top_pneumatic_control_expansion.create_gpio1(mode="op", default=0)
        self.gsm8_button_control = top_pneumatic_control_expansion.create_gpio0(mode="op", default=0)

        front_panel_i2c = I2C(self.daq2, 'EXP8', frequency=100000)
        self.front_panel = FrontPanel(front_panel_i2c)

        """
            The UART test shell may need to be created whenever a new 
            product is loaded. However, the UART instance is created 
            on initialization of the test jig class
        """
        self._dut_uart = DAQ_UART(self.daq2, "EXP1", baudrate=115200, timeout=2)
        self._test_shell = UARTTestShell(self._dut_uart,
                                         max_command_length=512,
                                         max_response_length=2048,
                                         debug=True,
                                         default_retries=2)

        """
            Voltage pogo pins are different based on the DUT
        """
        self.rms6_voltage_rails = {
            "3V3": self.daq2.IO1,
            "5V0": self.daq2.IO2,
            "PWR_OUT": self.daq2.AI17,
            "SW1_PWR": self.daq2.AI18,  # 18V ~ 23V
            "SW2_PWR": self.daq2.AI19,
            "SW3_PWR": self.daq2.AI20,
            "SW4_PWR": self.daq2.AI21,
            "SW5_PWR": self.daq2.AI22,
            "SW6_PWR": self.daq2.AI23
        }

        top_board_i2c = I2C(self.daq2, "EXP6", frequency=100000)

        """
            Connector probes    
        """

        tp40 = PCA9535A_GPIO(top_board_i2c, 0x27, 0, inverted_logic=True)
        tp39 = PCA9535A_GPIO(top_board_i2c, 0x27, 1, inverted_logic=True)
        tp38 = PCA9535A_GPIO(top_board_i2c, 0x27, 2, inverted_logic=True)
        tp37 = PCA9535A_GPIO(top_board_i2c, 0x27, 3, inverted_logic=True)
        tp36 = PCA9535A_GPIO(top_board_i2c, 0x27, 4, inverted_logic=True)
        tp35 = PCA9535A_GPIO(top_board_i2c, 0x27, 5, inverted_logic=True)
        tp34 = PCA9535A_GPIO(top_board_i2c, 0x27, 6, inverted_logic=True)
        tp33 = PCA9535A_GPIO(top_board_i2c, 0x27, 7, inverted_logic=True)
        tp32 = PCA9535A_GPIO(top_board_i2c, 0x27, 8, inverted_logic=True)
        tp31 = PCA9535A_GPIO(top_board_i2c, 0x27, 9, inverted_logic=True)
        tp46 = PCA9535A_GPIO(top_board_i2c, 0x27, 10, inverted_logic=True)
        tp45 = PCA9535A_GPIO(top_board_i2c, 0x27, 11, inverted_logic=True)
        tp44 = PCA9535A_GPIO(top_board_i2c, 0x27, 12, inverted_logic=True)
        tp43 = PCA9535A_GPIO(top_board_i2c, 0x27, 13, inverted_logic=True)
        tp42 = PCA9535A_GPIO(top_board_i2c, 0x27, 14, inverted_logic=True)
        tp41 = PCA9535A_GPIO(top_board_i2c, 0x27, 15, inverted_logic=True)

        self.gms8_connector_probes = {
            "GSM8_right_center_bottom_connector": tp40,
            "GSM8_right_center_top_connector": tp39,
            "GSM8_middle_bottom_connector": tp35,
            "GSM8_right_top_connector": tp31,
            "GSM8_left_center_connector": tp46,
            "GSM8_left_bottom_connector": tp45,
            "GSM8_left_top_connector": tp44,
            "GSM8_right_bottom_connector": tp43,
            "GSM8_middle_top_connector": tp41
        }

        self.rms6_connector_probes = {
            "RMS_right_top_connector": tp38,
            "RMS_left_bottom_connector": tp37,
            "RMS_middle_top_connector": tp36,
            "RMS_left_center_connector": tp34,
            "RMS_left_top_connector": tp33,
            "RMS_middle_bottom_connector": tp32,
            "RMS_right_bottom_connector": tp42,
        }

        """
            LED 
        """
        # Sensors
        rms6_led_u1 = TCA9546A_I2C(top_board_i2c, 0x74, 0)
        rms6_led_u2 = TCA9546A_I2C(top_board_i2c, 0x74, 1)
        rms6_led_u3 = TCA9546A_I2C(top_board_i2c, 0x74, 2)
        rms6_led_u4 = TCA9546A_I2C(top_board_i2c, 0x74, 3)
        rms6_led_u7 = TCA9546A_I2C(top_board_i2c, 0x75, 0)
        rms6_led_u8 = TCA9546A_I2C(top_board_i2c, 0x75, 1)
        rms6_led_u10 = TCA9546A_I2C(top_board_i2c, 0x75, 2)
        rms6_led_u11 = TCA9546A_I2C(top_board_i2c, 0x75, 3)

        self.rms6_led_sensor = {
            "CAN": TCS3472(rms6_led_u1),
            "SYS": TCS3472(rms6_led_u2),
            "RLY1": TCS3472(rms6_led_u4),
            # "RLY2": TCS3472(rms6_led_u3),
            "RLY3": TCS3472(rms6_led_u7),
            "RLY4": TCS3472(rms6_led_u8),
            "RLY5": TCS3472(rms6_led_u10),
            "RLY6": TCS3472(rms6_led_u11)
        }

        self.rms6_led_control = {

        }

        gsm8_led_u12 = TCA9546A_I2C(top_board_i2c, 0x76, 0)
        gsm8_led_u13 = TCA9546A_I2C(top_board_i2c, 0x76, 1)
        gsm8_led_u14 = TCA9546A_I2C(top_board_i2c, 0x76, 2)
        gsm8_led_u15 = TCA9546A_I2C(top_board_i2c, 0x76, 3)
        gsm8_led_u17 = TCA9546A_I2C(top_board_i2c, 0x77, 0)
        gsm8_led_u18 = TCA9546A_I2C(top_board_i2c, 0x77, 1)
        gsm8_led_u20 = TCA9546A_I2C(top_board_i2c, 0x77, 2)
        gsm8_led_u21 = TCA9546A_I2C(top_board_i2c, 0x77, 3)
        gsm8_led_u22 = TCA9546A_I2C(top_board_i2c, 0x70, 0)
        gsm8_led_u23 = TCA9546A_I2C(top_board_i2c, 0x70, 1)
        gsm8_led_u25 = TCA9546A_I2C(top_board_i2c, 0x70, 2)
        gsm8_led_u26 = TCA9546A_I2C(top_board_i2c, 0x70, 3)

        self.gsm8_leds = {

        }

        kw = {"extra_args": ("-d-3",)}
        self._oocd = None

        # Test firmware resources
        self.led_green = GPIOResource(self.test_shell, "LED_GREEN")
        self.led_red = GPIOResource(self.test_shell, "LED_RED")

        self.rms6_led_test_firmware_resources = {
            "SW311": GPIOResource(self.test_shell, "LED_SW311"),
            "SW301": GPIOResource(self.test_shell, "LED_SW301"),
            "SW312": GPIOResource(self.test_shell, "LED_SW312"),
            "SW302": GPIOResource(self.test_shell, "LED_SW302"),
            "SW313": GPIOResource(self.test_shell, "LED_SW313"),
            "SW303": GPIOResource(self.test_shell, "LED_SW303"),
        }

        """
            Buttons
        """
        self.rms6_push_button_resources = {
            "push_button_sw311": GPIOResource(self.test_shell, "SW311_PB"),
            "push_button_sw301": GPIOResource(self.test_shell, "SW301_PB"),
            "push_button_sw312": GPIOResource(self.test_shell, "SW312_PB"),
            "push_button_sw302": GPIOResource(self.test_shell, "SW302_PB"),
            "push_button_sw313": GPIOResource(self.test_shell, "SW313_PB"),
            "push_button_sw303": GPIOResource(self.test_shell, "SW303_PB"),
        }

        """
            Relay
        """
        wiring_board_gpio_expander_i2c = I2C(self.daq2, "EXP5", frequency=100000)
        self.rms6_relay_control = {
            "relay1_off": (GPIOResource(self.test_shell, "RLYA_OFF1"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 0)),
            "relay1_on": (GPIOResource(self.test_shell, "RLYA_ON1"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 1)),
            "relay2_off": (GPIOResource(self.test_shell, "RLYB_OFF1"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 2)),
            "relay2_on": (GPIOResource(self.test_shell, "RLYB_ON1"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 3)),
            "relay3_off": (GPIOResource(self.test_shell, "RLYA_OFF2"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 4)),
            "relay3_on": (GPIOResource(self.test_shell, "RLYA_ON2"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 5)),
            "relay4_off": (GPIOResource(self.test_shell, "RLYB_OFF2"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 6)),
            "relay4_on": (GPIOResource(self.test_shell, "RLYB_ON2"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 7)),
            "relay5_off": (GPIOResource(self.test_shell, "RLYA_OFF3"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 8)),
            "relay5_on": (GPIOResource(self.test_shell, "RLYA_ON3"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 9)),
            "relay6_off": (GPIOResource(self.test_shell, "RLYB_OFF3"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 10)),
            "relay6_on": (GPIOResource(self.test_shell, "RLYB_ON3"),PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 11)),
        }

        """
            Switch
        """
        self.rms6_switch_on_control = PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x23, 12, mode="op")
        self.rms6_switch_off_control = PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x23, 12, mode="op")




        """
            Address
        """
        self.rms6_address_test_firmware_resources = {
            "address_pin_01": GPIOResource(self.test_shell, "ADDR_01"),
            "address_pin_02": GPIOResource(self.test_shell, "ADDR_02"),
            "address_pin_04": GPIOResource(self.test_shell, "ADDR_04"),
            "address_pin_08": GPIOResource(self.test_shell, "ADDR_08"),
            "address_pin_11": GPIOResource(self.test_shell, "ADDR_11"),
            "address_pin_12": GPIOResource(self.test_shell, "ADDR_12"),
            "address_pin_14": GPIOResource(self.test_shell, "ADDR_14"),
            "address_pin_18": GPIOResource(self.test_shell, "ADDR_18"),
        }


        """
            Relay feedback
        """
        self.rms6_relay_feedback = {
            "relay_a_feedback_1": ADCResource(self.test_shell, "RLYA_FB1"),
            "relay_b_feedback_1": ADCResource(self.test_shell, "RLYB_FB1"),
            "relay_a_feedback_2": ADCResource(self.test_shell, "RLYA_FB2"),
            "relay_b_feedback_2": ADCResource(self.test_shell, "RLYB_FB2"),
            "relay_a_feedback_3": ADCResource(self.test_shell, "RLYA_FB3"),
            "relay_b_feedback_3": ADCResource(self.test_shell, "RLYB_FB3"),
        }


    @property
    def test_shell(self):
        return self._test_shell

    @property
    def oocd(self):
        return self._oocd

    @oocd.setter
    def oocd(self, value: OpenOCD):
        self._oocd = value

    def dut_setup(self, dut, **kwargs):
        pass

    def cleanup(self):
        pass

    def get_front_panel_options(self) -> typing.Tuple['BaseI2C', int]:
        return self.front_panel._i2c, 0

    def dut_power_on(self):
        self.daq2["VOUT_enable"].value = 1

    def dut_power_off(self):
        self.daq2["VOUT_enable"].value = 0

    def dut_power_cycle(self, delay: int=0.1):
        self.dut_power_off()
        sleep(delay)
        self.dut_power_on()

    def rms6_button_press(self):
        self.rms6_button_control.value = 1

    def rms6_button_release(self):
        self.rms6_button_control.value = 0
