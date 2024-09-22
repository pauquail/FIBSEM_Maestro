import logging

import numpy as np

from fibsem_maestro.tools.image_tools import image_saturation_info, image_bit_dept_band


class AutomaticContrastBrightness:
    def __init__(self, settings, microscope, logging_dict, logging_enabled=False, log_dir=None):
        self._initialize_settings(settings)
        self._microscope = microscope
        self._logging_dict = logging_dict
        self._log_dir = log_dir
        self._logging = logging_enabled

    def _initialize_settings(self, acb_settings):
        self.function = acb_settings['function']
        self.mask_name = acb_settings['mask_name']
        self.allowed_saturation = acb_settings['allowed_saturation']
        self.allowed_minimal_band = acb_settings['allowed_minimal_band']
        self.p_contrast = acb_settings['p_contrast']
        self.p_brightness = acb_settings['p_brightness']

    def decrease_contrast(self, decrease_value):
        self._microscope.beam.contrast -= decrease_value * self.p_contrast

    def increase_contrast(self, increase_value):
        self._microscope.beam.contrast += increase_value * self.p_contrast

    def __call__(self, image):
        if self.function == 'acb':
            logging.info('ACB executed')
            saturated, zeroed = image_saturation_info(image)

            # too much saturation and zeoring - decrease contrast
            if saturated > self.allowed_saturation and zeroed > self.allowed_saturation:
                logging.info(f'Contrast lowering needed. Saturated fraction: {saturated}, Zeroed fraction: {zeroed}')
                self.decrease_contrast(max(saturated, zeroed))

            # too low contrast
            if image_bit_dept_band(image) < self.allowed_minimal_band:



        else:
            logging.info('No acb executed')