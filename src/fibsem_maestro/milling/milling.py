import logging

import numpy as np
from colorama import Fore

from fibsem_maestro.microscope_control.settings import load_settings, save_settings
from fibsem_maestro.tools.image_tools import template_matching
from fibsem_maestro.tools.support import ScanningArea, Point


class Milling:
    def __init__(self, microscope, milling_settings, logging_dict, log_dir):
        self._microscope = microscope
        self.settings_init(milling_settings)
        self.logging_dict = logging_dict
        self._log_dir = log_dir
        self._fiducial_template = None
        self.position = None

    def settings_init(self, milling_settings):
        self.direction = milling_settings['direction']
        self.fiducial_margin = milling_settings['fiducial_margin']
        self.milling_depth = milling_settings['milling_depth']
        self.pattern = milling_settings['pattern']
        self.slice_distance = milling_settings['slice_distance']
        self.variables_to_save = milling_settings['variables_to_save']
        self.settings_file = milling_settings['settings_file']
        self.milling_area = ScanningArea.from_dict(milling_settings['milling_area'])
        self.fiducial_area = ScanningArea.from_dict(milling_settings['fiducial_area'])
        self.fiducial_rescan = milling_settings['fiducial_rescan']
        self.minimal_similarity = milling_settings['minimal_similarity']
        self.milling_enabled = milling_settings['milling_enabled']
        self.fiducial_update = milling_settings['fiducial_update']


    def load_settings(self):
        """ Load microscope settings from file and set microscope for milling """
        # set microscope
        try:
            logging.info('Microscope setting loading (fib)')
            load_settings(self._microscope, self.settings_file)
            self._microscope.beam = self._microscope.beam.ion_beam  # set ion as default beam
            print(Fore.GREEN + 'Microscope fib settings applied')
        except Exception as e:
            logging.error('Loading of microscope fib settings failed! ' + repr(e))
            print(Fore.RED + 'Application of microscope fib settings failed!')

    def save_settings(self):
        """ Save microscope settings from file from microscope for milling"""
        settings_to_save = self.variables_to_save
        try:
            save_settings(self._microscope,
                          settings=settings_to_save,
                          path=self.settings_file)
            print(Fore.GREEN + 'Microscope fib settings saved')
        except Exception as e:
            logging.error('Microscope fib settings saving error! ' + repr(e))
            print(Fore.RED + 'Microscope fib settings saving failed!')

    @property
    def init_position(self):
        """ Return the edge of milling area (based on mill direction)"""
        return self.milling_area.y if self.direction > 0 else self.milling_area.y + self.milling_area.height

    @property
    def fiducial_with_margin(self):
        return ScanningArea(center = Point(self.fiducial_area.x - self.fiducial_margin, self.fiducial_area.y - self.fiducial_margin),
                            width = self.fiducial_area.width + 2*self.fiducial_margin,
                            height = self.fiducial_area.height + 2*self.fiducial_margin)

    def milling_init(self):
        image = np.zeros([self.fiducial_rescan, self.fiducial_area.width, self.fiducial_area.height])
        for i in range(self.fiducial_rescan):
            self._microscope.beam.reduced_scanning = self.fiducial_area
            image[i] = self._microscope.area_scanning()

        width = image[0].shape[0]//2
        height = image[1].shape[1]//2
        dx1, dy1, maxval1 = template_matching(image[0], image[2], width, height)
        dx2, dy2, maxval2 = template_matching(image[1], image[2], width, height)

        if min([maxval1, maxval2]) < self.minimal_similarity:
            print(Fore.RED, 'Fiducial scan failed. Scan similarity is too low.')
            logging.error(f'Fiducial scan failed. Similarity 1-3 is {maxval1} and 2-3 is {maxval2}. '
                          f'Threshold is set to {self.minimal_similarity}')
            self._fiducial_template = None
        else:
            max_rescan_drift = max([abs(dx1), abs(dx2), abs(dy1), abs(dy2)])
            if max_rescan_drift > self.slice_distance:
                print(Fore.RED, 'Fiducial scan failed. Drift is too high.')
                logging.error(f'Fiducial scan failed. Drift is {max_rescan_drift} and slice distance is {self.slice_distance}')
                self._fiducial_template = None
            else:
                self.position = 0
                self._fiducial_template = np.mean(image, axis=0)

    def fiducial_correction(self):
        self._microscope.beam.reduced_scanning = self.fiducial_with_margin
        fiducial_image = self._microscope.area_scanning()
        width = fiducial_image.shape[0] // 2
        height = fiducial_image.shape[1] // 2
        dx, dy, sim = template_matching(fiducial_image, self._fiducial_template, width, height)
        if sim < self.minimal_similarity:
            print(Fore.RED, 'Fiducial localization failed')
            raise exceptions.FiducialLocalizationError('Fiducial localization failed', sim, self._fiducial_template,
                                                       fiducial_image)

        shift_x = dx * fiducial_image.pixel_size * self._microscope.beam.image_to_beam_shift.x
        shift_y = dy * fiducial_image.pixel_size * self._microscope.beam.image_to_beam_shift.y
        logging.info(f'Milling correction: x={shift_x}, y={shift_y}')
        if self._microscope.beam_shift_with_verification(Point(shift_x, shift_y)) == false:  # stage moved
            logging.warning('Stage moved. The fiducial must be rescanned!')
            self.fiducial_correction()

    def milling(self):
        pixel_size = self._fiducial_template.pixel_size
        self.position += self.slice_distance * self.direction
        beam_shift = (self._microscope.ion_beam.beam_shift +
                      Point(0, self.position % pixel_size * self._microscope.ion_beam.image_to_beam_shift.y))
        pattern_shift = self.position - beam_shift
        pattern_position = self.init_position + pattern_shift

        logging.debug('Pattern position: ' + str(pattern_position))
        logging.debug('Beam shift: ' + str(beam_shift))
        self.logging_dict['ion_pattern_position'] = pattern_position
        self.logging_dict['ion_beam_beam_shift'] = beam_shift

        if self._microscope.beam_shift_with_verification(beam_shift) == false:
            logging.error('Beam shift is on limit. Set the new milling position.')
            raise exceptions.FiducialLocalizationError('Beam shift is on limit')

        # set pattern. y: pattern_position check if it is in fov


    def __call__(self):
        if self.milling_enabled:
            self._microscope.beam = self._microscope.ion_beam  # switch to ion
            self.load_settings()  # apply fib settings
            self.milling()
            self.save_settings()
