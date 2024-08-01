from ._version import __version__
from .CLC_Profile import CLC_Profile
from .CLC_Jig import CLC_Jig


framework_profiles = {
    "CLC_Profile": CLC_Profile
}

framework_jigs = {
    "TAGTJ-CLC": CLC_Jig
}