#type ignore
from framework.components.front_panel.front_panel import FrontPanel
from pyDAQ.UniversalIO import UniversalIO, I2C, DAQ
from pyDAQ.Expanders import PCA9535A_GPIO
from enum import Enum
from time import sleep
import typing


daq_ports = DAQ.FindDAQs()

assert len(daq_ports) == 2, "Expected 2 DAQs, found {}".format(len(daq_ports))

_daqs = [UniversalIO(port=port.device) for port in daq_ports]
_a: typing.Dict[int, UniversalIO] = {int(daq.write("address")) : daq for daq in _daqs}
daq1 = _a[1]
daq2 = _a[2]
top_relay_control_expansion_port = daq2.EXP3
top_relay_board_i2c = I2C(daq2, 'EXP6', frequency=100000)


TP40 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 0, inverted_logic=True)
TP39 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 1, inverted_logic=True)
TP38 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 2, inverted_logic=True)
TP37 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 3, inverted_logic=True)
TP36 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 4, inverted_logic=True)
TP35 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 5, inverted_logic=True)
TP34 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 6, inverted_logic=True)
TP33 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 7, inverted_logic=True)
TP32 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 8, inverted_logic=True)
TP31 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 9, inverted_logic=True)
TP46 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 10, inverted_logic=True)
TP45 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 11, inverted_logic=True)
TP44 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 12, inverted_logic=True)
TP43 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 13, inverted_logic=True)
TP42 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 14, inverted_logic=True)
TP41 = PCA9535A_GPIO(top_relay_board_i2c, 0x27, 15, inverted_logic=True)


tps = {
    "GSM8_right_center_bottom_connector": TP40,
    "GSM8_right_center_top_connector": TP39,
    "RMS_right_top_connector": TP38,
    "RMS_left_bottom_connector": TP37,
    "RMS_middle_top_connector": TP36,
    "GSM8_middle_bottom_connector": TP35,
    "RMS_left_center_connector": TP34,
    "RMS_left_top_connector": TP33,
    "RMS_middle_bottom_connector": TP32,
    "GSM8_right_top_connector": TP31,
    "GSM8_left_center_connector": TP46,
    "GSM8_left_bottom_connector": TP45,
    "GSM8_left_top_connector": TP44,
    "GSM8_right_bottom_connector": TP43,
    "RMS_right_bottom_connector": TP42,
    "GSM8_middle_top_connector": TP41
}

top_relay2_control = top_relay_control_expansion_port.create_gpio1(mode="op", default=0)
top_relay1_control = top_relay_control_expansion_port.create_gpio0(mode="op", default=0)

front_panel_i2c = I2C(daq2, 'EXP8', frequency=100000)
front_panel = FrontPanel(front_panel_i2c)


def dut_power_on():
    daq2['VOUT_enable'].value = 1


def dut_power_off():
    daq2['VOUT_enable'].value = 0


def gsm8_button_press_on():
    top_relay1_control.value = 1


def gsm8_button_press_off():
    top_relay1_control.value = 0


def rms_button_press_on():
    top_relay2_control.value = 1


def rms_button_press_off():
    top_relay2_control.value = 0


def connector_probes_check():
    for key, gpio in tps.items():
        if gpio.value:
            print(f"{key}: {gpio.value}")

