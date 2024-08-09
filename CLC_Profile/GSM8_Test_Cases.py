from CLC_Profile import CLC_Profile

class GSM8TestCases:
	def __init__(self, profile: CLC_Profile):
		self._profile = profile


		self._profile.add_test(
			"Jumper",
			prerequisites=["Load Test Shell"],
			description="Measure the voltage rails",
			verify_function=lambda x: x,
			real_function=self._profile.gsm8_jumper_reading,
			function=self._profile.test_case_scheduler.TestCaseWaiter,
		)

		self._profile.add_test(
			"Switch Pilot Control",
			prerequisites=["Load Test Shell"],
			description="Control the relays",
			verify_function=lambda x: x,
			real_function=self._profile.gsm8_sw_pilot,
			function=self._profile.test_case_scheduler.TestCaseWaiter
		)

		self._profile.add_test(
			"Switch Pilot Feedback",
			prerequisites=["Load Test Shell"],
			description="Check the relay feedback",
			verify_function=lambda x: x,
			real_function=self._profile.gsm8_sw_feedback,
			function=self._profile.test_case_scheduler.TestCaseWaiter
		)

		self._profile.add_test(
			"SPI",
			prerequisites=["Load Test Shell"],
			description="Check SPI communication",
			verify_function=lambda x: x,
			real_function=self._profile.spi_test,
			function=self._profile.test_case_scheduler.TestCaseWaiter,
			parameters={"sn": self._profile.dut.SerialNumber}
		)