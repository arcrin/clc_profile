from interface.OpenOCD.OpenOCD import OpenOCD
from interface.jflash import GetModuleInfo
import threading
import logging
import os

info = {
    "build_dir": "clc_build",
    "param_base_address": 0x20004C00,
    "test_image": "clc.hex",
    "cfg_file": "stm32f1x_no_working_area.cfg",
}

mcu_info = GetModuleInfo("CLC")

flash_erased_event = threading.Event()


def program_flash(oocd: OpenOCD):
    # ASK: what is this output file?
    #   seems like  the the firmware file to be programmed
    # output_file = ""

    print("Erasing FLASH")
    oocd.memprog_submit(0, 0, 60)
    oocd.memprog_wait_command(0)
    flash_erased_event.set()

    print("Programming FLASH")

# Get the current directory of the script
current_directory = os.path.dirname(__file__)

# Construct the path to the build folder
test_firmware_path = os.path.join(os.path.dirname(__file__), "test_firmware\\CLC_STM32F103xB.hex").replace("\\", "/")
# test_firmware_path = os.path.join(os.path.dirname(__file__), "test_firmware\\clc_test_firmware.hex").replace("\\", "/")
flash_firmware = os.path.join(os.path.dirname(__file__), "build\\clc_led_toggle.hex").replace("\\", "/")
# flash_firmware = os.path.join(os.path.dirname(__file__), "build\\RM_V1.1(Build3.66).hex").replace("\\", "/")

print(test_firmware_path)

kw = {"extra_args": ("-d-3",)}

try:
    with OpenOCD(info["cfg_file"], "swd", port=0, device=mcu_info["MCU"], info=mcu_info, verify_id=False, speed=2000, log_level=logging.DEBUG, ft12=False, **kw) as oocd:
        try:
            # Load test firmware
            oocd.load_ram_image(test_firmware_path)
            oocd.memprog_init(info["param_base_address"])
            oocd.memprog_submit(0, 0, 60)
            oocd.memprog_wait_command(0)
            flash_erased_event.set()

            print("FLASH earased")
            print("Start programming FLASH")
            resp = oocd.memprog_program_async(flash_firmware, 60000, 0, do_erase=False, alignment={0: 2})
            print(resp)

        except Exception as e:
            print(e)
            raise
except Exception as e:
    print(e)
    raise
