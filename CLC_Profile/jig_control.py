#type ignore
from framework.components.front_panel.front_panel import FrontPanel
from pyDAQ.UniversalIO import UniversalIO, I2C, DAQ
from pyDAQ.UART import DAQ_UART
from pyDAQ.Sensors import TCS3472
from pyDAQ.Expanders import PCA9535A_GPIO, TCA9546A_I2C
from test_firmware.firmwareutil.resourceshell.py.GPIOResource import GPIOResource
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
led_rly1 = GPIOResource(test_shell, "LED_SW311")
led_rly2 = GPIOResource(test_shell, "LED_SW301")
led_rly3 = GPIOResource(test_shell, "LED_SW312")
led_rly4 = GPIOResource(test_shell, "LED_SW302")
led_rly5 = GPIOResource(test_shell, "LED_SW313")
led_rly6 = GPIOResource(test_shell, "LED_SW303")

rms6_led_u1 = TCA9546A_I2C(top_board_i2c, 0x74, 0)
rms6_led_u2 = TCA9546A_I2C(top_board_i2c, 0x74, 1)
rms6_led_u3 = TCA9546A_I2C(top_board_i2c, 0x74, 2)
rms6_led_u4 = TCA9546A_I2C(top_board_i2c, 0x74, 3)
rms6_led_u7 = TCA9546A_I2C(top_board_i2c, 0x75, 0)
rms6_led_u8 = TCA9546A_I2C(top_board_i2c, 0x75, 1)
rms6_led_u10 = TCA9546A_I2C(top_board_i2c, 0x75, 2)
rms6_led_u11 = TCA9546A_I2C(top_board_i2c, 0x75, 3)

rms6_leds = {
    "CAN": TCS3472(rms6_led_u1),
    "SYS": TCS3472(rms6_led_u2),
    "RLY1": TCS3472(rms6_led_u4),
    # "RLY2": TCS3472(rms6_led_u3),
    "RLY3": TCS3472(rms6_led_u7),
    "RLY4": TCS3472(rms6_led_u8),
    "RLY5": TCS3472(rms6_led_u10),
    "RLY6": TCS3472(rms6_led_u11)
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
wiring_board_gpio_expander_i2c = I2C(daq2, "EXP5", frequency=100000)

rms6_relay_control_feedback_readings = {
    "relay1_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 0),
    "relay1_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 1),
    "relay2_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 2),
    "relay2_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 3),
    "relay3_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 4),
    "relay3_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 5),
    "relay4_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 6),
    "relay4_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 7),
    "relay5_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 8),
    "relay5_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 9),
    "relay6_off_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 10),
    "relay6_on_reading": PCA9535A_GPIO(wiring_board_gpio_expander_i2c, 0x20, 11),
}


rms6_relay_control ={
    "relay1_off_test_firmware_resource": GPIOResource(test_shell, "RLYA_OFF1"),
    "relay1_on_test_firmware_resource": GPIOResource(test_shell, "RLYA_ON1"),
    "relay2_off_test_firmware_resource": GPIOResource(test_shell, "RLYB_OFF1"),
    "relay2_on_test_firmware_resource": GPIOResource(test_shell, "RLYB_ON1"),
    "relay3_off_test_firmware_resource": GPIOResource(test_shell, "RLYA_OFF2"),
    "relay3_on_test_firmware_resource": GPIOResource(test_shell, "RLYA_ON2"),
    "relay4_off_test_firmware_resource": GPIOResource(test_shell, "RLYB_OFF2"),
    "relay4_on_test_firmware_resource": GPIOResource(test_shell, "RLYB_ON2"),
    "relay5_off_test_firmware_resource": GPIOResource(test_shell, "RLYA_OFF3"),
    "relay5_on_test_firmware_resource": GPIOResource(test_shell, "RLYA_ON3"),
    "relay6_off_test_firmware_resource": GPIOResource(test_shell, "RLYB_OFF3"),
    "relay6_on_test_firmware_resource": GPIOResource(test_shell, "RLYB_ON3"),
}

address_pin_1 = GPIOResource(test_shell, "ADDR_01")
address_pin_2 = GPIOResource(test_shell, "ADDR_02")
address_pin_4 = GPIOResource(test_shell, "ADDR_04")
address_pin_8 = GPIOResource(test_shell, "ADDR_08")
address_pin_11 = GPIOResource(test_shell, "ADDR_11")
address_pin_12 = GPIOResource(test_shell, "ADDR_12")
address_pin_14 = GPIOResource(test_shell, "ADDR_14")
address_pin_18 = GPIOResource(test_shell, "ADDR_18")

rms6_address_reading = {
    "address_pin_1": address_pin_1,
    "address_pin_2": address_pin_2,
    "address_pin_3": address_pin_4,
    "address_pin_4": address_pin_8,
    "address_pin_5": address_pin_11,
    "address_pin_6": address_pin_12,
    "address_pin_7": address_pin_14,
    "address_pin_8": address_pin_18,
}


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
    for resource_name, resource in rms6_address_reading.items():
        print(f"{resource_name}: {resource.value}")



sleep(0.1)
front_panel.engage_mounting_plate()
sleep(2)
dut_power_on()
# sleep(0.5)
# start_oocd()
# sleep(0.2)
# load_test_shell()
# sleep(0.2)


