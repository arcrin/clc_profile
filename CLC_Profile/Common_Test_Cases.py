from CLC_Profile import CLC_Profile

class CommonTestCases:
    def __init__(self, profile: CLC_Profile):
        self._profile = profile
        _product = None
        if self._profile.dut.ProductNumber == CLC_Profile.CLC_Profile.CLCRMS6_PN:
            _product = "CLCRMS6"
        elif self._profile.dut.ProductNumber == CLC_Profile.CLC_Profile.CLCGSM8_PN:
            _product = "CLCGSM8"

        self._profile.add_test("Startup",
            description="Set up the test environment, such as turning on the product",
            verify_function=lambda x: x,
            function=self._profile.startup
        )

        preliminary_voltage_rails = None
        if _product == "CLCRMS6":
            preliminary_voltage_rails = self._profile.jig.rms6_preliminary_voltage_rails
        elif _product == "CLCGSM8":
            preliminary_voltage_rails = self._profile.jig.gsm8_preliminary_voltage_rails

        self._profile.add_test("Preliminary Voltage Rails",
            description="Measure the voltage rails",
            verify_function=lambda x: x,
            function=self._profile.preliminary_voltage_rails,
            parameters={"voltage_rails": preliminary_voltage_rails} if preliminary_voltage_rails else {}
        )

        self._profile.add_test("Start Threads",
            prerequisites=["Preliminary Voltage Rails"],
            description="Start thread scheduler",
            verify_function=lambda x: x,
            function=self._profile.start_test_case_scheduler
                      )

        self._profile.add_test("Start OpenOCD",
            description="Start OpenOCD",
            verify_function=lambda x: x,
            function=self._profile.start_oocd
                      )

        self._profile.add_test("Load Test Shell",
            prerequisites=["Start OpenOCD", "Start Threads", "Preliminary Voltage Rails"],
            description="Load the test shell",
            verify_function=lambda x: x,
            function=self._profile.load_test_shell
                      )

        connectors_probes = None
        if _product == "CLCRMS6":
            connectors_probes = self._profile.jig.rms6_connector_probes
        elif _product == "CLCGSM8":
            connectors_probes = self._profile.jig.gsm8_connector_probes

        self._profile.add_test("Program Flash",
            prerequisites=["Load Test Shell"],
            description="Program the flash",
            verify_function=lambda x: x,
            # function=self.program_flash,
            real_function=self._profile.program_flash,
            function=self._profile.test_case_scheduler.TestCaseWaiter)

        self._profile.add_test("Connector Detection",
            prerequisites=["Start Threads"],
            description="Detect the connectors",
            verify_function=lambda x: x,
            real_function=self._profile.connector_detection,
            function=self._profile.test_case_scheduler.TestCaseWaiter,
            parameters={"connectors_probes": connectors_probes} if connectors_probes else {})

        button_press_detection = None
        if _product == "CLCRMS6":
            button_press_detection = self._profile.jig.rms6_button_press_detection
        elif _product == "CLCGSM8":
            button_press_detection = self._profile.jig.gsm8_button_press_detection
        self._profile.add_test("Button Press Check",
            prerequisites=["Load Test Shell"],
            description="Check if buttons are pressed",
            verify_function=lambda x: x,
            # function=self.button_press_check,
            real_function=self._profile.button_press_check,
            function=self._profile.test_case_scheduler.TestCaseWaiter,
            parameters={"button_press_detection": button_press_detection} if button_press_detection else {})

        self._profile.add_test("Address",
            prerequisites=["Load Test Shell"],
            description="Check the address",
            verify_function=lambda x: x,
            real_function=self._profile.read_address,
            function=self._profile.test_case_scheduler.TestCaseWaiter)

        relay_switch_leds = None
        sys_led_sensor = None
        if _product == "CLCRMS6":
            relay_switch_leds = self._profile.jig.rms6_relay_leds
            sys_led_sensor =  self._profile.jig.rms6_sys_led_sensor
        elif _product == "CLCGSM8":
            relay_switch_leds = self._profile.jig.gsm8_switch_leds
            sys_led_sensor =  self._profile.jig.gsm8_sys_led_sensor
        self._profile.add_test("LED Test",
            prerequisites=["Load Test Shell"],
            description="Test the LEDs",
            verify_function=lambda x: x,
            real_function=self._profile.led_test,
            function=self._profile.test_case_scheduler.TestCaseWaiter,
            parameters={
                    "relay_switch_leds": relay_switch_leds if relay_switch_leds else None,
                    "sys_led_sensor": sys_led_sensor if sys_led_sensor else None
                })


        # self._profile.add_test("CAN Termination Test",
        #               prerequisites=["Load Test Shell"],
        #               description="Check the CAN termination",
        #               verify_function=lambda x: x,
        #               real_function=self._profile.can_termination_test,
        #               function=self._profile.test_case_scheduler.TestCaseWaiter
        #               )

        self._profile.add_test("CAN Communication",
            prerequisites=["Load Test Shell"],
            description="Check the CAN communication",
            verify_function=lambda x: x,
            real_function=self._profile.can,
            function=self._profile.test_case_scheduler.TestCaseWaiter)

        can_led_sensor = None
        if _product == "CLCRMS6":
            can_led_sensor = self._profile.jig.rms6_can_led_sensor
        elif _product == "CLCGSM8":
            can_led_sensor = self._profile.jig.gsm8_can_led_sensor
        self._profile.add_test("CAN LED",
            prerequisites=["Load Test Shell", "CAN Communication"],
            description="Test the CAN LED",
            verify_function=lambda x: x,
            real_function=self._profile.can_led,
            function=self._profile.test_case_scheduler.TestCaseWaiter,
            parameters={"can_led_sensor": can_led_sensor} if can_led_sensor else {})