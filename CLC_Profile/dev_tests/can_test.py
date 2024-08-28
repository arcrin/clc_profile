from pyDAQ.CAN import CAN
from pyDAQ.UniversalIO import UniversalIO, DAQ
from test_firmware.firmwareutil.resourceshell.py.CANResource import CANResource, CANFrame
import typing

daq_ports = DAQ.FindDAQs()

assert len(daq_ports) == 2, "There should be 2 DAQs connected"

_daqs = [UniversalIO(port=port.device) for port in daq_ports]

_a: typing.Dict[int, UniversalIO] = {int(daq.write("address")): daq for daq in _daqs}
daq1 = _a[1]
daq2 = _a[2]

can1 = CAN(daq1)
can2 = CAN(daq2)

sample_can_data = CANFrame(int(4), b'\x68\x65\x6c\x6c\x6f')

