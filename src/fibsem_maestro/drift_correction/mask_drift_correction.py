import logging


class MaskDriftCorrection:
    def __init__(self, mask, microscope, logging_dict):
        assert mask is not None, 'Mask not found. Drift correction failed.'

        self._mask = mask
        self._microscope = microscope
        self.logging_dict = logging_dict

    def __call__(self, slice_number):
        self.current_position = self._mask._get_center()
        center = self._mask.image_ceter
        pixel_size = self._mask.image_pixel_size
        if self.current_position is not None:
            shift_x = (center[0] - self.current_position[0]) * pixel_size
            shift_y = (center[1] - self.current_position[1]) * pixel_size
            self.logging_dict[f"shift_x"] = shift_x
            self.logging_dict[f"shift_y"] = shift_y
        else:
            logging.warning('The position in mask drift correction is not defined!')

    @property
    def mask(self):
        return self._mask
