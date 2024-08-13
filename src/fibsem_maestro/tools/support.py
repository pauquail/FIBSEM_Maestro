import math
from enum import Enum


class Imaging(Enum):
    electron = "eb"
    ion = "ib"


class Point:
    def __init__(self, x=0, y=0):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        self._x = x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        self._y = y

    @staticmethod
    def from_point_as(point_as):
        """Create a Point instance from a AS Point instance."""
        return Point(x=point_as.x, y=point_as.y)

    def to_xy(self):
        return (self.x, self.y)

    def to_dict(self):
        return vars(self)

    def __mul__(self, other):
        if isinstance(other, Point):
            return Point(self.x * other.x, self.y * other.y)
        else:
            return NotImplemented

class StagePosition:
    """
    Class representing the stage position
    Rotation and tilt is in deg
    """

    def __init__(self, x=0.0, y=0.0, z=0.0, rotation=0.0, tilt=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.rotation = rotation
        self.tilt = tilt

    @staticmethod
    def from_stage_position_as(stage_position_as):
        """Create a StagePosition instance from a AS StagePosition instance."""
        return StagePosition(x=stage_position_as.x, y=stage_position_as.y, z=stage_position_as.z,
                             rotation=math.degrees(stage_position_as.r),
                             tilt=math.degrees(stage_position_as.t))

    def to_dict(self):
        return vars(self)

    def to_xy(self):
        return (self.x, self.y)