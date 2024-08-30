import logging
from scipy.spatial import distance

from fibsem_maestro.tools.support import StagePosition, Point, ScanningArea
from fibsem_maestro.microscope_control.autoscript_control import AutoscriptMicroscopeControl
from fibsem_maestro.microscope_control.abstract_control import MicroscopeControl


def create_microscope(control: str):
    """
    :param control: The type of microscope control. Possible values are: 'autoscript'
    :type control: str
    :return: A dynamically created Microscope class based on the given control type.

    """
    if control.lower() == 'autoscript':
        microscope_base = AutoscriptMicroscopeControl
    else:
        raise ValueError(f"Invalid microscope control type: {control}")

    class Microscope(microscope_base):
        def __init__(self, stage_tolerance=1e-7, stage_trials=3,
                     beamshift_tolerance=50e-9, beam_shift_to_stage_move = (-1, -1), **kwargs):
            """
            Initializes a new instance of the class.

            :param stage_tolerance: The tolerance value for stage movement.
                                    Default is 1e-6.
            :type stage_tolerance: float

            :param stage_trials: The number of trials to perform for stage movement.
                                 Default is 3.
            :type stage_trials: int
            :param beamshift_tolerance: The tolerance value for beam shift.
                            Default is 50e-9.
            :type beamshift_tolerance: float
            :param beam_shift_to_stage_move: Relative axis direction between beam shift and stage movement.
                                     Default is (-1, -1).
            :type beam_shift_to_stage_move: Tuple[int, int]
            """
            super().__init__(**kwargs)
            self.stage_tolerance = stage_tolerance
            self.stage_trials = stage_trials
            self.stage_trial_counter = stage_trials
            self.beamshift_tolerance = beamshift_tolerance
            self.beam_shift_to_stage_move = beam_shift_to_stage_move
            self.beam = self.electron_beam  # default setting for actual beam

        def stage_move_with_verification(self, new_stage_position: StagePosition):
            """
            Moves the stage to the specified position and verifies the movement within a tolerance.

            :param new_stage_position: The new position of the stage.
            :return: None
            """
            self.position = new_stage_position  # set stage position
            position = self.position  # get stage position
            # after movement, verify whether the movement is within tolerance
            dist = distance.euclidean(position.to_xy(), new_stage_position.to_xy())

            if dist > self.stage_tolerance:
                logging.warning(
                    f"Stage reached position {new_stage_position} is too far ({dist}) from defined position {new_stage_position} ")
                self.stage_trial_counter -= 1
                self.stage_move_with_verification(new_stage_position)  # move again
                if self.stage_trial_counter == 0:
                    logging.error("Stage movement failed after multiple trials")
                    raise Exception("Stage movement failed after multiple trials")
            else:
                # reset trials counter
                self.stage_trial_counter = self.stage_trials

        def beam_shift_with_verification(self, new_beam_shift: Point):
            """
            Do beam shift.
            If the beam shift is out of range, do relative movement by stage.
            """
            try:
                self.beam.beam_shift = new_beam_shift  # set beam shift
                dist = distance.euclidean(self.beam.beam_shift.to_xy(), new_beam_shift.to_xy())
                if dist > self.beamshift_tolerance:
                    raise Exception("Beam shift out of range")
            except:  # if any problem with beam shift or out of range -> stage move
                logging.warning("Beam shift is out of range. Stage position needs to be adjusted.")
                # stage move = beam shift * axis reversion
                new_stage_move = new_beam_shift * Point(self.beam.beam_shift_to_stage_move[0], self.beam.beam_shift_to_stage_move[1])
                self.relative_position = StagePosition(x=new_stage_move.x, y=new_stage_move.y)
                self.beam.beam_shift = Point(0, 0)  # zero beam shift

        def blank_screen(self):
            """
            Make a black screen (blank and grab frame).
            :return: None
            """
            contrast_backup = self.beam.detector_contrast
            brightness_backup = self.beam.detector_brightness
            dwell_backup = self.beam.dwell_time
            self.beam.detector_contrast = 0
            self.beam.detector_brightness = 0
            self.beam.blank()
            self.beam.grab_frame()
            self.beam.dwell_time = dwell_backup
            self.beam.contrast = contrast_backup
            self.beam.brightness = brightness_backup

        def total_blank(self):
            """
            Blank with zero contrast and brightness
            :return:
            """
            self._detector_contrast_backup = self.beam.detector_contrast
            self._detector_brightness_backup = self.beam.detector_brightness
            self.beam.detector_contrast = 0
            self.beam.detector_brightness = 0
            self.beam.blank()

        def total_unblank(self):
            self.beam.detector_contrast = self._detector_contrast_backup
            self.beam.detector_brightness = self._detector_brightness_backup
            self.beam.unblank()

        def area_scanning(self):
            """ Perform scanning in reduced area and crop out the image """
            assert self.beam.scanning_area is not None, "Scanning area is not set"
            img = self.beam.grab_frame()
            left_top, size = self.beam.scanning_area.to_img_coordinates(img.shape)
            img_cropped = img[left_top[0]:left_top[0] + size[0], left_top[1]:left_top[1] + size[1]]
            return img_cropped


    return Microscope  # factory

