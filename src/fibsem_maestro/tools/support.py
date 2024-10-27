import math
import re

import numpy
import numpy as np


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
        return self.x, self.y

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

    def __str__(self):
        return f"Point({self.x}, {self.y})"

    @classmethod
    def from_str(cls, point_string):
        # Extract the coordinates from the string
        x, y = map(float, point_string[6:-1].split(', '))
        return cls(x, y)


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
        return StagePositionAS(**stage_dict, coordinate_system="Specimen")

    def to_dict(self):
        return vars(self)

    def to_xy(self):
        return self.x, self.y

    def __str__(self):
        return f"StagePosition({self.x}, {self.y}, {self.z}, {self.rotation}, {self.tilt})"

    @classmethod
    def from_str(cls, point_string):
        # Extract the coordinates from the string
        x, y, z, r ,t = map(float, point_string[14:-1].split(', '))
        return cls(x, y, z, r, t)


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
        left_top = [center_pix.x - height_pix // 2,
                    center_pix.y - width_pix // 2]
        return left_top, [height_pix, width_pix]

    def __str__(self):
        return f"ScanningArea({self.center.x}, {self.center.y}, {self.width}, {self.height})"

    @classmethod
    def from_str(cls, point_string):
        # Extract the coordinates from the string
        x, y, w, h = map(float, point_string[13:-1].split(', '))
        return cls(Point(x, y), w, h)


class Image(np.ndarray):
    def __new__(cls, image, pixel_size):
        obj = np.asarray(image.data).view(cls)
        obj.pixel_size = pixel_size
        return obj

    @staticmethod
    def from_as(adorned_image):
        pixel_size = adorned_image.metadata.binary_result.pixel_size.x
        image = np.array(adorned_image.data)
        return Image(image, pixel_size)

    def __array_finalize__(self, obj):
        if obj is None: return
        self.pixel_size = getattr(obj, 'pixel_size', None)

    def __getitem__(self, index):
        result = super(Image, self).__getitem__(index)
        if type(result) is Image:
            return result
        else:
            return Image(result, self.pixel_size)


def find_in_dict(name, list_of_dicts):
    """ find the item in a dict based on name value """
    if name == 'none':
        return None
    else:
        return [dic for dic in list_of_dicts if dic['name'] == name][0]


def find_in_objects(name, list_of_objects):
    """ find the item in objects list based on name value """
    if name == 'none':
        return None
    else:
        return [dic for dic in list_of_objects if dic.name == name][0]


def fold_filename(log_dir, slice_number, postfix=""):
    """return: log_dir+slice_number+postfix"""
    if slice_number is None:
        slice_number = -1
    filename = log_dir + f'/{slice_number:05}/{postfix}'
    return filename
