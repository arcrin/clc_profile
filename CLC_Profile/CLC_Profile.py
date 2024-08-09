import time

from framework.components.profile import Profile
from .CLC_Jig import CLC_Jig
from .test_firmware.firmwareutil.resourceshell.py.CANResource import CANFrame
from .Common_Test_Cases import CommonTestCases
from .RMS6_Test_Cases import RMS6TestCases
from .GSM8_Test_Cases import GSM8TestCases
from framework.components.test_case import TestCase
from test_jig_util.TestResult import TestResult
from time import sleep
from collections import OrderedDict
from test_jig_util.evaluation import is_truthy_bool, retry_func, in_range_list
from interface.jflash import GetModuleInfo
from interface.OpenOCD.OpenOCD import OpenOCD
from test_jig_util.trace import format_exc_plus
from test_jig_util.TCScheduler import TCScheduler
from pyDAQ.DAQ import DAQ
import threading
import logging
import yaml
import os
import sys
import serial

OOCD_DEBUG = True

LOAD_TEST_SHELL_EVENT = threading.Event()

def ordered_load(stream, Loader=yaml.SafeLoader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


class CLC_Profile(Profile):
    mongo_client_name = "mongodb://QA-TestMongo:27017"
    mongo_database_name = "TestMFG"
    mongo_collection_name = "TestRecords3"
    Description = "CLC Profile"

    CLCRMS6_PN = 325056
    CLCRM6_PN = 325054
    CLCGSM8_PN = 325057
    CLCDIM4_PN = 325055

    supported_product_numbers = {
        CLCRMS6_PN: {'full_sn': True},
        CLCRM6_PN: {'full_sn': True},
        CLCGSM8_PN: {'full_sn': True, "skip": [351011]},
        CLCDIM4_PN: {'full_sn': True}
    }

    jig: CLC_Jig = None

    FIRMWARE = None
    cwd = os.path.dirname(os.path.abspath(__file__))
    expected_measurement = ordered_load(open(cwd + r'\expected_measurement.yaml', 'r'), yaml.SafeLoader)

    def __init__(self, dut, jig, prompt_function=None):
        super(CLC_Profile, self).__init__(dut)
        self.dut = dut
        CLC_Profile.jig = jig
        CLC_Profile.Profile_Info['daq'] = jig.daq1
        self.test_case_scheduler = TCScheduler(self, log_level=logging.DEBUG)

        self.clean_up_script = TestCase("CleanUp",
                                        description="Power down dut, exit OpenOCD",
                                        verify_function=lambda x: x,
                                        function=self.test_suit_clean_up)

        CommonTestCases(self)
        if self.dut.ProductNumber == CLC_Profile.CLCRMS6_PN:
            RMS6TestCases(self)
            CLC_Profile.FIRMWARE = "RM_V1.1(Build3.66)"
        elif self.dut.ProductNumber == CLC_Profile.CLCGSM8_PN:
            GSM8TestCases(self)
            CLC_Profile.FIRMWARE = "GS_V1.1(Build3.98)"


    @classmethod
    def profile_clean_up(cls):
        # TODO: need to find a way to clean up when reloading the profile without initializing a profile instance
        if cls.jig.oocd is not None:
            try:
                cls.jig.oocd.__exit__(*sys.exc_info())
            except:
                pass
            finally:
                cls.jig.oocd = None

        OpenOCD.disconnect(0, kill_existing=True)

        cls.jig.daq1.close()
        cls.jig.daq2.close()



    def startup(self):
        self.jig.dut_power_on()
        sleep(0.5)
        LOAD_TEST_SHELL_EVENT.clear()
        return True

    def start_test_case_scheduler(self):
        self.test_case_scheduler.Start()
        return True

    def preliminary_voltage_rails(self, *args, **kwargs):
        if 'voltage_rails' not in kwargs:
            return TestResult(False, "Preliminary Voltage Rails", "", "", "No voltage rails to measure")
        result = TestResult()
        if self.dut.ProductNumber == CLC_Profile.CLCRMS6_PN:
            expected_ranges = CLC_Profile.expected_measurement['Rails']['RMS6']
        elif self.dut.ProductNumber == CLC_Profile.CLCGSM8_PN:
            expected_ranges = CLC_Profile.expected_measurement['Rails']['GSM8']
        for rail_name, test_point in kwargs['voltage_rails'].items():
            result += in_range_list(test_point.value, expected_ranges[rail_name], rail_name)
        return result

    def rms6_jumper_reading(self):
        result = TestResult()
        expected_ranges = CLC_Profile.expected_measurement['Jumper']['RMS6']
        for jumper_label, test_point in self.jig.rms6_switch_power_rails.items():
            result += in_range_list(test_point.value, expected_ranges, jumper_label)
        return result

    def start_oocd(self):
        self.jig.dut_power_cycle()
        if self.jig.oocd:
            return True

        mcu_info = GetModuleInfo('CLC')

        result = TestResult()
        result.Start("Start OpenOCD", "")

        kw = {"extra_args": ("-d3",)} if OOCD_DEBUG else {}
        log_level = 9 if OOCD_DEBUG else logging.INFO

        self.jig.oocd = OpenOCD("stm32f1x_no_working_area.cfg",
                                "swd",
                                 port=0,
                                 device=mcu_info['MCU'],
                                 info=mcu_info,
                                 verify_id=False,
                                 speed=2000,
                                 log_level=logging.DEBUG,
                                 ft12=False,
                                 kill_existing=True,
                                 **kw)

        try:
            self.jig.oocd.__enter__()
            result.Finish(True, "",  "")
        except:
            result.Finish(False, self.jig._oocd.get_log(), format_exc_plus())
            self.jig._oocd = None

        return result

    def stop_oocd(self):
        if self.jig.oocd is not None:
            try:
                self.jig.oocd.__exit__(*sys.exc_info())
            except:
                pass
            finally:
                self.jig.oocd = None
        OpenOCD.disconnect(0, kill_existing=True)
        return True

    def load_test_shell(self):
        restarts = 0

        test_firmware_path = os.path.join(os.path.dirname(__file__), "test_firmware\\CLC_STM32F103xB.hex").replace("\\", "/")

        result = TestResult()

        chipid = self.jig.oocd.chipID()
        chipid = "0x%032X" % chipid if chipid else False  # mongo cant handle large number
        result += TestResult(True if chipid else False, "ChipID", 0, chipid,
                             f"MCU ID: {chipid if chipid else 'Could not read MCU ID'}")
        if result.is_fail():
            return result

        first_load = True

        @retry_func(2, on_exception=lambda: time.sleep(0.5))
        def load_test_firmware():
            nonlocal first_load

            def wait_shell(duration: float=2):
                end = time.time() + duration
                while 1:
                    if self.jig.test_shell.ser.read_all():
                        break
                    if time.time() > end:
                        break

            result.Start("Load Test Shell", "")
            self.jig.test_shell.ser.read_all()
            self.jig.oocd.load_ram_image(test_firmware_path)

            # TODO: Wait until the test shell is running, the following line will throw an exception if it is not responsive
            # self.jig.test_shell.query("system config", retries=3, timeout=0.1)

        try:
            load_test_firmware()
            result.Finish(True, "", f"Retries: {restarts}")
        except:
            result.Finish(False, self.jig.oocd.get_log(), format_exc_plus())
            return result

        self.jig.oocd.memprog_init(0x20004C00)

        LOAD_TEST_SHELL_EVENT.set()
        self.jig.led_red.configure()
        self.jig.led_green.configure()
        self.jig.led_sys_red.configure()
        self.jig.led_sys_green.configure()
        self.jig.led_can_err.configure()
        self.jig.led_red.value = False
        self.jig.led_green.value = False
        self.jig.led_sys_red.value = False
        self.jig.led_sys_green.value = False
        self.jig.led_can_err.value = False

        return result

    def connector_detection(self, **kwargs):
        try:
            connectors_probes = kwargs["connectors_probes"]
        except KeyError:
            return TestResult(False, "Connector Detection", "", "", "Connector probe information missing")
        result = TestResult()
        for connector_position, test_point in connectors_probes.items():
            result += TestResult(
                test_point.value,
                connector_position,
                "Connector Present",
                "Connector Present" if test_point.value else "Connector Missing",
                ""
            )
            if result.is_fail():
                break
        return result

    def button_press_check(self, **kwargs):
        LOAD_TEST_SHELL_EVENT.wait()
        try:
            button_press_detection = kwargs["button_press_detection"]
        except KeyError:
            return TestResult(False, "Button Press Check", "", "", "Button press detection missing")
        result = TestResult()
        self.jig.rms6_button_press()
        self.jig.gsm8_button_press()
        sleep(0.5)
        for button_name, test_firmware_resource in button_press_detection.items():
            result += TestResult(
                test_firmware_resource.value,
                button_name,
                "Button Pressed",
                "Button Pressed" if test_firmware_resource.value else "Button Not Pressed",
                ""
            )
            if result.is_fail():
                break
        self.jig.rms6_button_release()
        self.jig.gsm8_button_release()
        sleep(0.1)
        return result

    def relay_control(self):
        LOAD_TEST_SHELL_EVENT.wait()
        result = TestResult()
        for relay_control_label, (test_firmware_resource, uio_reading) in self.jig.rms6_relay_control.items():
            test_firmware_resource.configure()
            print(f"{relay_control_label} CLEAR")
            test_firmware_resource.value = 0
            result += TestResult(
                not uio_reading.value,
                relay_control_label,
                "CLEAR",
                "CLEAR" if not uio_reading.value else "SET",
                ""
            )
            print(f"{relay_control_label} SET")
            test_firmware_resource.value = 1
            result += TestResult(
                uio_reading.value,
                relay_control_label,
                "SET",
                "SET" if uio_reading.value else "CLEAR",
                ""
            )

            if result.is_fail():
                break
        return result

    def program_flash(self):
        LOAD_TEST_SHELL_EVENT.wait()
        try:
            flash_firmware = os.path.join(os.path.dirname(__file__), f"firmware\\{CLC_Profile.FIRMWARE}.hex").replace("\\", "/")
            # flash_firmware = os.path.join(os.path.dirname(__file__), "build\\clc_led_toggle.hex").replace("\\", "/")

            self.jig.oocd.memprog_submit(0, 0, 60)
            self.jig.oocd.memprog_wait_command(0)

            print("Program FLASH")
            resp = self.jig.oocd.memprog_program_async(flash_firmware, 60000, 0, do_erase=False, alignment={0: 2})
            result = TestResult(True, "Program MCU", CLC_Profile.FIRMWARE, CLC_Profile.FIRMWARE, resp)
            return result
        except:
            raise

    @retry_func(3)
    def read_address(self):
        LOAD_TEST_SHELL_EVENT.wait()

        result = TestResult()
        for address_pin_label, address_pin_resource in self.jig.rms6_address_test_firmware_resources.items():
            address_pin_resource.configure()
            self.jig.led_red.value = False
            self.jig.led_green.value = False
            result += TestResult(address_pin_resource.value == self.expected_measurement["Address"][address_pin_label],
                                 address_pin_label,
                                 f"{address_pin_label} {'High' if self.expected_measurement['Address'][address_pin_label] else 'Low'}",
                                 f"{address_pin_label} {'High' if address_pin_resource.value else 'Low'}",
                                 "")
        return result

    @retry_func(5)
    def relay_feedback(self):
        LOAD_TEST_SHELL_EVENT.wait()
        result = TestResult()
        for relay_feedback_label, relay_feedback_resource in self.jig.rms6_relay_feedback.items():
            relay_feedback_resource.configure()
            result += in_range_list(relay_feedback_resource.value, [2.0, 3.0], relay_feedback_label)
            if result.is_fail():
                break
        return result

    @retry_func(3)
    def switch_control_feedback(self):
        LOAD_TEST_SHELL_EVENT.wait()
        result = TestResult()
        self.jig.rms6_switch_on_control.value = 0
        self.jig.rms6_switch_off_control.value = 0
        sleep(0.1)
        for switch_control_label, switch_control_reading_resource in self.jig.rms6_switch_control_feedback.items():
            switch_control_reading_resource.configure()
            result += TestResult(
                switch_control_reading_resource.value == False,
                switch_control_label,
                "Switch Off",
                "Switch On" if switch_control_reading_resource.value else "Switch Off",
                ""
            )
            if result.is_fail():
                return result

        self.jig.rms6_switch_on_control.value = 1
        self.jig.rms6_switch_off_control.value = 1
        sleep(0.1)
        for switch_control_label, switch_control_reading_resource in self.jig.rms6_switch_control_feedback.items():
            result += TestResult(
                switch_control_reading_resource.value == True,
                switch_control_label,
                "Switch On",
                "Switch On" if switch_control_reading_resource.value else "Switch Off",
                ""
            )
            if result.is_fail():
                return result
        return  result

    def can_termination_test(self):
        result = TestResult()
        self.jig.can_termination_test_control.value = 0
        sleep(0.1)
        pre_additional_resistance_measurement = self.jig.can_h_measurement.value
        result += TestResult(True, "Before adding resistance", "", pre_additional_resistance_measurement, "")
        self.jig.can_termination_test_control.value = 1
        sleep(0.1)
        post_additional_resistance_measurement = self.jig.can_h_measurement.value
        result += TestResult(True, "After adding resistance", "", post_additional_resistance_measurement, "")
        return result

    def can(self):
        LOAD_TEST_SHELL_EVENT.wait()
        result = TestResult()
        for frame in (CANFrame(self.jig.can_id, b'\x55\xFF\xAB\x5C\xC5\xD3\xFF\x55'),
                      CANFrame(self.jig.can_id, b'\x34\x23\xDF\x3E\xE3\xC2\x2C\x22')):
            self.jig.rms6_can_bus_resource.flush()
            self.jig.rms6_can_bus_resource.write(frame)
            sleep(0.1)
            resp = self.jig.daq2_can.read()
            res = resp is not None and resp.can_id == frame.can_id and resp.data == frame.data
            result += TestResult(res, f"DUT->DAQ", frame, resp,
                                 "Correct response" if res else "Incorrect response")
            if result.is_fail():
                return result

            # self.jig.rms6_can_bus_resource.flush()
            # self.jig.daq2_can.write(frame)
            # sleep(0.1)
            # resp = self.jig.rms6_can_bus_resource.read()
            # res = resp is not None and resp.can_id == frame.can_id and resp.data == frame.data
            # result += TestResult(res, f"DAQ->DUT", frame, resp,
            #                      "Correct response" if res else "Incorrect response")
            # if result.is_fail():
            #     return result
        return result

    def _test_relay_led(self, led_label: str, relay_switch_leds: dict):
        result = TestResult()
        # Red
        relay_switch_leds[led_label][0].configure()
        relay_switch_leds[led_label][0].value = True
        self.jig.led_red.value = True
        sleep(0.3)
        result += TestResult(True, f"{led_label} RED", "",  relay_switch_leds[led_label][1].value, "")
        self.jig.led_red.value = False
        relay_switch_leds[led_label][0].value = False

        # Green
        self.jig.led_green.value = True
        relay_switch_leds[led_label][0].value = True
        sleep(0.3)
        result += TestResult(True, f"{led_label} GREEN", "",  relay_switch_leds[led_label][1].value, "")
        return result

    def _test_system_led(self, sys_led_sensor):
        result = TestResult()
        self.jig.led_sys_red.value = True
        sleep(0.3)
        result += TestResult(True, "SYS RED", "", sys_led_sensor.value, "")
        self.jig.led_sys_red.value = False
        self.jig.led_sys_green.value = True
        sleep(0.3)
        result += TestResult(True, "SYS GREEN", "", sys_led_sensor.value, "")
        return result

    def can_led(self, *args, **kwargs):
        try:
            can_led_sensor = kwargs["can_led_sensor"]
        except KeyError:
            return TestResult(False, "CAN LED", "", "", "No CAN LED sensor to measure")
        result = TestResult()
        # Red
        self.jig.led_can_err.value = True
        sleep(0.5)
        result += TestResult(True, "CAN RED", "", can_led_sensor.value, "")
        self.jig.led_can_err.value = False
        # Green
        with self.jig.rms6_can_bus_resource.test(CANFrame(int(0), b'\x00\x00\x00\x00'), timeout=1.0):
            sleep(0.5)
            result += TestResult(True, "CAN GREEN", "", can_led_sensor.value, "")
        return result

    def led_test(self, *args, **kwargs):
        if not kwargs["relay_switch_leds"]:
            return TestResult(False, "LED Test", "", "", "Missing Relay/Switch LED Sensors")
        if not kwargs["sys_led_sensor"]:
            return TestResult(False, "LED Test", "", "", "Missing System LED Sensor")

        relay_switch_leds = kwargs["relay_switch_leds"]
        sys_led_sensor = kwargs["sys_led_sensor"]
        result = TestResult()
        for led_label in relay_switch_leds.keys():
            result += self._test_relay_led(led_label, relay_switch_leds)
            if result.is_fail():
                return result
        result += self._test_system_led(sys_led_sensor)
        if result.is_fail():
            return result
        return result

    def spi_test(self, **kwargs):
        try:
            sn = kwargs["sn"]
        except KeyError:
            return TestResult(False, "SPI Test", "", "", "Missing SN")
        sn = int(sn)
        sn_in_bytes = sn.to_bytes(4, byteorder='big')
        sn_write_instruction = b'\x02\x00\x00' + sn_in_bytes
        # Enable write instruction
        self.jig.gsm8_spi.transfer(b'\x06')
        # Send sn through SPI
        self.jig.gsm8_spi.transfer(sn_write_instruction)
        # Read back sn
        resp = self.jig.gsm8_spi.transfer(b'\x03\x00\x00\x00\x00\x00\x00')
        sn_read_back = int.from_bytes(resp[3:], byteorder='big')

        return TestResult(
            sn == sn_read_back,
            "SPI Test",
            f"SN sent: {sn}",
            f"SN read back: {sn_read_back}",
            "Correct response" if sn == sn_read_back else "Incorrect response"
        )


    def gsm8_jumper_reading(self):
        result = TestResult()
        expected_ranges = CLC_Profile.expected_measurement['Jumper']['GSM8']
        for jumper_label, test_point in self.jig.gsm8_jumper_measurement.items():
            result += in_range_list(test_point.value, expected_ranges, jumper_label)
        return result


    def gsm8_sw_pilot(self):
        result = TestResult()
        for sw_pilot_label, test_point in self.jig.gsm8_pilot_voltage_measurement.items():
            result += in_range_list(test_point.value, [15, 25], sw_pilot_label)
        return result

    @retry_func(3)
    def gsm8_sw_feedback(self):
        result = TestResult()
        for sw_label, sw_on_feedback in self.jig.gsm8_switch_on_feedback.items():
            sw_on_feedback.configure()
            result += in_range_list(sw_on_feedback.value, [3.0, 3.4], sw_label)
        for sw_label, sw_off_feedback in self.jig.gsm8_switch_off_feedback.items():
            result += TestResult(not sw_off_feedback.value, sw_label, "Negative Feedback", "Negative Feedback" if not sw_off_feedback.value else "Positive Feedback", "")

        for sw_label, simulation in self.jig.gsm8_switch_off_simulation.items():
            simulation.value = 1

        sleep(1)
        for sw_label, sw_on_feedback in self.jig.gsm8_switch_on_feedback.items():
            sw_on_feedback.configure()
            result += in_range_list(sw_on_feedback.value, [0.0, 0.5], sw_label)
        for sw_label, sw_off_feedback in self.jig.gsm8_switch_off_feedback.items():
            result += TestResult(sw_off_feedback.value, sw_label, "Positive Feedback", "Positive Feedback" if sw_off_feedback.value else "Negative Feedback", "")

        for sw_label, simulation in self.jig.gsm8_switch_off_simulation.items():
            simulation.value = 0

        return result


    def test_suit_clean_up(self):
        self.stop_oocd()
        try:
            self.jig.dut_power_off()
        except:
            pass
        self.test_case_scheduler.Finish()