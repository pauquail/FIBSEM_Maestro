import logging
from scipy.spatial import distance

from fibsem_maestro.tools.support import StagePosition, Point, Imaging
from fibsem_maestro.microscope_control.autoscript_control import AutoscriptMicroscopeControl
from fibsem_maestro.microscope_control.abstract_control import MicroscopeControl

def create_microscope(control: MicroscopeControl):
    """
    Factory for Microscope object.
    Based on argument type (AutoscriptMicroscopeControl), it return Microscope object
    that is inherited from the same class as argument.
    """

    if isinstance(control, AutoscriptMicroscopeControl):
        microscope_base = AutoscriptMicroscopeControl
    else:
        raise ValueError(f"Invalid microscope control type: {control}")

    class Microscope(microscope_base):
        def __init__(self, microscope_control, stage_tolerance=1e-7, stage_trials=3,
                     beamshift_tolerance=50e-9, beam_shift_to_stage_move = (-1, -1)):
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
            :param beamshift_tolerance: The tolerance value for beam shift.
                            Default is 50e-9.
            :type beamshift_tolerance: float
            :param beam_shift_to_stage_move: Relative axis direction between beam shift and stage movement.
                                     Default is (-1, -1).
            :type beam_shift_to_stage_move: Tuple[int, int]
            """
            super().__init__(kwargs)
            self.microscope_control = microscope_control
            self.stage_tolerance = stage_tolerance
            self.stage_trials = stage_trials
            self.stage_trial_counter = stage_trials
            self.beamshift_tolerance = beamshift_tolerance
            self.beam_shift_to_stage_move = beam_shift_to_stage_move

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

        def beam_shift_with_verification(self, new_beam_shift: Point, selected_beam: Imaging = Imaging.electron):
            """
            Do beam shift.
            If the beam shift is out of range, do relative movement by stage.
            """
            try:
                self.beam(selected_beam).beam_shift = new_beam_shift  # set beam shift
                dist = distance.euclidean(self.beam(selected_beam).beam_shift.to_xy(), new_beam_shift.to_xy())
                if dist > self.beamshift_tolerance:
                    raise Exception("Beam shift out of range")
            except:  # if any problem with beam shift or out of range -> stage move
                logging.warning("Beam shift is out of range. Stage position needs to be adjusted.")
                # stage move = beam shift * axis reversion
                new_stage_move = new_beam_shift * Point(self.beam(selected_beam).beam_shift_to_stage_move[0], self.beam(selected_beam).beam_shift_to_stage_move[1])
                self.relative_position = StagePosition(x=new_stage_move.x, y=new_stage_move.y)
                self.beam(selected_beam).beam_shift = Point(0, 0)  # zero beam shift

    return Microscope  # factory
