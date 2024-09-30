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
        self.p_increase_contrast = acb_settings['p_increase_contrast']
        self.p_decrease_contrast = acb_settings['p_decrease_contrast']
        self.p_brightness = acb_settings['p_brightness']

    def decrease_contrast(self, decrease_value):
        self._microscope.beam.contrast -= decrease_value * self.p_decrease_contrast

    def increase_contrast(self, increase_value):
        self._microscope.beam.contrast += increase_value * self.p_increase_contrast

    def decrease_brightness(self, decrease_value):
        self._microscope.beam.brighness -= decrease_value * self.p_brightness

    def increase_brightness(self, increase_value):
        self._microscope.beam.brighness += increase_value * self.p_brightness

    def __call__(self, image):
        if self.function == 'acb':
            logging.info('ACB executed')

            # get statistics from image
            saturated, zeroed = image_saturation_info(image)
            image_band = image_bit_dept_band(image)

            # too much saturation and zeoring - decrease contrast
            if saturated > self.allowed_saturation and zeroed > self.allowed_saturation:
                logging.info(f'Contrast lowering needed. Saturated fraction: {saturated}, Zeroed fraction: {zeroed}')
                self.decrease_contrast(max(saturated-self.allowed_saturation, zeroed-self.allowed_saturation))

            # too low contrast
            elif image_band < self.allowed_minimal_band:
                logging.info(f'Contrast increase needed. Used band: {image_band} is lower than allowed minimal band {self.allowed_minimal_band}')
                self.increase_contrast(1 - image_band)

            # too high brightness
            elif saturated > self.allowed_saturation:
                logging.info(f'Brightness lowering needed. Saturated fraction: {saturated} is higher than allowed saturation {self.allowed_saturation}')
                self.decrease_brightness(saturated-self.allowed_saturation)

            # too low brightness
            elif zeroed > self.allowed_saturation:
                logging.info(f'Brightness increase needed. Zeroed fraction: {zeroed} is higher than allowed saturation {self.allowed_saturation}')
                self.increase_brightness(saturated-self.allowed_saturation)
            # ok
            else:
                logging.info(f'Contrast, brightness OK. Saturated fraction: {saturated}, Zeroed fraction: {zeroed}, Used band: {image_band}')

        else:
            logging.info('No acb executed')