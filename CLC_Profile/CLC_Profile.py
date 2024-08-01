import time

from framework.components.profile import Profile
from .CLC_Jig import CLC_Jig
from framework.components.test_case import TestCase
from test_jig_util.TestResult import TestResult
from time import sleep
from collections import OrderedDict
from test_jig_util.evaluation import is_truthy_bool, retry_func, in_range_list
from interface.jflash import GetModuleInfo
from interface.OpenOCD.OpenOCD import OpenOCD
from test_jig_util.trace import format_exc_plus
from test_jig_util.TCScheduler import TCScheduler
import threading
import logging
import yaml
import os
import sys

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
        CLCGSM8_PN: {'full_sn': True},
        CLCDIM4_PN: {'full_sn': True}
    }

    jig: CLC_Jig = None

    FIRMWARE = '123456'
    cwd = os.path.dirname(os.path.abspath(__file__))
    expected_measurement = ordered_load(open(cwd + r'\expected_measurement.yaml', 'r'), yaml.SafeLoader)

    def __init__(self, dut, jig, prompt_function=None):
        super(CLC_Profile, self).__init__(dut)
        self.dut = dut
        CLC_Profile.jig = jig
        self.test_case_scheduler = TCScheduler(self, log_level=logging.DEBUG)

        self.clean_up_script = TestCase("CleanUp",
                                        description="Power down dut, exit OpenOCD",
                                        verify_function=lambda x: x,
                                        function=self.test_suit_clean_up)

        self.add_test("Startup",
                      description="Set up the test environment, such as turning on the product",
                      verify_function=lambda x: x,
                      function=self.startup
                      )

        self.add_test("Start Threads",
                        description="Start thread scheduler",
                        verify_function=lambda x: x,
                        function=self.start_test_case_scheduler
                      )

        self.add_test("Voltage Rails Measurement",
                      description="Measure the voltage rails",
                      verify_function=lambda x: x,
                      # function=self.voltage_rails_measurement,
                      real_function=self.voltage_rails_measurement,
                      function=self.test_case_scheduler.TestCaseWaiter,
                      )

        self.add_test("Start OpenOCD",
                      description="Start OpenOCD",
                      verify_function=lambda x: x,
                      function=self.start_oocd
                      )

        self.add_test("Load Test Shell",
                      description="Load the test shell",
                      verify_function=lambda x: x,
                      function=self.load_test_shell
                      )



        self.add_test("Connector Detection",
                      description="Detect the connectors",
                      verify_function=lambda x: x,
                      # function=self.connector_detection,
                      real_function=self.connector_detection,
                      function=self.test_case_scheduler.TestCaseWaiter,
                      )

        self.add_test("Button Press Check",
                      description="Check if buttons are pressed",
                      verify_function=lambda x: x,
                      # function=self.button_press_check,
                      real_function=self.button_press_check,
                      function=self.test_case_scheduler.TestCaseWaiter
                      )

        self.add_test("Relay Control",
                      description="Control the relays",
                      verify_function=lambda x: x,
                      # function=self.relay_control,
                      real_function=self.relay_control,
                      function=self.test_case_scheduler.TestCaseWaiter
                      )

        self.add_test("Program Flash",
                      description="Program the flash",
                      verify_function=lambda x: x,
                      # function=self.program_flash,
                      real_function=self.program_flash,
                      function=self.test_case_scheduler.TestCaseWaiter
                      )



    @classmethod
    def profile_clean_up(cls):
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

    def voltage_rails_measurement(self):
        result = TestResult()
        expected_ranges = CLC_Profile.expected_measurement['Rails']
        for rail_name, test_point in self.jig.rms6_voltage_rails.items():
            result += in_range_list(test_point.value, expected_ranges[rail_name], rail_name)
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
        return result

    def connector_detection(self):
        result = TestResult()
        for connector_position, test_point in self.jig.rms6_connector_probes.items():
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

    def button_press_check(self):
        LOAD_TEST_SHELL_EVENT.wait()
        result = TestResult()
        self.jig.rms6_button_press()
        sleep(0.5)
        for button_name, test_firmware_resource in self.jig.rms6_push_button_resources.items():
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
        sleep(0.1)
        return result

    def relay_control(self):
        LOAD_TEST_SHELL_EVENT.wait()
        result = TestResult()
        for relay_control_label, (test_firmware_resource, uio_reading) in self.jig.rms6_relay_control.items():
            sleep(1)
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
            flash_firmware = os.path.join(os.path.dirname(__file__), "build\\RM_V1.1(Build3.66).hex").replace("\\", "/")

            self.jig.oocd.memprog_submit(0, 0, 60)
            self.jig.oocd.memprog_wait_command(0)

            print("Program FLASH")
            resp = self.jig.oocd.memprog_program_async(flash_firmware, 60000, 0, do_erase=False, alignment={0: 2})
            result = TestResult(True, "Program MCU", CLC_Profile.FIRMWARE, CLC_Profile.FIRMWARE, resp)
            return result
        except:
            raise
    def test_suit_clean_up(self):
        self.stop_oocd()
        try:
            self.jig.dut_power_off()
        except:
            pass
        self.test_case_scheduler.Finish()