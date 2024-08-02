from .BaseTestShell import BaseTestShell
from pyDAQ.GPIO import BaseGPIO


class GPIOResource(BaseGPIO):
    def __init__(self, shell: BaseTestShell, name: str):
        """

        :param shell:
        :param name: pin name as defined in test firmware
        """

        self._name = name
        self._peripheral_name = f"{self.__class__.__name__}<{self._name}>"
        super().__init__()
        self._shell = shell

    @property
    def peripheral_name(self):
        return self._peripheral_name

    def configure(self):
        self._shell.query(f"GPIOResource CONF {self._name}", )

    @property
    def value(self) -> bool:
        resp = self._shell.query(f"GPIOResource R {self._name}")
        value = bool(int(resp))
        return value

    @value.setter
    def value(self, value: bool):
        command = f"GPIOResource W {self._name} {'1' if value else '0'}"
        self._shell.query(command)
