from abc import ABC, abstractmethod


class MicroscopeControl(ABC):
    """
    This is an abstract base class for controlling a microscope.

    The class provides the interface methods that should be implemented by any specific microscope control class (such as
    FIBSEM API, or direct Autoscript


    These methods include basic functionalities for controlling the various components
    and parameters of a microscope such as the stage, lens alignment, detector properties, beam controls, and acquisition.
    """

    @abstractmethod
    def move_stage(self):
        pass

    @property
    @abstractmethod
    def working_distance(self):
        pass

    @working_distance.setter
    @abstractmethod
    def working_distance(self, value):
        pass

    @property
    @abstractmethod
    def stigmator_x(self):
        pass

    @stigmator_x.setter
    @abstractmethod
    def stigmator_x(self, value):
        pass

    @property
    @abstractmethod
    def stigmator_y(self):
        pass

    @stigmator_y.setter
    @abstractmethod
    def stigmator_y(self, value):
        pass

    @property
    @abstractmethod
    def lens_alignment_x(self):
        pass

    @lens_alignment_x.setter
    @abstractmethod
    def lens_alignment_x(self, value):
        pass

    @property
    @abstractmethod
    def lens_alignment_y(self):
        pass

    @lens_alignment_y.setter
    @abstractmethod
    def lens_alignment_y(self, value):
        pass

    @abstractmethod
    def detector_contrast(self):
        pass

    @abstractmethod
    def detector_brightness(self):
        pass

    @abstractmethod
    def blank_unblank_beam(self):
        pass

    @abstractmethod
    def start_acquisition(self):
        pass

    @abstractmethod
    def stop_acquisition(self):
        pass


class StagePosition:
    """
    Class representing the stage position
    Rotation and tilt is in deg
    """
    def __init__(self, x=0, y=0, z=0, rotation=0, tilt=0):
        self.x = x
        self.y = y
        self.z = z
        self.rotation = rotation
        self.tilt = tilt

    def to_dict(self):
        return vars(self)