import logging

import numpy as np
from colorama import Fore

from fibsem_maestro.microscope_control.settings import load_settings, save_settings
from fibsem_maestro.tools.image_tools import template_matching
from fibsem_maestro.tools.support import ScanningArea, Point


class Milling:
    def __init__(self, microscope, milling_settings, log_dir=None):
        self._microscope = microscope
        self.settings_init(milling_settings)
        self._log_dir = log_dir

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
        self.milling_enabled = milling_settings['milling_enabled']


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
    def position(self):
        """ Return the edge position (based on mill direction)"""
        return self.milling_area.y if self.direction > 0 else self.milling_area.y + self.milling_area.height

    @property
    def fiducial_with_margin(self):
        return ScanningArea(center = Point(self.fiducial_area.x - self.fiducial_margin, self.fiducial_area.y - self.fiducial_margin),
                            width = self.fiducial_area.width + 2*self.fiducial_margin,
                            height = self.fiducial_area.height + 2*self.fiducial_margin)

    def fiducial_init(self):
        image = np.zeros([self.fiducial_rescan, self.fiducial_with_margin.width, self.fiducial_with_margin.height])
        for i in range(self.fiducial_rescan):
            self._microscope.beam.reduced_scanning = self.fiducial_area
            image[i] = self._microscope.area_scanning()

        width = image[0].shape[0]//2
        height = image[1].shape[1]//2
        dx1, dy1, maxval1 = template_matching(image[0], image[1], width, height)
        dx2, dy2, maxval2 = template_matching(image[1], image[2], width, height)

        if min([maxval1, maxval2]) < 0.9:
            print(Fore.RED, 'Too low ')

    def fiducial_correction(self):
        pass

    def milling(self):
        pass

    def __call__(self):
        if self.milling_enabled:
            self._microscope.beam = self._microscope.ion_beam  # switch to ion
            self.load_settings()  # apply fib settings
            self.milling()
