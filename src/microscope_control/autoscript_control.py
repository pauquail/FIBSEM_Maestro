import logging
from abstract_control import MicroscopeControl

class AutoscriptMicroscopeControl(MicroscopeControl):

    def __init__(self):

    def move_stage(self):
        logging.debug("Moving stage...")

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