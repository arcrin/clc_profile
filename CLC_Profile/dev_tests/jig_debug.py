#type ignore
from framework.components.front_panel.front_panel import FrontPanel
from pyDAQ.UniversalIO import UniversalIO, I2C, DAQ
from pyDAQ.UART import DAQ_UART
from pyDAQ.Sensors import TCS3472
from pyDAQ.Expanders import PCA9535A_GPIO, TCA9546A_I2C
from pyDAQ.CAN import CAN
from test_firmware.firmwareutil.resourceshell.py.GPIOResource import GPIOResource
from test_firmware.firmwareutil.resourceshell.py.ADCResource import ADCResource
from test_firmware.firmwareutil.resourceshell.py.CANResource import CANResource, CANFrame
from test_firmware.firmwareutil.resourceshell.py.SPIResource import SPIResource
from test_firmware.firmwareutil.resourceshell.py.UARTTestShell import UARTTestShell
from interface.OpenOCD.OpenOCD import OpenOCD
from enum import Enum
from time import sleep
import logging
import typing
import os


test_firmware_path = os.path.join(os.path.dirname(__file__), "test_firmware\\CLC_STM32F103xB.hex").replace("\\", "/")
flash_firmware = os.path.join(os.path.dirname(__file__), "build\\clc_led_toggle.hex").replace("\\", "/")

daq_ports = DAQ.FindDAQs()

assert len(daq_ports) == 2, "Expected 2 DAQs, found {}".format(len(daq_ports))

_daqs = [UniversalIO(port=port.device) for port in daq_ports]
_a: typing.Dict[int, UniversalIO] = {int(daq.write("address")): daq for daq in _daqs}
daq1 = _a[1]
daq2 = _a[2]
top_relay_control_expansion_port = daq2.EXP3
top_board_i2c = I2C(daq2, 'EXP6', frequency=100000)
kw = {"extra_args": ("-d-3",)}
oocd = OpenOCD("stm32f1x_no_working_area.cfg",
               "swd",
               port=0,
               device="STM32F103V8",
               verify_id=False,
               speed=2000,
               log_level=logging.DEBUG,
               ft12=False,
               kill_existing=True,
               # **kw
               )


TP40 = PCA9535A_GPIO(top_board_i2c, 0x27, 0, inverted_logic=True)
TP39 = PCA9535A_GPIO(top_board_i2c, 0x27, 1, inverted_logic=True)
TP38 = PCA9535A_GPIO(top_board_i2c, 0x27, 2, inverted_logic=True)
TP37 = PCA9535A_GPIO(top_board_i2c, 0x27, 3, inverted_logic=True)
TP36 = PCA9535A_GPIO(top_board_i2c, 0x27, 4, inverted_logic=True)
TP35 = PCA9535A_GPIO(top_board_i2c, 0x27, 5, inverted_logic=True)
TP34 = PCA9535A_GPIO(top_board_i2c, 0x27, 6, inverted_logic=True)
TP33 = PCA9535A_GPIO(top_board_i2c, 0x27, 7, inverted_logic=True)
TP32 = PCA9535A_GPIO(top_board_i2c, 0x27, 8, inverted_logic=True)
TP31 = PCA9535A_GPIO(top_board_i2c, 0x27, 9, inverted_logic=True)
TP46 = PCA9535A_GPIO(top_board_i2c, 0x27, 10, inverted_logic=True)
TP45 = PCA9535A_GPIO(top_board_i2c, 0x27, 11, inverted_logic=True)
TP44 = PCA9535A_GPIO(top_board_i2c, 0x27, 12, inverted_logic=True)
TP43 = PCA9535A_GPIO(top_board_i2c, 0x27, 13, inverted_logic=True)
TP42 = PCA9535A_GPIO(top_board_i2c, 0x27, 14, inverted_logic=True)
TP41 = PCA9535A_GPIO(top_board_i2c, 0x27, 15, inverted_logic=True)


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

test_shell_uart = DAQ_UART(daq2, "EXP1", baudrate=115200, timeout=1)
test_shell = UARTTestShell(test_shell_uart,
                           max_command_length=512,
                           max_response_length=2048,
                           debug=True,
                           default_retries=2)

"""
    LED 
"""

led_green = GPIOResource(test_shell, "LED_GREEN")
led_red = GPIOResource(test_shell, "LED_RED")
led_rly1_resource = GPIOResource(test_shell, "LED_RLY1")
led_rly2_resource = GPIOResource(test_shell, "LED_RLY2")
led_rly3_resource = GPIOResource(test_shell, "LED_RLY3")
led_rly4_resource = GPIOResource(test_shell, "LED_RLY4")
led_rly5_resource = GPIOResource(test_shell, "LED_RLY5")
led_rly6_resource = GPIOResource(test_shell, "LED_RLY6")
led_sys_green_resource = GPIOResource(test_shell, "LED_SYS_GREEN")
led_sys_red_resource = GPIOResource(test_shell, "LED_SYS_RED")
led_can_err_resource = GPIOResource(test_shell, "LED_CAN_ERR")
led_can_rx_debug = GPIOResource(test_shell, "CAN_RX_DEBUG")
led_can_rx_ip = GPIOResource(test_shell, "CAN_RX")


rms6_led_u1 = TCA9546A_I2C(top_board_i2c, 0x74, 0)
rms6_led_u2 = TCA9546A_I2C(top_board_i2c, 0x74, 1)
rms6_led_u3 = TCA9546A_I2C(top_board_i2c, 0x74, 2)
rms6_led_u4 = TCA9546A_I2C(top_board_i2c, 0x74, 3)
rms6_led_u7 = TCA9546A_I2C(top_board_i2c, 0x75, 0)
rms6_led_u8 = TCA9546A_I2C(top_board_i2c, 0x75, 1)
rms6_led_u10 = TCA9546A_I2C(top_board_i2c, 0x75, 2)
rms6_led_u11 = TCA9546A_I2C(top_board_i2c, 0x75, 3)

rms6_can_led_sensor = TCS3472(rms6_led_u1)
rms6_sys_led_sensor = TCS3472(rms6_led_u2)
rms6_relay1_led_sensor = TCS3472(rms6_led_u4)
rms6_relay2_led_sensor = TCS3472(rms6_led_u3)
rms6_relay3_led_sensor = TCS3472(rms6_led_u7)
rms6_relay4_led_sensor = TCS3472(rms6_led_u8)
rms6_relay5_led_sensor = TCS3472(rms6_led_u10)
rms6_relay6_led_sensor = TCS3472(rms6_led_u11)

rms6_relay_leds = {
    "LED_RLY1": (led_rly1_resource, rms6_relay1_led_sensor),
    "LED_RLY2": (led_rly2_resource, rms6_relay2_led_sensor),
    "LED_RLY3": (led_rly3_resource, rms6_relay3_led_sensor),
    "LED_RLY4": (led_rly4_resource, rms6_relay4_led_sensor),
    "LED_RLY5": (led_rly5_resource, rms6_relay5_led_sensor),
    "LED_RLY6": (led_rly6_resource, rms6_relay6_led_sensor),
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

gsm8_led_sw1 = GPIOResource(test_shell, "LED_RLY1")
gsm8_led_sw2 = GPIOResource(test_shell, "LED_RLY2")
gsm8_led_sw3 = GPIOResource(test_shell, "LED_RLY3")
gsm8_led_sw4 = GPIOResource(test_shell, "LED_RLY4")
gsm8_led_sw5 = GPIOResource(test_shell, "LED_RLY5")
gsm8_led_sw6 = GPIOResource(test_shell, "LED_RLY6")
gsm8_led_sw7 = GPIOResource(test_shell, "LED_RLY7")
gsm8_led_sw8 = GPIOResource(test_shell, "LED_RLY8")

gsm8_led_sw1_sensor = TCS3472(gsm8_led_u17)
gsm8_led_sw2_sensor = TCS3472(gsm8_led_u18)
gsm8_led_sw3_sensor = TCS3472(gsm8_led_u20)
gsm8_led_sw4_sensor = TCS3472(gsm8_led_u21)
gsm8_led_sw5_sensor = TCS3472(gsm8_led_u12)
gsm8_led_sw6_sensor = TCS3472(gsm8_led_u13)
gsm8_led_sw7_sensor = TCS3472(gsm8_led_u14)
gsm8_led_sw8_sensor = TCS3472(gsm8_led_u15)

gsm8_can_led_sensor = TCS3472(gsm8_led_u23)
gsm8_sys_led_sensor = TCS3472(gsm8_led_u22)

gms8_switch_leds = {
    "LED_SW1": (gsm8_led_sw1, gsm8_led_sw1_sensor),
    "LED_SW2": (gsm8_led_sw2, gsm8_led_sw2_sensor),
    "LED_SW3": (gsm8_led_sw3, gsm8_led_sw3_sensor),
    "LED_SW4": (gsm8_led_sw4, gsm8_led_sw4_sensor),
    "LED_SW5": (gsm8_led_sw5, gsm8_led_sw5_sensor),
    "LED_SW6": (gsm8_led_sw6, gsm8_led_sw6_sensor),
    "LED_SW7": (gsm8_led_sw7, gsm8_led_sw7_sensor),
    "LED_SW8": (gsm8_led_sw8, gsm8_led_sw8_sensor),
}


"""
    Push buttons
"""
rms6_push_button_reading = {
    "push_button_sw311_test_firmware_resource": GPIOResource(test_shell, "SW311_PB"),
    "push_button_sw301_test_firmware_resource": GPIOResource(test_shell, "SW301_PB"),
    "push_button_sw312_test_firmware_resource": GPIOResource(test_shell, "SW312_PB"),
    "push_button_sw302_test_firmware_resource": GPIOResource(test_shell, "SW302_PB"),
    "push_button_sw313_test_firmware_resource": GPIOResource(test_shell, "SW313_PB"),
    "push_button_sw303_test_firmware_resource": GPIOResource(test_shell, "SW303_PB"),
}

"""
    Relay feedback
"""
rms6_relay_feedback = {
    "relay_a_feedback1":  GPIOResource(test_shell, "RLYA_FB1"),
    "relay_b_feedback1":  GPIOResource(test_shell, "RLYB_FB1"),
    "relay_a_feedback2":  GPIOResource(test_shell, "RLYA_FB2"),
    "relay_b_feedback2":  GPIOResource(test_shell, "RLYB_FB2"),
    "relay_a_feedback3":  GPIOResource(test_shell, "RLYA_FB3"),
    "relay_b_feedback3":  GPIOResource(test_shell, "RLYB_FB3"),
}

"""
    Voltage rails
"""
rms6_voltage_rails = {
    "3V3": daq2.IO1,
    "5V0": daq2.IO2,
    "PWR_OUT": daq2.AI17,
    "SW1_PWR": daq2.AI18,
    "SW2_PWR": daq2.AI19,
    "SW3_PWR": daq2.AI20,
    "SW4_PWR": daq2.AI21,
    "SW5_PWR": daq2.AI22,
    "SW6_PWR": daq2.AI23,
    "HW_FUSED": daq2.AI32
}


"""
    Relay on/off 
"""
wiring_board_gpio_expander_0x20_i2c = I2C(daq2, "EXP5", frequency=100000)

rms6_relay_control_feedback_readings = {
    "relay1_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 0),
    "relay1_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 1),
    "relay2_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 2),
    "relay2_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 3),
    "relay3_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 4),
    "relay3_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 5),
    "relay4_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 6),
    "relay4_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 7),
    "relay5_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 8),
    "relay5_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 9),
    "relay6_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 10),
    "relay6_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 11),
}


rms6_relay_control ={
    "relay1_off_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYA_OFF1"),
    "relay1_on_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYA_ON1"),
    "relay2_off_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYB_OFF1"),
    "relay2_on_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYB_ON1"),
    "relay3_off_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYA_OFF2"),
    "relay3_on_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYA_ON2"),
    "relay4_off_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYB_OFF2"),
    "relay4_on_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYB_ON2"),
    "relay5_off_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYA_OFF3"),
    "relay5_on_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYA_ON3"),
    "relay6_off_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYB_OFF3"),
    "relay6_on_test_firmware_resource": GPIOResource(test_shell, "RMS6_RLYB_ON3"),
}

# address_pin_1 = GPIOResource(test_shell, "ADDR_11")
# address_pin_2 = GPIOResource(test_shell, "ADDR_12")
# address_pin_4 = GPIOResource(test_shell, "ADDR_14")
# address_pin_8 = GPIOResource(test_shell, "ADDR_18")
# address_pin_11 = GPIOResource(test_shell, "ADDR_01")
# address_pin_12 = GPIOResource(test_shell, "ADDR_02")
# address_pin_14 = GPIOResource(test_shell, "ADDR_04")
# address_pin_18 = GPIOResource(test_shell, "ADDR_08")

rms6_address_reading = {
    "address_pin_1": GPIOResource(test_shell, "ADDR_1"),
    "address_pin_2": GPIOResource(test_shell, "ADDR_2"),
    "address_pin_3": GPIOResource(test_shell, "ADDR_3"),
    "address_pin_4": GPIOResource(test_shell, "ADDR_4"),
    "address_pin_5": GPIOResource(test_shell, "ADDR_5"),
    "address_pin_6": GPIOResource(test_shell, "ADDR_6"),
    "address_pin_7": GPIOResource(test_shell, "ADDR_7"),
    "address_pin_8": GPIOResource(test_shell, "ADDR_8"),
}

relay_a_feedback_1 = ADCResource(test_shell, "RLYA_FB1")
relay_b_feedback_1 = ADCResource(test_shell, "RLYB_FB1")
relay_a_feedback_2 = ADCResource(test_shell, "RLYA_FB2")
relay_b_feedback_2 = ADCResource(test_shell, "RLYB_FB2")
relay_a_feedback_3 = ADCResource(test_shell, "RLYA_FB3")
relay_b_feedback_3 = ADCResource(test_shell, "RLYB_FB3")

relay_feedback = {
    "relay_a_feedback_1": relay_a_feedback_1,
    "relay_b_feedback_1": relay_b_feedback_1,
    "relay_a_feedback_2": relay_a_feedback_2,
    "relay_b_feedback_2": relay_b_feedback_2,
    "relay_a_feedback_3": relay_a_feedback_3,
    "relay_b_feedback_3": relay_b_feedback_3
}

"""
    Switch
"""

rms6_switch_on_control = PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 12, mode="op")
rms6_switch_off_control = PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 13, mode="op")

swa_on1 = GPIOResource(test_shell, "SWA_ON1")
swa_off1 = GPIOResource(test_shell, "SWA_OFF1")
swb_on1 = GPIOResource(test_shell, "SWB_ON1")
swb_off1 = GPIOResource(test_shell, "SWB_OFF1")
swa_on2 = GPIOResource(test_shell, "SWA_ON2")
swa_off2 = GPIOResource(test_shell, "SWA_OFF2")
swb_on2 = GPIOResource(test_shell, "SWB_ON2")
swb_off2 = GPIOResource(test_shell, "SWB_OFF2")
swa_on3 = GPIOResource(test_shell, "SWA_ON3")
swa_off3 = GPIOResource(test_shell, "SWA_OFF3")
swb_on3 = GPIOResource(test_shell, "SWB_ON3")
swb_off3 = GPIOResource(test_shell, "SWB_OFF3")


rms6_switch_control_readings = {
    "swa_on1" : swa_on1,
    "swa_off1" : swa_off1,
    "swb_on1" : swb_on1,
    "swb_off1" : swb_off1,
    "swa_on2" : swa_on2,
    "swa_off2" : swa_off2,
    "swb_on2" : swb_on2,
    "swb_off2" : swb_off2,
    "swa_on3" : swa_on3,
    "swa_off3" : swa_off3,
    "swb_on3" : swb_on3,
    "swb_off3" : swb_off3,
}

daq_can = CAN(daq2)
sample_can_data = CANFrame(int(4), b'\x68\x65\x6c\x6c\x6f')
can_rx = GPIOResource(test_shell, "CAN_RX_DEBUG")
can_tx = GPIOResource(test_shell, "CAN_TX")
dut_can = CANResource(test_shell, "CAN")
can_termination_test_control = PCA9535A_GPIO(wiring_board_gpio_expander_0x20_i2c, 0x20, 14, mode="op")
can_h = daq2.IO3
can_l = daq2.IO4

"""
    SPI
"""
dut_spi = SPIResource(test_shell, "EEPROM")


"""
    GSM8 power switch
"""
gsm8_net_power_switch_control = daq1.EXP8.create_gpio0(mode="op", default=0)

"""
    GSM8 Jumper
"""
gsm8_jumper_measurement = {
    "jumper_1": daq1.IO9,
    "jumper_2": daq1.IO10,
    "jumper_3": daq1.IO11,
    "jumper_4": daq1.IO12,
    "jumper_5": daq1.IO13,
    "jumper_6": daq1.IO14,
    "jumper_7": daq1.IO15,
    "jumper_8": daq1.IO16,
}

"""
    GSM8 pilot
"""
gsm8_pilot_voltage_measurement = {
    "pilot_1": daq1.IO1,
    "pilot_2": daq1.IO2,
    "pilot_3": daq1.IO3,
    "pilot_4": daq1.IO4,
    "pilot_5": daq1.IO5,
    "pilot_6": daq1.IO6,
    "pilot_7": daq1.IO7,
    "pilot_8": daq1.IO8,
}

gsm8_pilot_enable = {
    "pilot_1": GPIOResource(test_shell, "GSM8_SWA_PILOT1"),
    "pilot_2": GPIOResource(test_shell, "GSM8_SWB_PILOT1"),
    "pilot_3": GPIOResource(test_shell, "GSM8_SWA_PILOT2"),
    "pilot_4": GPIOResource(test_shell, "GSM8_SWB_PILOT2"),
    "pilot_5": GPIOResource(test_shell, "GSM8_SWA_PILOT3"),
    "pilot_6": GPIOResource(test_shell, "GSM8_SWB_PILOT3"),
    "pilot_7": GPIOResource(test_shell, "GSM8_SWA_PILOT4"),
    "pilot_8": GPIOResource(test_shell, "GSM8_SWB_PILOT4"),
}


gsm8_switch_on_feedback = {
    "sw1_on_feedback": ADCResource(test_shell, "ADC04"),
    "sw2_on_feedback": ADCResource(test_shell, "ADC05"),
    "sw3_on_feedback": ADCResource(test_shell, "ADC06"),
    "sw4_on_feedback": ADCResource(test_shell, "ADC07"),
    "sw5_on_feedback": ADCResource(test_shell, "ADC10"),
    "sw6_on_feedback": ADCResource(test_shell, "ADC11"),
    "sw7_on_feedback": ADCResource(test_shell, "ADC12"),
    "sw8_on_feedback": ADCResource(test_shell, "ADC13"),
}

wiring_board_gpio_23_expander_i2c = I2C(daq1, "EXP2", frequency=100000)

gsm8_switch_feedback_simulation = {
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

gsm8_switch_off_feedback = {
    "sw1_off_feedback": GPIOResource(test_shell, "GSM8_SWA_OFF1"),
    "sw2_off_feedback": GPIOResource(test_shell, "GSM8_SWB_OFF1"),
    "sw3_off_feedback": GPIOResource(test_shell, "GSM8_SWA_OFF2"),
    "sw4_off_feedback": GPIOResource(test_shell, "GSM8_SWB_OFF2"),
    "sw5_off_feedback": GPIOResource(test_shell, "GSM8_SWA_OFF3"),
    "sw6_off_feedback": GPIOResource(test_shell, "GSM8_SWB_OFF3"),
    "sw7_off_feedback": GPIOResource(test_shell, "GSM8_SWA_OFF4"),
    "sw8_off_feedback": GPIOResource(test_shell, "GSM8_SWB_OFF4"),
}

"""
    RMS6 nREVERSE jumper
"""
rms6_nreverse_jumper = GPIOResource(test_shell, "RMS6_nREVERSE_JUMPER")


def dut_power_on():
    daq2['VOUT_enable'].value = 1


def dut_power_off():
    daq2['VOUT_enable'].value = 0


def dut_power_cycle():
    dut_power_off()
    sleep(1)
    dut_power_on()


def gsm8_button_press_on():
    top_relay1_control.value = 1


def gsm8_button_press_off():
    top_relay1_control.value = 0


def rms6_button_press():
    top_relay2_control.value = 1


def rms6_button_release():
    top_relay2_control.value = 0


def rms6_press_button_sim():
    print("Press button")
    rms6_button_press()
    sleep(0.1)
    for resource_name, resource in rms6_push_button_reading.items():
        print(f"{resource_name}: {resource.value}")

    print("Release button")
    rms6_button_release()
    sleep(0.5)
    for resource_name, resource in rms6_push_button_reading.items():
        print(f"{resource_name}: {resource.value}")


def connector_probes_check():
    for key, gpio in tps.items():
        if gpio.value:
            print(f"{key}: {gpio.value}")


def start_oocd():
    oocd.__enter__()


def exit_oocd():
    oocd.__exit__(None, None, None)


def load_test_shell():
    oocd.load_ram_image(test_firmware_path)


def measure_rms6_voltage_rails():
    for key, value in rms6_voltage_rails.items():
        print(f"{key}: {value.value}")


def read_rms6_relay_feedback():
    for key, value in rms6_relay_feedback.items():
        print(f"{key}: {value.value}")


def rms6_relay_control_sim():
    for (resource_name, resource), (test_point_name, test_point) in \
            zip(rms6_relay_control.items(), rms6_relay_control_feedback_readings.items()):
        print(f"Turn on {resource_name}")
        resource.value = 1
        sleep(0.1)
        print(f"{test_point_name}: {test_point.value}")
        print(f"Turn off {resource_name}")
        resource.value = 0
        sleep(0.1)
        print(f"{test_point_name}: {test_point.value}\n")

def address_reading():
    led_red.configure()
    led_green.configure()
    led_sys_green_resource.configure()
    led_sys_red_resource.configure()
    led_can_err_resource.configure()
    led_red.value = 0
    led_green.value = 0
    led_sys_red_resource.value = 0
    led_sys_green_resource.value = 0
    led_can_err_resource.value = 0
    for resource_name, resource in rms6_address_reading.items():
        resource.configure()
        led_red.value = 0
        led_green.value = 0
        print(f"{resource_name}: {resource.value}")

def relay_feedback_reading():
    for resource_name, resource in relay_feedback.items():
        print(f"{resource_name}: {resource.value}")


def switch_control_reading():
    for resource_name, resource in rms6_switch_control_readings.items():
        print(f"{resource_name}: {resource.value}")

def can_communication_test():
    dut_can.write(sample_can_data)

def read_can():
    return dut_can.read()

def test_relay_led_red(led_label: str):
    rms6_relay_leds[led_label][0].configure()
    rms6_relay_leds[led_label][0].value = True
    led_red.value = True
    sleep(0.3)
    print(f"{led_label} RED: {rms6_relay_leds[led_label][1].value}")

def test_relay_led_green(led_label: str):
    rms6_relay_leds[led_label][0].configure()
    rms6_relay_leds[led_label][0].value = True
    led_green.value = True
    sleep(0.3)
    print(f"{led_label} GREEN: {rms6_relay_leds[led_label][1].value}")

def turn_relay_led_off(led_label: str):
    rms6_relay_leds[led_label][0].value = False
    led_green.value = False
    led_red.value = False

def test_system_led():
    led_sys_red_resource.value = True
    sleep(0.3)
    print(f"SYS RED: {rms6_sys_led_sensor.value}")
    led_sys_red_resource.value = False
    led_sys_green_resource.value = True
    sleep(0.3)
    print(f"SYS GREEN: {rms6_sys_led_sensor.value}")
    led_sys_green_resource.value = False

def test_rms6_can_led():
    led_can_err_resource.value = True
    sleep(0.5)
    led_red_reading = []
    for i in range(100):
        led_red_reading.append(rms6_can_led_sensor.value[1])
    print(f"CAN RED: {sum(led_red_reading, start=0) / 100}")

    led_can_err_resource.value = False
    with dut_can.test(CANFrame(int(0), b'\x00\x00\x00\x00'), timeout=1.0) as can_test_async:
        sleep(0.5)
        led_greeen_readings = []
        for i in range(100):
            led_greeen_readings.append(rms6_can_led_sensor.value[2])
        print(f"CAN GREEN: {sum(led_greeen_readings, start=0) / 100}")


def test_gsm8_can_led():
    led_can_err_resource.value = True
    sleep(0.5)
    led_red_reading = []
    for i in range(100):
        led_red_reading.append(gsm8_can_led_sensor.value[1])
    print(f"CAN RED: {sum(led_red_reading, start=0) / 100}")

    led_can_err_resource.value = False
    with dut_can.test(CANFrame(int(0), b'\x00\x00\x00\x00'), timeout=1.0) as can_test_async:
        sleep(0.5)
        led_greeen_readings = []
        for i in range(100):
            led_greeen_readings.append(gsm8_can_led_sensor.value[2])
        print(f"CAN GREEN: {sum(led_greeen_readings, start=0) / 100}")


def rms6_led():
    led_rly1_resource.value = 1
    led_rly2_resource.value = 1
    led_rly3_resource.value = 1
    led_rly4_resource.value = 1
    led_rly5_resource.value = 1
    led_rly6_resource.value = 1
    sleep(0.5)
    print(f"rms6_can_led_sensor: {rms6_can_led_sensor.value}")
    print(f"rms6_sys_led_sensor: {rms6_sys_led_sensor.value}")
    print(f"rms6_relay1_led_sensor: {rms6_relay1_led_sensor.value}")
    print(f"rms6_relay2_led_sensor: {rms6_relay2_led_sensor.value}")
    print(f"rms6_relay3_led_sensor: {rms6_relay3_led_sensor.value}")
    print(f"rms6_relay4_led_sensor: {rms6_relay4_led_sensor.value}")
    print(f"rms6_relay5_led_sensor: {rms6_relay5_led_sensor.value}")
    print(f"rms6_relay6_led_sensor: {rms6_relay6_led_sensor.value}")
    sleep(0.5)
    led_rly1_resource.value = 0
    led_rly2_resource.value = 0
    led_rly3_resource.value = 0
    led_rly4_resource.value = 0
    led_rly5_resource.value = 0
    led_rly6_resource.value = 0

def gsm8_led():
    gsm8_led_sw1.value = 1
    gsm8_led_sw2.value = 1
    gsm8_led_sw3.value = 1
    gsm8_led_sw4.value = 1
    gsm8_led_sw5.value = 1
    gsm8_led_sw6.value = 1
    gsm8_led_sw7.value = 1
    gsm8_led_sw8.value = 1
    sleep(0.5)
    print(f"gsm8_led_sw1_sensor: {gsm8_led_sw1_sensor.value}")
    print(f"gsm8_led_sw2_sensor: {gsm8_led_sw2_sensor.value}")
    print(f"gsm8_led_sw3_sensor: {gsm8_led_sw3_sensor.value}")
    print(f"gsm8_led_sw4_sensor: {gsm8_led_sw4_sensor.value}")
    print(f"gsm8_led_sw5_sensor: {gsm8_led_sw5_sensor.value}")
    print(f"gsm8_led_sw6_sensor: {gsm8_led_sw6_sensor.value}")
    print(f"gsm8_led_sw7_sensor: {gsm8_led_sw7_sensor.value}")
    print(f"gsm8_led_sw8_sensor: {gsm8_led_sw8_sensor.value}")
    sleep(0.5)
    gsm8_led_sw1.value = 0
    gsm8_led_sw2.value = 0
    gsm8_led_sw3.value = 0
    gsm8_led_sw4.value = 0
    gsm8_led_sw5.value = 0
    gsm8_led_sw6.value = 0
    gsm8_led_sw7.value = 0
    gsm8_led_sw8.value = 0


def gsm8_jumper_readings():
    for jumper_label, jumper_measurement in gsm8_jumper_measurement.items():
        print(f"{jumper_label}: {jumper_measurement.value}")


def gsm8_pilot_measurement():
    for pilot_label, pilot_measurement in gsm8_pilot_voltage_measurement.items():
        print(f"{pilot_label}: {pilot_measurement.value}")


def gsm8_pilot_control(state: bool):
    for pilot_label, pilot_enable in gsm8_pilot_enable.items():
        pilot_enable.configure()
        pilot_enable.value = state
        sleep(0.1)
        print(f"{pilot_label}: {pilot_enable.value}")

def gsm8_sw_on_feedback():
    for sw_label, sw_off_feedback in gsm8_switch_on_feedback.items():
        sw_off_feedback.configure()
        print(f"{sw_label}: {sw_off_feedback.value}")

def gsm8_sw_off_feedback():
    for sw_label, sw_off_feedback in gsm8_switch_off_feedback.items():
        sw_off_feedback.configure()
        print(f"{sw_label}: {sw_off_feedback.value}")

def gsm8_sw_feedback_simulation(state: bool):
    for sw_label, sw_off in gsm8_switch_feedback_simulation.items():
        sw_off.value = 1 if state else 0

def relay5_off_control_debug():
    while True:
        print("Relay 5 off-control SET")
        rms6_relay_control['relay5_off_test_firmware_resource'].value = 1
        print(f"Relay 5 off-control feedback: {'SET' if rms6_relay_control_feedback_readings['relay5_off_reading'].value else 'CLEAR'}")
        sleep(0.5)
        print("Relay 5 off-control CLEAR")
        rms6_relay_control['relay5_off_test_firmware_resource'].value = 0
        print(f"Relay 5 off-control feedback: {'SET' if not rms6_relay_control_feedback_readings['relay5_off_reading'].value else 'CLEAR'}")
        sleep(1)



sleep(0.1)
front_panel.engage_mounting_plate()
sleep(2)
dut_power_on()
sleep(0.5)
# start_oocd()
# sleep(0.2)
# load_test_shell()
# sleep(0.2)
# led_green.value = 0
# led_red.value = 0
# led_rly1_resource.value = 0
# led_rly2_resource.value = 0
# led_rly3_resource.value = 0
# led_rly4_resource.value = 0
# led_rly5_resource.value = 0
# led_rly6_resource.value = 0
# led_sys_green_resource.value = 0
# led_sys_red_resource.value = 0
# led_can_err_resource.value = 0
# gsm8_led_sw1.value = 0
# gsm8_led_sw2.value = 0
# gsm8_led_sw3.value = 0
# gsm8_led_sw4.value = 0
# gsm8_led_sw5.value = 0
# gsm8_led_sw6.value = 0
# gsm8_led_sw7.value = 0
# gsm8_led_sw8.value = 0
# can_l.mode = "op"
# can_h.mode = "op"
# can_h.value = 3.5
# can_l.value = 1.5
# daq_can.close()
# exp7 = daq2.EXP7
# exp7p0 = exp7.create_gpio0(mode="op", default=0)
# exp7p1 = exp7.create_gpio1(mode="op", default=0)

