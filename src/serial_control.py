import logging
import math

import yaml

from fibsem_maestro.microscope_control.microscope import create_microscope
from fibsem_maestro.microscope_control.settings import load_settings
from fibsem_maestro.tools.dirs_management import make_dirs
from fibsem_maestro.tools.email_attention import send_email
from fibsem_maestro.tools.support import Point
class SerialControl:
    def __init__(self, settings_path = 'settings.yml'):
        with open(settings_path, "r") as yamlfile:
            settings = yaml.safe_load(yamlfile)

        self.acquisition_settings = settings['acquisition']
        self.autofunction_settings = settings['autofunction']
        self.email_settings = settings['email']

        # calculate increments
        self.wd_increment = self.acquisition_settings["slice_distance"] / math.sin(math.radians(self.acquisition_settings["imaging_angle"]))  # z correction
        self.y_increment = math.tan(math.radians(self.acquisition_settings["imaging_angle"])) * self.acquisition_settings["slice_distance"]
        logging.info(f"wd increment: {self.wd_increment}")
        logging.info(f"y increment: {self.y_increment}")

        # make dirs if needed
        make_dirs(settings['dirs'])

        self._microscope = create_microscope(self.acquisition_settings['microscope']['library'])(self.acquisition_settings['microscope'])
        self._electron = self._microscope.electron_beam

    def imaging(self):
        # set microscope
        try:
            logging.info('Microscope setting loading')
            load_settings(self._microscope, self.acquisition_settings['settings_file'])
            self._microscope.beam = self._electron # set electron as default beam
        except Exception as e:
            logging.error('Loading of microscope settings failed! '+repr(e))

        # WD increment
        try:
            logging.info('WD increment: '+str(self.wd_increment))
            self._electron.working_distance += self.wd_increment
        except Exception as e:
            logging.error('Working distance setting failed! '+repr(e))

        # y correction
        if self.acquisition_settings == 'y':
            try:
                logging.info('Y correction: '+str(self.y_increment))
                bs = Point(*self.acquisition_settings['additive_beamshift'])
                bs = bs + Point(0, self.y_increment)
                self._microscope.beam_shift_with_verification(bs) # check y_increment direction
            except Exception as e:
                logging.error('Y correction failed! '+repr(e))

        # autofunction if needed
        # if too much number of attempts, send email
        if self._microscope.af_attempt >= len(self.autofunction_settings['af_values']):
            try:
                send_email(self.email_settings['sender'], self.email_settings['receiver'], "Maestro alert!",
                           f"{self._microscope.af_attempt} attempts of AF failed. Acquisition stopped!")
            except Exception as e:
                logging.error("Sending email error. "+repr(e))

            print(f"Number of focusing attempts exceeds allowed level ({self._microscope.af_attempt}).")
            print("Perform manual inspection and press enter")
            input()
            self._microscope.af_attempt = 0  # set the first focusing step
        # if AF needed
        if self._microscope.af_attempt > 0:
            af_value = self.autofunction_settings['af_values'][self._microscope.af_attempt]
            logging.info(f'Autofunction needed')

            # Focusing on different area
            # Move to focusing area
            if self.acquisition_settings["delta_x"] != 0:
                self._microscope.relative_position(Point(x=self.autofunction_settings['delta_x'],y=0))
                logging.info(f"Stage relative move for focusing. dx={self.autofunction_settings['delta_x']}")

            logging.info(f'Executed autofunction: {af_value}')
            # run af

            # Moving back from focusing area
            self._microscope.relative_position(Point(x=-self.autofunction_settings['delta_x'], y=0))
            logging.info(f"Stage relative move back. dx={-self.autofunction_settings['delta_x']}")

