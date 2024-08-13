""" Unit test for low level microscope control"""
import logging

from fibsem_maestro.microscope_control.autoscript_control import AutoscriptMicroscopeControl
from fibsem_maestro.microscope_control.microscope import create_microscope
from fibsem_maestro.tools.support import StagePosition, Point, Imaging

logging.getLogger().handlers.clear()  # leave only root logger
logging.basicConfig(level=logging.DEBUG)

mic = create_microscope(AutoscriptMicroscopeControl())

mic.stage_move_with_verification(StagePosition(0, 0, z=30e-3, tilt=35, rotation=180))
print(f"Stage position: {mic.position.to_dict()}")

mic.beam_shift_with_verification(new_beam_shift=Point(1e-6, -1e-6))

mic.beam_shift_with_verification(new_beam_shift=Point(4e-6, -4e-6))

mic.position = StagePosition(1e-3, 1e-3, z=0, tilt=0, rotation=180)