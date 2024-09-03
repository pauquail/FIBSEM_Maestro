import importlib
import logging
import math
import os
import threading

from colorama import Fore, Style, init as colorama_init
import yaml

from fibsem_maestro.autofunctions.autofunction_control import AutofunctionControl
from fibsem_maestro.autofunctions.criteria import Criterion
from fibsem_maestro.drift_correction.template_matching import TemplateMatchingDriftCorrection
from fibsem_maestro.microscope_control.microscope import create_microscope
from fibsem_maestro.microscope_control.settings import load_settings, save_settings
from fibsem_maestro.tools.dirs_management import make_dirs
from fibsem_maestro.tools.support import Point

colorama_init(autoreset=True) # colorful console

class SerialControl:
    def __init__(self, settings_path = 'settings.yaml'):
        self.image = None # actual image
        self.image_resolution = 0 # initial image resolution = 0 # initial image res
        self._thread = None
        # logging dict (important parameters)
        self.log_params = {}

        with open(settings_path, "r") as yamlfile:
            settings = yaml.safe_load(yamlfile)
            print(f'Settings file {settings_path} successfully loaded')

        self.acquisition_settings = settings['acquisition']
        self.microscope_settings = settings['microscope']
        self.autofunction_settings = settings['autofunction']
        self.email_settings = settings['email']
        self.criterion_calculation_settings = settings['criterion_calculation']
        self.mask_settings = settings['mask']
        self.dc_settings = settings['drift_correction']
        self.dirs_settings = settings['dirs']

        self.logger = logging.getLogger()  # Create a logger object.
        self.logger.setLevel(self.acquisition_settings['log_level'])
        fmt = '%(module)s - %(levelname)s - %(message)s'
        self.logger_formatter = logging.Formatter(fmt)
        self.logging_file_handler = None
        self.set_log_file('init')

        # calculate increments
        imaging_angle = float(self.acquisition_settings["imaging_angle"])
        slice_distance = float(self.acquisition_settings["slice_distance"])
        if imaging_angle == 38: # no stage tilting between milling and imaging
            self.wd_increment = slice_distance / math.cos(math.radians(imaging_angle))  # z correction
            self.y_increment = math.tan(math.radians(imaging_angle)) * slice_distance
        elif imaging_angle == 90:  # stage tilting to 90 degrees imaging angle
            self.wd_increment = slice_distance
            self.y_increment = 0
        else:
            logging.error(f'Invalid imaging angle {imaging_angle} only 38 and 90 are allowed')
            raise ValueError("Invalid value of imaging angle.")

        logging.info(f"wd increment: {self.wd_increment}")
        logging.info(f"y increment: {self.y_increment}")
        print(f'Calculated increments: wd {self.wd_increment}, y {self.y_increment}')

        # make dirs if needed
        make_dirs(self.dirs_settings)

        # microscope init
        try:
            self._microscope = create_microscope(self.acquisition_settings['library'])(self.microscope_settings, self.dirs_settings['output_images']) # return the right class and call initializer
            self._electron = self._microscope.electron_beam
            print('Microscope initialized')
        except Exception as e:
            logging.error("Microscope initialization failed! "+repr(e))
            raise RuntimeError('"Microscope initialization failed!') from e

        # autofunction init
        try:
            self._autofunctions = AutofunctionControl(self._microscope, settings,
                                                      logging_enabled=self.acquisition_settings['log'],
                                                      log_dir=self.dirs_settings['log'])
            print(f'{len(self._autofunctions.af_values)} autofunctions found')
        except Exception as e:
            logging.error("Autofunction initialization failed! "+repr(e))
            raise RuntimeError('"Autofunction initialization failed!') from e

        # criterion of resolution calculation of final image - it uses parameters from criterion_calculation settings
        try:
            self._criterion_resolution = Criterion(self.criterion_calculation_settings, self.mask_settings,
                                                  self.criterion_calculation_settings)
            print(f'Image resolution criterion: {self._criterion_resolution.criterion_func.__name__}')
        except Exception as e:
            logging.error("Initialization of resolution criteria failed! "+repr(e))
            raise RuntimeError("Initialization of resolution criteria failed!") from e

        # drift correction init
        if self.dc_settings['type'] == 'template_matching':
            try:
                self.drift_correction = TemplateMatchingDriftCorrection(self._microscope, self.dc_settings,
                                                                        template_matching_dir=self.dirs_settings['template_matching'],
                                                                        logging_dict=self.log_params,
                                                                        logging_enabled=self.acquisition_settings['log'],
                                                                        log_dir=self.dirs_settings['log'])
            except Exception as e:
                logging.error("Initialization of template matching failed! " + repr(e))
                raise RuntimeError("Initialization of template matching failed!") from e
        else:
            self.drift_correction = None
            print('No drift correction found')

    def set_log_file(self, slice_number):
        # make dir (log/slice_number
        os.makedirs(os.path.join(self.dirs_settings['log'], f'{slice_number}'), exist_ok=True)
        log_filename = os.path.join(self.dirs_settings['log'], f'{slice_number}/app.log')

        # remove last logging file handler
        if self.logging_file_handler is not None:
            self.logger.removeHandler(self.logging_file_handler)
        # set a new logging file handler
        self.logging_file_handler = logging.FileHandler(log_filename)  # Configure the logger to write into a file
        self.logging_file_handler.setFormatter(self.logger_formatter)
        self.logger.addHandler(self.logging_file_handler)  # Add the handler to the logger object

    def separate_thread(self, slice_number):
        self.calculate_resolution()
        self.log_params['resolution'] = self.image_resolution
        del self.image
        self.save_log_dict(slice_number)

    def calculate_resolution(self):
        try:
            self.image_resolution = self._criterion_resolution(self.image)
            print(Fore.GREEN + f'Resolution calculated: {self.image_resolution}')
        except Exception as e:
            logging.error('Image resolution calculation error. Setting resolution to 0.'+repr(e))
            print(Fore.RED + 'Resolution measurement failed')
            self.image_resolution = 0

    def logging_params(self):
        self.log_params['wd'] = self._electron.working_distance
        self.log_params['beam_shift_x'] = self._electron.beam_shift_x
        self.log_params['beam_shift_y'] = self._electron.beam_shift_y
        position = self._microscope.position
        self.log_params['stage_x'] = position.x
        self.log_params['stage_y'] = position.y

    def save_log_dict(self, slice_number):
        with open(os.path.join(self.dirs_settings['log'], f'{slice_number}/log_dict.yaml'), 'w') as f:
            yaml.dump(self.log_params, f, default_flow_style=False)
        self.log_params.clear()

    def imaging(self, slice_number):

        # wait for resolution calculation if needed
        if self._thread is not None:
            self._thread.join()

        print(Fore.YELLOW + f'Current slice number: {slice_number}')

        # set logging file
        if self.acquisition_settings['log']:
            self.set_log_file(slice_number)

        # logging dict (important parameters)
        self.log_params.clear()
        self.log_params['slice_number'] = slice_number

        # set microscope
        try:
            logging.info('Microscope setting loading')
            load_settings(self._microscope, self.acquisition_settings['settings_file'])
            self._microscope.beam = self._electron # set electron as default beam
            print(Fore.GREEN + 'Microscope settings applied')
        except Exception as e:
            logging.error('Loading of microscope settings failed! '+repr(e))
            print(Fore.RED + 'Application of microscope settings failed!')

        # WD increment
        try:
            logging.info('WD increment: '+str(self.wd_increment))
            self._electron.working_distance += self.wd_increment
            print(Fore.GREEN + 'WD correction applied')
        except Exception as e:
            logging.error('Working distance settings failed! '+repr(e))
            print(Fore.RED + 'Working distance settings failed!')

        # y correction
        if self.acquisition_settings['y_correction'] == 'y':
            try:
                logging.info('Y correction: '+str(self.y_increment))
                bs = self._electron.beam_shift
                bs = bs + Point(*self.acquisition_settings['additive_beam_shift'])
                bs = bs + Point(0, self.y_increment)
                self._microscope.beam_shift_with_verification(bs) # check y_increment direction
                print(Fore.GREEN + 'Y correction applied')
            except Exception as e:
                logging.error('Y correction failed! '+repr(e))
                print(Fore.RED + 'Y correction failed!')

        # autofunctions
        try:
            self._autofunctions(slice_number, self.image_resolution)
            if len(self._autofunctions.scheduler) == 0:
                print(Fore.GREEN + 'No autofunction')
            else:
                print(Fore.YELLOW + f'Current autofunctions: {self._autofunctions.scheduler}')
        except Exception as e:
            logging.error('Autofunction error. '+repr(e))
            print(Fore.RED + 'Autofunction error!')

        # acquire image
        self.logging_params()
        try:
            self.image = self._microscope.acquire_image(slice_number)
            print(Fore.GREEN + 'Image acquired')
        except Exception as e:
            logging.error('Image acquisition error. '+repr(e))
            print(Fore.RED + 'Image acquisition failed!')

        # drift correction
        if self.drift_correction is not None:
            try:
                self.drift_correction(self.image, slice_number)
                print(Fore.GREEN + 'Drift correction applied')
            except Exception as e:
                logging.error('Drift correction error. ' + repr(e))
                print(Fore.RED + 'Application of drift correction failed!')

        # resolution calculation (separate thread)
        self._thread = threading.Thread(target=self.separate_thread, args=[slice_number])
        self._thread.start()

        # save settings
        try:
            save_settings(self._microscope,
                          settings=self.acquisition_settings['variables_to_save'],
                          path=self.acquisition_settings['settings_file'])
            print(Fore.GREEN + 'Microscope settings saved')
        except Exception as e:
            logging.error('Microscope settings saving error! ' + repr(e))
            print(Fore.RED + 'Microscope settings saving failed!')