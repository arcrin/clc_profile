import codecs
import typing
from dataclasses import dataclass
from test_jig_util.Lockable import Lockable
from.BaseTestShell import BaseTestShell

@dataclass
class CANFrame:
    can_id: int
    data: bytes
    timestamp: float = 0
    remote: bool = False

class CANResource(Lockable):


    def __init__(self, test_shell: BaseTestShell, can_port: str, *args, **kwargs):
        self._shell = test_shell
        self._shell_can_port = can_port
        self._peripheral_name = f"{self.__class__.__name__}<{self._shell_can_port}>"
        Lockable.__init__(self, *args, **kwargs)

    @property
    def peripheral_name(self):
        return self._peripheral_name

    def configure(self):
        self._shell.query(f"can conf {self._shell_can_port}")

    def read(self) -> typing.Optional[CANFrame]:
        resp = self._shell.query(f"can r {self._shell_can_port}")
        if resp:
            can_id, timestamp, data = resp.split(" ")
            frame = CANFrame(int(can_id), codecs.decode(data, 'hex'), float(timestamp))
            return frame

    def write(self, frame: CANFrame):
        self._shell.query(f"can w {self._shell_can_port} {frame.can_id} {str(codecs.encode(frame.data, 'hex').decode('utf-8'))}")

    def test(self, frame: CANFrame, timeout: typing.Optional[float] = None) -> BaseTestShell.AsyncQuery:
        return self._shell.aquery(f"can test {self._shell_can_port} {frame.can_id} {str(codecs.encode(frame.data, 'hex').decode('utf-8'))}", timeout)

    def flush(self):
        self._shell.query(f"can flush {self._shell_can_port}")