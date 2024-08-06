import logging
from abstract_control import MicroscopeControl, StagePosition

from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import StagePosition as StagePositionAS

class AutoscriptMicroscopeControl(MicroscopeControl):

    def __init__(self, ip_address = "localhost"):
        """ Connect to AS server """
        self._microscope = SdbMicroscopeClient()
        self._microscope.connect(ip_address)

    def move_stage(self, goal: StagePosition, min_tolerance: float = None):
        """ Move stage to goal position
        min_tolerance - if set, the final stage position is verified (only in x and y)"""
        sp = StagePositionAS(**goal.to_dict(), coordinate_system = "raw")
        self._microscope.specimen.stage.absolute_move(sp)
        logging.debug(f"Moving stage to {goal.to_dict()}...")
        if min_tolerance is not None:


    @property
    def working_distance(self):
        return self._working_distance

    @working_distance.setter
    def working_distance(self, value):
        logging.debug(f"Setting working distance: {value}")
        self._working_distance = value

    @property
    def stigmator_x(self):
        return self._stigmator_x

    @stigmator_x.setter
    def stigmator_x(self, value):
        logging.debug(f"Setting stigmator x: {value}")
        self._stigmator_x = value

    @property
    def stigmator_y(self):
        return self._stigmator_y

    @stigmator_y.setter
    def stigmator_y(self, value):
        logging.debug(f"Setting stigmator y: {value}")
        self._stigmator_y = value

    @property
    def lens_alignment_x(self):
        return self._lens_alignment_x

    @lens_alignment_x.setter
    def lens_alignment_x(self, value):
        logging.debug(f"Setting lens alignment x: {value}")
        self._lens_alignment_x = value

    @property
    def lens_alignment_y(self):
        return self._lens_alignment_y

    @lens_alignment_y.setter
    def lens_alignment_y(self, value):
        logging.debug(f"Setting lens alignment y: {value}")
        self._lens_alignment_y = value

    def detector_contrast(self):
        logging.debug("Setting detector contrast...")

    def detector_brightness(self):
        logging.debug("Setting detector brightness...")

    def blank_unblank_beam(self):
        logging.debug("Blanking/Unblanking the beam...")

    def start_acquisition(self):
        logging.debug("Starting acquisition...")

    def stop_acquisition(self):
        logging.debug("Stopping acquisition...")