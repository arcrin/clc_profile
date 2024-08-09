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
            "PWR_OUT": self.daq2.AI17,
        }

        self.rms6_switch_power_rails = {
            "SW1_PWR": self.daq2.AI18,  # 18V ~ 23V
            "SW2_PWR": self.daq2.AI19,
            "SW3_PWR": self.daq2.AI20,
            "SW4_PWR": self.daq2.AI21,
            "SW5_PWR": self.daq2.AI22,
            "SW6_PWR": self.daq2.AI23
        }

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

        self.rms6_can_led_sensor = TCS3472(rms6_led_u1)
        self.rms6_sys_led_sensor = TCS3472(rms6_led_u2)

        self.rms6_relay_leds = {
            "LED_RLY1": (GPIOResource(self.test_shell, "LED_RLY1"), TCS3472(rms6_led_u4)),
            # "LED_RLY2": (GPIOResource(self.test_shell, "LED_RLY2"), TCS3472(rms6_led_u3)),
            "LED_RLY3": (GPIOResource(self.test_shell, "LED_RLY3"), TCS3472(rms6_led_u7)),
            "LED_RLY4": (GPIOResource(self.test_shell, "LED_RLY4"), TCS3472(rms6_led_u8)),
            "LED_RLY5": (GPIOResource(self.test_shell, "LED_RLY5"), TCS3472(rms6_led_u10)),
            "LED_RLY6": (GPIOResource(self.test_shell, "LED_RLY6"), TCS3472(rms6_led_u11)),
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
            "LED_SW1": (GPIOResource(self.test_shell, "LED_RLY1"), TCS3472(gsm8_led_u17)),
            "LED_SW2": (GPIOResource(self.test_shell, "LED_RLY2"), TCS3472(gsm8_led_u18)),
            "LED_SW3": (GPIOResource(self.test_shell, "LED_RLY3"), TCS3472(gsm8_led_u20)),
            # "LED_SW4": (GPIOResource(self.test_shell, "LED_RLY4"), TCS3472(gsm8_led_u21)),
            "LED_SW5": (GPIOResource(self.test_shell, "LED_RLY5"), TCS3472(gsm8_led_u12)),
            "LED_SW6": (GPIOResource(self.test_shell, "LED_RLY6"), TCS3472(gsm8_led_u13)),
            "LED_SW7": (GPIOResource(self.test_shell, "LED_RLY7"), TCS3472(gsm8_led_u14)),
            "LED_SW8": (GPIOResource(self.test_shell, "LED_RLY8"), TCS3472(gsm8_led_u15)),
        }

        self.gsm8_can_led_sensor = TCS3472(gsm8_led_u23)
        self.gsm8_sys_led_sensor = TCS3472(gsm8_led_u22)
        self.gsm8_pwr_in_led_sensor = TCS3472(gsm8_led_u25) # at the bottom of the product
        self.gsm8_pwr_in_led_sensor = TCS3472(gsm8_led_u26) # at the top of the product


        """
            Buttons
        """
        self.rms6_button_press_detection = {
            "push_button_sw311": GPIOResource(self.test_shell, "RLAY_PB1"),
            "push_button_sw301": GPIOResource(self.test_shell, "RLYB_PB1"),
            "push_button_sw312": GPIOResource(self.test_shell, "RLYA_PB2"),
            "push_button_sw302": GPIOResource(self.test_shell, "RLYB_PB2"),
            "push_button_sw313": GPIOResource(self.test_shell, "RLYA_PB3"),
            "push_button_sw303": GPIOResource(self.test_shell, "RLYB_PB3"),
        }

        self.gsm8_button_press_detection = {
            "sw1": GPIOResource(self.test_shell, "RLAY_PB1"),
            "sw2": GPIOResource(self.test_shell, "RLYB_PB1"),
            "sw3": GPIOResource(self.test_shell, "RLYA_PB2"),
            "sw4": GPIOResource(self.test_shell, "RLYB_PB2"),
            "sw5": GPIOResource(self.test_shell, "RLYA_PB3"),
            "sw6": GPIOResource(self.test_shell, "RLYB_PB3"),
            "sw7": GPIOResource(self.test_shell, "RLYA_PB4"),
            "sw8": GPIOResource(self.test_shell, "RLYB_PB4"),
        }



        """
            Relay
        """
        wiring_board_gpio_20_expander_i2c = I2C(self.daq2, "EXP5", frequency=100000)
        self.rms6_relay_control = {
            "relay1_off": (GPIOResource(self.test_shell, "RMS6_RLYA_OFF1"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 0)),
            "relay1_on": (GPIOResource(self.test_shell, "RMS6_RLYA_ON1"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 1)),
            "relay2_off": (GPIOResource(self.test_shell, "RMS6_RLYB_OFF1"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 2)),
            "relay2_on": (GPIOResource(self.test_shell, "RMS6_RLYB_ON1"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 3)),
            "relay3_off": (GPIOResource(self.test_shell, "RMS6_RLYA_OFF2"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 4)),
            "relay3_on": (GPIOResource(self.test_shell, "RMS6_RLYA_ON2"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 5)),
            "relay4_off": (GPIOResource(self.test_shell, "RMS6_RLYB_OFF2"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 6)),
            "relay4_on": (GPIOResource(self.test_shell, "RMS6_RLYB_ON2"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 7)),
            "relay5_off": (GPIOResource(self.test_shell, "RMS6_RLYA_OFF3"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 8)),
            "relay5_on": (GPIOResource(self.test_shell, "RMS6_RLYA_ON3"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 9)),
            "relay6_off": (GPIOResource(self.test_shell, "RMS6_RLYB_OFF3"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 10)),
            "relay6_on": (GPIOResource(self.test_shell, "RMS6_RLYB_ON3"),PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 11)),
        }

        """
            Switch
        """
        self.rms6_switch_on_control = PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 12, mode="op")
        self.rms6_switch_off_control = PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 13, mode="op")

        self.rms6_switch_control_feedback = {
            "swa_on1_control" : GPIOResource(self.test_shell, "RMS6_SWA_ON1"),
            "swa_off1_control" : GPIOResource(self.test_shell, "RMS6_SWA_OFF1"),
            "swb_on1_control" : GPIOResource(self.test_shell, "RMS6_SWB_ON1"),
            "swb_off1_control" : GPIOResource(self.test_shell, "RMS6_SWB_OFF1"),
            "swa_on2_control" : GPIOResource(self.test_shell, "RMS6_SWA_ON2"),
            "swa_off2_control" : GPIOResource(self.test_shell, "RMS6_SWA_OFF2"),
            "swb_on2_control" : GPIOResource(self.test_shell, "RMS6_SWB_ON2"),
            "swb_off2_control" : GPIOResource(self.test_shell, "RMS6_SWB_OFF2"),
            "swa_on3_control" : GPIOResource(self.test_shell, "RMS6_SWA_ON3"),
            "swa_off3_control" : GPIOResource(self.test_shell, "RMS6_SWA_OFF3"),
            "swb_on3_control" : GPIOResource(self.test_shell, "RMS6_SWB_ON3"),
            "swb_off3_control" : GPIOResource(self.test_shell, "RMS6_SWB_OFF3"),
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


        """
            Relay feedback
        """
        self.rms6_relay_feedback = {
            "relay_a_feedback_1": ADCResource(self.test_shell, "ADC04"),
            "relay_b_feedback_1": ADCResource(self.test_shell, "ADC05"),
            "relay_a_feedback_2": ADCResource(self.test_shell, "ADC06"),
            "relay_b_feedback_2": ADCResource(self.test_shell, "ADC07"),
            "relay_a_feedback_3": ADCResource(self.test_shell, "ADC10"),
            "relay_b_feedback_3": ADCResource(self.test_shell, "ADC11"),
        }

        """
            Jumper
        """
        self.rms6_jumpers = {
            "jumper_1": self.daq2.AI24,
            "jumper_2": self.daq2.AI25,
            "jumper_3": self.daq2.AI26,
            "jumper_4": self.daq2.AI27,
            "jumper_5": self.daq2.AI28,
            "jumper_6": self.daq2.AI29,

        }


        """
            CAN Bus
        """
        self.can_termination_test_control = PCA9535A_GPIO(wiring_board_gpio_20_expander_i2c, 0x20, 14, mode="op", inverted_logic=True)
        self.can_termination_test_control.value = 0
        self.rms6_can_bus_resource = CANResource(self.test_shell, "CAN")
        self.daq2_can = CAN(self.daq2)
        self._can_id = 4
        self.can_h_measurement = self.daq2.IO3
        self.can_l_measurement = self.daq2.IO4

        """
            SPI
        """
        self.gsm8_spi = SPIResource(self.test_shell, "EEPROM")

        """
            GSM8 Jumpers
        """
        self.gsm8_jumper_measurement = {
            "jumper_1": self.daq1.IO9,
            "jumper_2": self.daq1.IO10,
            "jumper_3": self.daq1.IO11,
            "jumper_4": self.daq1.IO12,
            "jumper_5": self.daq1.IO13,
            "jumper_6": self.daq1.IO14,
            "jumper_7": self.daq1.IO15,
            "jumper_8": self.daq1.IO16,
        }


        """
            GSM8 Pilot light control and reading
        """
        self.gsm8_pilot_voltage_measurement = {
            "pilot_1": self.daq1.IO1,
            "pilot_2": self.daq1.IO2,
            "pilot_3": self.daq1.IO3,
            "pilot_4": self.daq1.IO4,
            "pilot_5": self.daq1.IO5,
            "pilot_6": self.daq1.IO6,
            "pilot_7": self.daq1.IO7,
            "pilot_8": self.daq1.IO8,
        }

        self.gsm8_pilot_enable = {
            "pilot_1": GPIOResource(self.test_shell, "GSM8_SWA_PILOT1"),
            "pilot_2": GPIOResource(self.test_shell, "GSM8_SWB_PILOT1"),
            "pilot_3": GPIOResource(self.test_shell, "GSM8_SWA_PILOT2"),
            "pilot_4": GPIOResource(self.test_shell, "GSM8_SWB_PILOT2"),
            "pilot_5": GPIOResource(self.test_shell, "GSM8_SWA_PILOT3"),
            "pilot_6": GPIOResource(self.test_shell, "GSM8_SWB_PILOT3"),
            "pilot_7": GPIOResource(self.test_shell, "GSM8_SWA_PILOT4"),
            "pilot_8": GPIOResource(self.test_shell, "GSM8_SWB_PILOT4"),
        }

        """
            GSM8 Switch Feedback
        """
        self.gsm8_switch_on_feedback = {
            "sw1_on_feedback": ADCResource(self.test_shell, "ADC04"),
            "sw2_on_feedback": ADCResource(self.test_shell, "ADC05"),
            "sw3_on_feedback": ADCResource(self.test_shell, "ADC06"),
            "sw4_on_feedback": ADCResource(self.test_shell, "ADC07"),
            "sw5_on_feedback": ADCResource(self.test_shell, "ADC10"),
            "sw6_on_feedback": ADCResource(self.test_shell, "ADC11"),
            "sw7_on_feedback": ADCResource(self.test_shell, "ADC12"),
            "sw8_on_feedback": ADCResource(self.test_shell, "ADC13"),
        }

        self.gsm8_switch_off_feedback = {
            "sw1_off_feedback": GPIOResource(self.test_shell, "GSM8_SWA_OFF1"),
            "sw2_off_feedback": GPIOResource(self.test_shell, "GSM8_SWB_OFF1"),
            "sw3_off_feedback": GPIOResource(self.test_shell, "GSM8_SWA_OFF2"),
            "sw4_off_feedback": GPIOResource(self.test_shell, "GSM8_SWB_OFF2"),
            "sw5_off_feedback": GPIOResource(self.test_shell, "GSM8_SWA_OFF3"),
            "sw6_off_feedback": GPIOResource(self.test_shell, "GSM8_SWB_OFF3"),
            "sw7_off_feedback": GPIOResource(self.test_shell, "GSM8_SWA_OFF4"),
            "sw8_off_feedback": GPIOResource(self.test_shell, "GSM8_SWB_OFF4"),
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
