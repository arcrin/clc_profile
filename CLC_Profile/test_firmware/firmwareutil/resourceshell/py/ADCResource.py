from .BaseTestShell import BaseTestShell

class ADCResource:
    def __init__(self, shell: BaseTestShell, name: str):
        self._name = name
        self._peripheral_name = f"{self.__class__.__name__}<{self._name}>"
        super().__init__()
        self._shell = shell

    @property
    def peripheral_name(self):
        return self._peripheral_name

    @property
    def value(self):
        resp = self._shell.query(f"adc r {self._name}")
        adc_value = int(resp)
        value = 3.3 / 4096 * adc_value
        return value

    def configure(self):
        self._shell.query(f"ADCResource CONF {self._name}")