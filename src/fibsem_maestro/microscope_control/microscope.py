import logging

from scipy.spatial import distance


class Microscope:
    def __init__(self, microscope_control, stage_tolerance=1e-6, stage_trials=3):
        """
        Initializes a new instance of the class.

        :param microscope_control: The microscope control object.
        :type microscope_control: object

        :param stage_tolerance: The tolerance value for stage movement.
                                Default is 1e-6.
        :type stage_tolerance: float

        :param stage_trials: The number of trials to perform for stage movement.
                             Default is 3.
        :type stage_trials: int
        """
        self.microscope_control = microscope_control
        self.stage_tolerance = stage_tolerance
        self.stage_trials = stage_trials
        self.stage_trial_counter = stage_trials

    def stage_move_with_verification(self, new_stage_position):
        """
        Moves the stage to the specified position and verifies the movement within a tolerance.

        :param new_stage_position: The new position of the stage.
        :return: None
        """
        self.position(new_stage_position)  # set stage position
        position = self.position  # get stage position
        # after movement, verify whether the movement is within tolerance
        dist = distance.euclidean(position, new_stage_position)

        if dist > self.stage_tolerance:
            logging.warning(
                f"Stage reached position {new_stage_position} is too far ({dist}) from defined position {new_stage_position} ")
            self.stage_trial_counter -= 1
            if self.stage_trial_counter == 0:
                logging.error("Stage movement failed after multiple trials")
                raise Exception("Stage movement failed after multiple trials")
        else:
            # reset trials counter
            self.stage_trial_counter = self.stage_trials

    def beam_shift_with_verification(self, new_beam_shift):
        try:
            self.beam_shift = Point(x, y)
            if abs(microscope.beams.electron_beam.beam_shift.value.x - x) > 50e-9 or abs(
                    microscope.beams.electron_beam.beam_shift.value.y - y) > 50e-9:
                raise Exception("Beam shift out of range")
        except:
            print("Beam shift is out of range. Stage position was adjusted.")
            # raise Exception("Stage err")
            x = -x  # stage has reversed x-axis
            y = -y * cal_y  # stage has reversed y-axis - corrected because of angle
            # beam shift out of range
            microscope.specimen.stage.relative_move(StagePosition(x=x, y=y))
            microscope.beams.electron_beam.beam_shift.value = Point(0, 0)
        return microscope.beams.electron_beam.beam_shift.value, microscope.specimen.stage.current_position

        # here, implement the logic of beam shifting
        self.beam_shift = new_beam_shift
        print(f"Beam shifted to: {self.beam_shift}")

        # after shift, verify the shift
        # assuming we have a method "verify_beam_shift"
        verification_status = self.verify_beam_shift(self.beam_shift)
        print(f"Verification status: {verification_status}")

    def verify_beam_shift(self, beam_shift):
        return True  # change this with real verification logic

    def __getattr__(self, attr):
        """Call attributes from microscope_control if not found"""
        return getattr(self.microscope_control, attr)
