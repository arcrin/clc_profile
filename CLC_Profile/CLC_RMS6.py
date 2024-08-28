from CLC_Profile.CLC_Product import CLCProduct
from .test_firmware.firmwareutil.resourceshell.py.GPIOResource import GPIOResource
from .test_firmware.firmwareutil.resourceshell.py.ADCResource import ADCResource


class CLCRMS6(CLCProduct):
    def __init__(self, daq_uart):
        super().__init__(daq_uart)

        self.rms6_nreverse_jumper = GPIOResource(self.test_shell, "RMS6_nREVERSE_JUMPER")

        """
            LED
        """
        self.switch_led_gpio = {
            "LED_SW1": GPIOResource(self.test_shell, "LED_SW1"),
            "LED_SW2": GPIOResource(self.test_shell, "LED_SW2"),
            "LED_SW3": GPIOResource(self.test_shell, "LED_SW3"),
            "LED_SW4": GPIOResource(self.test_shell, "LED_SW4"),
            "LED_SW5": GPIOResource(self.test_shell, "LED_SW5"),
            "LED_SW6": GPIOResource(self.test_shell, "LED_SW6"),
        }


        self.button_gpio = {
            "SW311": GPIOResource(self.test_shell, "RLAY_PB1"),
            "SW301": GPIOResource(self.test_shell, "RLYB_PB1"),
            "SW312": GPIOResource(self.test_shell, "RLYA_PB2"),
            "SW302": GPIOResource(self.test_shell, "RLYB_PB2"),
            "SW313": GPIOResource(self.test_shell, "RLYA_PB3"),
            "SW303": GPIOResource(self.test_shell, "RLYB_PB3"),
        }

        self.rms6_relay_control = {
            "RELAY1_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYA_OFF1"),
            "RELAY1_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYA_ON1"),
            "RELAY2_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYB_OFF1"),
            "RELAY2_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYB_ON1"),
            "RELAY3_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYA_OFF2"),
            "RELAY3_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYA_ON2"),
            "RELAY4_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYB_OFF2"),
            "RELAY4_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYB_ON2"),
            "RELAY5_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYA_OFF3"),
            "RELAY5_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYA_ON3"),
            "RELAY6_OFF_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYB_OFF3"),
            "RELAY6_ON_SIGNAL": GPIOResource(self.test_shell, "RMS6_RLYB_ON3"),
        }

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

        self.rms6_relay_feedback = {
            "RELAY1_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC04"),
            "RELAY2_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC05"),
            "RELAY3_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC06"),
            "RELAY4_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC07"),
            "RELAY5_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC10"),
            "RELAY6_PILOT_FEEDBACK": ADCResource(self.test_shell, "ADC11"),
        }