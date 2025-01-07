import logging

import numpy as np
from colorama import Fore

from fibsem_maestro.microscope_control.settings import load_settings, save_settings
from fibsem_maestro.tools.image_tools import template_matching
from fibsem_maestro.tools.support import ScanningArea, Point
import fibsem_maestro.logger as log

class Milling:
    def __init__(self, microscope, milling_settings):
        self._microscope = microscope
        self.settings_init(milling_settings)
        self._fiducial_template = None
        self.position = None  # position [m] from milling start edge

    def settings_init(self, milling_settings):
        self.direction = milling_settings['direction']
        self.fiducial_margin = milling_settings['fiducial_margin']
        self.milling_depth = milling_settings['milling_depth']
        self.pattern_file = milling_settings['pattern_file']
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
        """ Return the initial edge of milling area (based on mill direction)"""
        return self.milling_area.y if self.direction > 0 else self.milling_area.y + self.milling_area.height

    @property
    def fiducial_with_margin(self):
        """ Get fiducial area extended by the margin"""
        return ScanningArea(center=Point(self.fiducial_area.x - self.fiducial_margin, self.fiducial_area.y - self.fiducial_margin),
                            width=self.fiducial_area.width + 2*self.fiducial_margin,
                            height=self.fiducial_area.height + 2*self.fiducial_margin)

    def milling_init(self):
        """ Save the milling fiducial """
        image = np.zeros([self.fiducial_rescan, self.fiducial_area.width, self.fiducial_area.height])
        # scan the fiducial several times
        for i in range(self.fiducial_rescan):
            self._microscope.beam.reduced_scanning = self.fiducial_area
            image[i] = self._microscope.area_scanning()

        center_x = image[0].shape[0]//2
        center_y = image[0].shape[1]//2

        # all possible pairs of rescan images (without repetitions)
        pairs = [(a, b) for a in range(self.fiducial_rescan) for b in range(a + 1, self.fiducial_rescan)]
        for a, b in pairs:
            dx, dy, max_val = template_matching(image[a], image[b], center_x, center_y)
            if max_val < self.minimal_similarity:
                print(Fore.RED, f'Fiducial scan failed. Scan similarity between {a + 1}-{b + 1} is too low.')
                logging.error(
                    f'Fiducial scan failed. Similarity {a + 1}-{b + 1} is {max_val}. Threshold is set to {self.minimal_similarity}')
                self._fiducial_template = None
                return
            if max([dx, dy]) > self.slice_distance:
                print(Fore.RED, 'Fiducial scan failed. Drift is too high.')
                logging.error(
                    f'Fiducial scan failed. Drift is {max([dx, dy])} and slice distance is {self.slice_distance}')
                self._fiducial_template = None
                return

        self.position = 0
        # calculate template as mean of images
        self._fiducial_template = np.mean(image, axis=0)
        log.logger.fib_fiducial_template_image = self._fiducial_template  # log image

    def fiducial_correction(self):
        """ Set beam_shift & stage to mill """
        self._microscope.beam.reduced_scanning = self.fiducial_with_margin
        fiducial_image = self._microscope.area_scanning()
        center_x = fiducial_image.shape[0] // 2
        center_y = fiducial_image.shape[1] // 2
        dx, dy, sim, heatmap = template_matching(fiducial_image, self._fiducial_template, center_x, center_y, return_heatmap=True)
        if sim < self.minimal_similarity:
            print(Fore.RED, 'Fiducial localization failed')
            raise RuntimeError(f'Fiducial localization failed. Similarity={sim}')

        # convert shift in the image to the beam shift
        shift_x = dx * fiducial_image.pixel_size * self._microscope.beam.image_to_beam_shift.x
        shift_y = dy * fiducial_image.pixel_size * self._microscope.beam.image_to_beam_shift.y

        logging.info(f'Milling correction: x={shift_x}, y={shift_y}')
        if not self._microscope.beam_shift_with_verification(Point(shift_x, shift_y)):  # stage moved
            logging.warning('Stage moved. The fiducial must be rescanned!')
            self.fiducial_correction()

        log.logger.fib_fiducial_image = fiducial_image  # log image
        log.logger.fib_similarity_map = heatmap
        log.logger.log_params['fib_similarity'] = sim
        log.logger.log_params['fib_driftcorr'] = Point(shift_x, shift_y)


    def milling(self, slice_number: int):
        pixel_size = self._fiducial_template.pixel_size
        # increment milling pattern position by slice distance
        self.position += self.slice_distance * self.direction
        # change beam_shift for subpixel precision of milling
        beam_shift = Point(0, -self.position % pixel_size * self._microscope.ion_beam.image_to_beam_shift.y)
        # final pattern position
        pattern_position = self.init_position + self.position

        logging.debug('Pattern position: ' + str(pattern_position))
        logging.debug('Beam shift: ' + str(beam_shift.y))
        log.logger.log_params['fib_pattern_position'] = pattern_position
        log.logger.log_params['fib_beam_shift'] = beam_shift.y

        if not self._microscope.beam_shift_with_verification(self._microscope.ion_beam.beam_shift + beam_shift):
            print(Fore.RED, 'Beam shift is on the limit')
            raise RuntimeError('Beam shift is on the limit')

        image_shape = self._microscope.ion_beam.resolution
        left_top, size = self.milling_area.to_img_coordinates(image_shape)
        left_top[1] = pattern_position  # modify pattern y
        size[1] = self.slice_distance  # modify height
        milling_rect = ScanningArea.from_image_coordinates(image_shape, left_top[0], left_top[1], size[0], size[1])
        logging.info(f'Milling on position: {milling_rect.to_dict()}')
        direction = 'down' if self.direction < 0 else direction = 'up'
        self._microscope.ion_beam.rectangle_milling(self.pattern_file, rect=milling_rect, depth=self.milling_depth,
                                                    direction=direction)

        # fiducial image rescan
        if slice_number % self.fiducial_update == 0:
            print(Fore.YELLOW, 'Milling fiducial update')
            logging.warning(f'Milling fiducial update on slice {slice_number}')
            self.milling_init()

    def __call__(self, slice_number: int):
        if self.milling_enabled:
            self._microscope.beam = self._microscope.ion_beam  # switch to ion
            self.load_settings()  # apply fib settings
            self.fiducial_correction()  # set beam shift to correct drifts
            self.milling(slice_number)  # pattern milling
            self.save_settings()
