import math
from enum import Enum


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
        elif isinstance(other, list):
            return Point(self.x * other[0], self.y * other[1])
        else:
            return TypeError("Unsupported operand type")

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        else:
            raise TypeError("Unsupported operand type")

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

    def to_stage_position_as(self):
        """Convert StagePosition to AS StagePosition instance."""
        from autoscript_sdb_microscope_client.structures import StagePosition as StagePositionAS
        stage_dict = self.to_dict()
        stage_dict['r'] = math.radians(stage_dict['rotation'])
        stage_dict['t'] = math.radians(stage_dict['tilt'])
        del stage_dict['rotation']
        del stage_dict['tilt']
        return StagePositionAS(**stage_dict, coordinate_system="raw")

    def to_dict(self):
        return vars(self)

    def to_xy(self):
        return (self.x, self.y)

class ScanningArea:
    def __init__(self, center: Point, width: float, height: float):
        """ Area defined as the fraction (center of the image = 0.5)"""
        self.center = center
        self.width = width
        self.height = height

    def to_as(self):
        """ Convert the coordinates to AS coordinates """
        raise NotImplementedError("Not implemented yet")

    def to_img_coordinates(self, img_shape):
        """
        Calculate the coordinates of an object in an image based on its relative position and size.

        :param img_shape: The shape of the image as a tuple (height, width).
        :type img_shape: tuple
        :return: The left top coordinates of the object and its size as a tuple.
        :rtype: tuple
        """
        center_pix = self.center * img_shape
        height_pix = img_shape[0] * self.height
        width_pix = img_shape[1] * self.width
        left_top = [center_pix[0] - height_pix // 2,
                    center_pix[1] - width_pix // 2]
        return left_top, [height_pix, width_pix]
