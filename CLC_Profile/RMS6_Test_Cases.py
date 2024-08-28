from CLC_Profile import CLC_Profile


class RMS6TestCases:
    def __init__(self, profile: CLC_Profile):
        self._profile = profile

        self._profile.add_test("Jumper",
                               prerequisites=["Load Test Shell"],
                               description="Measure the voltage rails",
                               verify_function=lambda x: x,
                               real_function=self._profile.rms6_jumper_reading,
                               function=self._profile.test_case_scheduler.TestCaseWaiter,
                               )

        self._profile.add_test("Relay Control Signals",
                               prerequisites=["Load Test Shell"],
                               description="Control the relays",
                               verify_function=lambda x: x,
                               real_function=self._profile.relay_control,
                               function=self._profile.test_case_scheduler.TestCaseWaiter
                               )

        self._profile.add_test("Relay Feedback",
                               prerequisites=["Load Test Shell"],
                               description="Check the relay feedback",
                               verify_function=lambda x: x,
                               real_function=self._profile.relay_feedback,
                               function=self._profile.test_case_scheduler.TestCaseWaiter)

        self._profile.add_test("Switch Control Feedback",
                               prerequisites=["Load Test Shell"],
                               description="Check the switch control reading",
                               verify_function=lambda x: x,
                               real_function=self._profile.switch_control_feedback,
                               function=self._profile.test_case_scheduler.TestCaseWaiter
                               )

