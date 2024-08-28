from framework.components.front_panel.front_panel import FrontPanel
from framework.components.test_jig import TestJig
from pyDAQ.UniversalIO import UniversalIO, I2C, DAQ
from pyDAQ.UART import DAQ_UART
from pyDAQ.CAN import CAN
from pyDAQ.Sensors import TCS3472
from pyDAQ.Expanders import PCA9535A_GPIO, TCA9546A_I2C
from .test_firmware.firmwareutil.resourceshell.py.GPIOResource import GPIOResource
from .test_firmware.firmwareutil.resourceshell.py.ADCResource import ADCResource
from .test_firmware.firmwareutil.resourceshell.py.CANResource import CANResource
from .test_firmware.firmwareutil.resourceshell.py.SPIResource import SPIResource
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

        top_board_i2c = I2C(self.daq2, "EXP6", frequency=100000)

        kw = {"extra_args": ("-d-3",)}
        self._oocd = None

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
        self.rms6_preliminary_voltage_rails = {
            "3V3": self.daq2.IO1,
            "5V0": self.daq2.IO2,
            "PWR_PASS_THROUGH": self.daq2.AI17,
        }

        self.rms6_switch_power_rails = {
            "SW1_PWR": self.daq2.AI18,  # 18V ~ 23V
            "SW2_PWR": self.daq2.AI19,
            "SW3_PWR": self.daq2.AI20,
            "SW4_PWR": self.daq2.AI21,
            "SW5_PWR": self.daq2.AI22,
            "SW6_PWR": self.daq2.AI23
        }

        self.rms6_nreverse_jumper = GPIOResource(self.test_shell, "RMS6_nREVERSE_JUMPER")

        self.gsm8_preliminary_voltage_rails = {
            "3V3": self.daq1.AI19,
            "5V0": self.daq1.AI20,
            "PWR_OUT": self.daq1.AI18,
            "NET_PWR_OUT": self.daq1.AI17
        }

        self.gsm8_net_power_switch_control = self.daq1.EXP8.create_gpio0(mode="op", default=0)

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

        self.gsm8_connector_probes = {
            "IP1 Connector": tp46,
            "IP4 Connector": tp45,
            "IP6 Connector": tp39,
            "IP8 Connector": tp40,
            "OUT RJ45 Connector": tp31,
            "IN RJ45 Connector": tp43,
            "P1 Connector": tp44,
            "P902 Connector": tp35,
            "P903 Connector": tp41
        }

        self.rms6_connector_probes = {
            "RLY1_2 Connector": tp33,
            "RLY3_4 Connector": tp34,
            "RLY5_6 Connector": tp37,
            "SW1 Connector": tp38,
            "WS6 Connector": tp42,
            "P903 Connector": tp36,
            "P902 Connector": tp32,
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

        self.rms6_can_led_sensor = TCS3472(rms6_led_u1)
        self.rms6_sys_led_sensor = TCS3472(rms6_led_u2)

        self.rms6_relay_leds = {
            "LED_SW1": (GPIOResource(self.test_shell, "LED_SW1"), TCS3472(rms6_led_u4)),
            "LED_SW2": (GPIOResource(self.test_shell, "LED_SW2"), TCS3472(rms6_led_u3)),
            "LED_SW3": (GPIOResource(self.test_shell, "LED_SW3"), TCS3472(rms6_led_u7)),
            "LED_SW4": (GPIOResource(self.test_shell, "LED_SW4"), TCS3472(rms6_led_u8)),
            "LED_SW5": (GPIOResource(self.test_shell, "LED_SW5"), TCS3472(rms6_led_u10)),
            "LED_SW6": (GPIOResource(self.test_shell, "LED_SW6"), TCS3472(rms6_led_u11)),
        }

        self.led_green = GPIOResource(self.test_shell, "LED_GREEN")
        self.led_red = GPIOResource(self.test_shell, "LED_RED")
        self.led_sys_green = GPIOResource(self.test_shell, "LED_SYS_GREEN")
        self.led_sys_red = GPIOResource(self.test_shell, "LED_SYS_RED")
        self.led_can_err = GPIOResource(self.test_shell, "LED_CAN_ERR")

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

        self.gsm8_switch_leds = {
            "LED_SW1": (GPIOResource(self.test_shell, "LED_SW1"), TCS3472(gsm8_led_u17)),
            "LED_SW2": (GPIOResource(self.test_shell, "LED_SW2"), TCS3472(gsm8_led_u18)),
            "LED_SW3": (GPIOResource(self.test_shell, "LED_SW3"), TCS3472(gsm8_led_u20)),
            "LED_SW4": (GPIOResource(self.test_shell, "LED_SW4"), TCS3472(gsm8_led_u21)),
            "LED_SW5": (GPIOResource(self.test_shell, "LED_SW5"), TCS3472(gsm8_led_u12)),
            "LED_SW6": (GPIOResource(self.test_shell, "LED_SW6"), TCS3472(gsm8_led_u13)),
            "LED_SW7": (GPIOResource(self.test_shell, "LED_SW7"), TCS3472(gsm8_led_u14)),
            "LED_SW8": (GPIOResource(self.test_shell, "LED_SW8"), TCS3472(gsm8_led_u15)),
        }

        self.gsm8_can_led_sensor = TCS3472(gsm8_led_u23)
        self.gsm8_sys_led_sensor = TCS3472(gsm8_led_u22)
        self.gsm8_pwr_in_led_sensor = TCS3472(gsm8_led_u25) # at the bottom of the product
        self.gsm8_pwr_in_led_sensor = TCS3472(gsm8_led_u26) # at the top of the product

        """
            Buttons
        """
        self.rms6_button_press_detection = {
            "SW311": GPIOResource(self.test_shell, "RLAY_PB1"),
            "SW301": GPIOResource(self.test_shell, "RLYB_PB1"),
            "SW312": GPIOResource(self.test_shell, "RLYA_PB2"),
            "SW302": GPIOResource(self.test_shell, "RLYB_PB2"),
            "SW313": GPIOResource(self.test_shell, "RLYA_PB3"),
            "SW303": GPIOResource(self.test_shell, "RLYB_PB3"),
        }

        self.gsm8_button_press_detection = {
            "SW501": GPIOResource(self.test_shell, "RLAY_PB1"),
            "SW601": GPIOResource(self.test_shell, "RLYB_PB1"),
            "SW502": GPIOResource(self.test_shell, "RLYA_PB2"),
            "SW602": GPIOResource(self.test_shell, "RLYB_PB2"),
            "SW503": GPIOResource(self.test_shell, "RLYA_PB3"),
            "SW603": GPIOResource(self.test_shell, "RLYB_PB3"),
            "SW504": GPIOResource(self.test_shell, "RLYA_PB4"),
            "SW604": GPIOResource(self.test_shell, "RLYB_PB4"),
        }



        """
            Relay
        """
        wiring_board_gpio_20_expander_i2c = I2C(self.daq2, "EXP5", frequency=100000)
        self.rms6_relay_control = {
            "RELAY1_OFF_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYA_OFF1"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 0)),
            "RELAY1_ON_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYA_ON1"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 1)),
            "RELAY2_OFF_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYB_OFF1"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 2)),
            "RELAY2_ON_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYB_ON1"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 3)),
            "RELAY3_OFF_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYA_OFF2"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 4)),
            "RELAY3_ON_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYA_ON2"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 5)),
            "RELAY4_OFF_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYB_OFF2"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 6)),
            "RELAY4_ON_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYB_ON2"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 7)),
            "RELAY5_OFF_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYA_OFF3"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 8)),
            "RELAY5_ON_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYA_ON3"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 9)),
            "RELAY6_OFF_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYB_OFF3"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 10)),
            "RELAY6_ON_SIGNAL": (GPIOResource(self.test_shell, "RMS6_RLYB_ON3"), PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 11)),
        }

        """
            Switch
        """
        self.rms6_switch_on_control = PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 12, mode="op")
        self.rms6_switch_off_control = PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 13, mode="op")

        self.rms6_switch_control_feedback = {
            "SW1_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWA_ON1"),
            "SW1_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWA_OFF1"),
            "SW2_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWB_ON1"),
            "SW2_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWB_OFF1"),
            "SW3_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWA_ON2"),
            "SW3_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWA_OFF2"),
            "SW4_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWB_ON2"),
            "SW4_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWB_OFF2"),
            "SW5_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWA_ON3"),
            "SW5_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWA_OFF3"),
            "SW6_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWB_ON3"),
            "SW6_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_SWB_OFF3"),
        }

        """
            Address
        """
        self.rms6_address_test_firmware_resources = {
            "address_pin_1": GPIOResource(self.test_shell, "ADDR_1"),
            "address_pin_2": GPIOResource(self.test_shell, "ADDR_2"),
            "address_pin_3": GPIOResource(self.test_shell, "ADDR_3"),
            "address_pin_4": GPIOResource(self.test_shell, "ADDR_4"),
            "address_pin_5": GPIOResource(self.test_shell, "ADDR_5"),
            "address_pin_6": GPIOResource(self.test_shell, "ADDR_6"),
            "address_pin_7": GPIOResource(self.test_shell, "ADDR_7"),
            "address_pin_8": GPIOResource(self.test_shell, "ADDR_8"),
        }

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

        """
            Relay feedback
        """
        self.rms6_relay_feedback = {
            "RELAY1_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC04"),
            "RELAY2_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC05"),
            "RELAY3_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC06"),
            "RELAY4_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC07"),
            "RELAY5_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC10"),
            "RELAY6_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC11"),
        }

        """
            Jumper
        """
        self.rms6_jumpers = {
            "J311": self.daq2.AI24,
            "J301": self.daq2.AI25,
            "J312": self.daq2.AI26,
            "J302": self.daq2.AI27,
            "J313": self.daq2.AI28,
            "J303": self.daq2.AI29,

        }


        """
            CAN Bus
        """
        self.can_termination_test_control = PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 14, mode="op", inverted_logic=True)
        self.can_termination_test_control.value = 0
        self.dut_can_resource = CANResource(self.test_shell, "CAN")
        self.daq2_can = CAN(self.daq2)
        self._can_id = 4
        self.can_h = self.daq2.IO3
        self.can_h.mode = "ip"
        self.can_l = self.daq2.IO4
        self.can_l.mode = "ip"

        """
            SPI
        """
        self.gsm8_spi = SPIResource(self.test_shell, "EEPROM")

        """
            GSM8 Jumpers
        """
        self.gsm8_jumper_measurement = {
            "P501": self.daq1.IO9,
            "P601": self.daq1.IO10,
            "P502": self.daq1.IO11,
            "P602": self.daq1.IO12,
            "P503": self.daq1.IO13,
            "P603": self.daq1.IO14,
            "P504": self.daq1.IO15,
            "P604": self.daq1.IO16,
        }

        self.gsm8_pilot_voltage_measurement = {
            "IP1_PILOT_FEEDBACK": self.daq1.IO1,
            "IP2_PILOT_FEEDBACK": self.daq1.IO2,
            "IP3_PILOT_FEEDBACK": self.daq1.IO3,
            "IP4_PILOT_FEEDBACK": self.daq1.IO4,
            "IP5_PILOT_FEEDBACK": self.daq1.IO5,
            "IP6_PILOT_FEEDBACK": self.daq1.IO6,
            "IP7_PILOT_FEEDBACK": self.daq1.IO7,
            "IP8_PILOT_FEEDBACK": self.daq1.IO8,
        }

        self.gsm8_pilot_light_fw_control = {
            "IP1_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWA_PILOT1"),
            "IP2_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWB_PILOT1"),
            "IP3_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWA_PILOT2"),
            "IP4_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWB_PILOT2"),
            "IP5_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWA_PILOT3"),
            "IP6_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWB_PILOT3"),
            "IP7_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWA_PILOT4"),
            "IP8_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWB_PILOT4"),
        }

        """
            GSM8 Switch Feedback
        """
        self.gsm8_switch_on_feedback = {
            "IP1_ON_SIGNAL": ADCResource(self.test_shell, "ADC04"),
            "IP2_ON_SIGNAL": ADCResource(self.test_shell, "ADC05"),
            "IP3_ON_SIGNAL": ADCResource(self.test_shell, "ADC06"),
            "IP4_ON_SIGNAL": ADCResource(self.test_shell, "ADC07"),
            "IP5_ON_SIGNAL": ADCResource(self.test_shell, "ADC10"),
            "IP6_ON_SIGNAL": ADCResource(self.test_shell, "ADC11"),
            "IP7_ON_SIGNAL": ADCResource(self.test_shell, "ADC12"),
            "IP8_ON_SIGNAL": ADCResource(self.test_shell, "ADC13"),
        }

        self.gsm8_switch_off_feedback = {
            "IP1_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWA_OFF1"),
            "IP2_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWB_OFF1"),
            "IP3_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWA_OFF2"),
            "IP4_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWB_OFF2"),
            "IP5_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWA_OFF3"),
            "IP6_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWB_OFF3"),
            "IP7_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWA_OFF4"),
            "IP8_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWB_OFF4"),
        }

        wiring_board_gpio_23_expander_i2c = I2C(self.daq1, "EXP2", frequency=100000)

        self.gsm8_switch_off_simulation = {
            "sw1_on": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 0, mode="op"),
            "sw1_off": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 1, mode="op"),
            "sw2_on": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 2, mode="op"),
            "sw2_off": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 3, mode="op"),
            "sw3_on": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 4, mode="op"),
            "sw3_off": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 5, mode="op"),
            "sw4_on": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 6, mode="op"),
            "sw4_off": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 7, mode="op"),
            "sw5_on": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 8, mode="op"),
            "sw5_off": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 9, mode="op"),
            "sw6_on": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 10, mode="op"),
            "sw6_off": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 11, mode="op"),
            "sw7_on": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 12, mode="op"),
            "sw7_off": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 13, mode="op"),
            "sw8_on": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 14, mode="op"),
            "sw8_off": PCA9535A_GPIO(wiring_board_gpio_23_expander_i2c, 0x23, 15, mode="op"),
        }



    @property
    def can_id(self):
        return self._can_id

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

    def gsm8_button_press(self):
        self.gsm8_button_control.value = 1

    def gsm8_button_release(self):
        self.gsm8_button_control.value = 0
