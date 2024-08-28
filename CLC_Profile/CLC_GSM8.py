from CLC_Profile.CLC_Product import CLCProduct
from .test_firmware.firmwareutil.resourceshell.py.GPIOResource import GPIOResource
from .test_firmware.firmwareutil.resourceshell.py.ADCResource import ADCResource
from .test_firmware.firmwareutil.resourceshell.py.SPIResource import SPIResource
from pyDAQ.UART import DAQ_UART


class CLCGSM8(CLCProduct):
    def __init__(self, daq_uart: DAQ_UART):
        super().__init__(daq_uart)

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
            "LED_SW7": GPIOResource(self.test_shell, "LED_SW7"),
            "LED_SW8": GPIOResource(self.test_shell, "LED_SW8"),
        }

        """
            Buttons
        """
        self.button_gpio = {
            "SW501": GPIOResource(self.test_shell, "RLAY_PB1"),
            "SW601": GPIOResource(self.test_shell, "RLYB_PB1"),
            "SW502": GPIOResource(self.test_shell, "RLYA_PB2"),
            "SW602": GPIOResource(self.test_shell, "RLYB_PB2"),
            "SW503": GPIOResource(self.test_shell, "RLYA_PB3"),
            "SW603": GPIOResource(self.test_shell, "RLYB_PB3"),
            "SW504": GPIOResource(self.test_shell, "RLYA_PB4"),
            "SW604": GPIOResource(self.test_shell, "RLYB_PB4"),
        }

        """
            SPI
        """
        self.gsm8_spi = SPIResource(self.test_shell, "EEPROM")

        """
            GSM8 Jumpers
        """
        self.gsm8_pilot_light_fw_control = {
            "IP1_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWA_PILOT1"),
            "IP2_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWB_PILOT1"),
            "IP3_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWA_PILOT2"),
            "IP4_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWB_PILOT2"),
            "IP5_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWA_PILOT3"),
            "IP6_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWB_PILOT3"),
            "IP7_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWA_PILOT4"),
            "IP8_PILOT_FEEDBACK": GPIOResource(self.test_shell, "GSM8_SWB_PILOT4"),
        }

        """
            GSM8 Switch Feedback
        """
        self.gsm8_switch_on_feedback = {
            "IP1_ON_SIGNAL": ADCResource(self.test_shell, "ADC04"),
            "IP2_ON_SIGNAL": ADCResource(self.test_shell, "ADC05"),
            "IP3_ON_SIGNAL": ADCResource(self.test_shell, "ADC06"),
            "IP4_ON_SIGNAL": ADCResource(self.test_shell, "ADC07"),
            "IP5_ON_SIGNAL": ADCResource(self.test_shell, "ADC10"),
            "IP6_ON_SIGNAL": ADCResource(self.test_shell, "ADC11"),
            "IP7_ON_SIGNAL": ADCResource(self.test_shell, "ADC12"),
            "IP8_ON_SIGNAL": ADCResource(self.test_shell, "ADC13"),
        }

        self.gsm8_switch_off_feedback = {
            "IP1_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWA_OFF1"),
            "IP2_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWB_OFF1"),
            "IP3_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWA_OFF2"),
            "IP4_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWB_OFF2"),
            "IP5_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWA_OFF3"),
            "IP6_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWB_OFF3"),
            "IP7_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWA_OFF4"),
            "IP8_OFF_SIGNAL": GPIOResource(self.test_shell, "GSM8_SWB_OFF4"),
        }