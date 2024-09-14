import logging
import os
import threading

from colorama import Fore, Style, init as colorama_init
import yaml

from fibsem_maestro.autofunctions.autofunction_control import AutofunctionControl
from fibsem_maestro.autofunctions.criteria import Criterion
from fibsem_maestro.autofunctions.masking import Masking
from fibsem_maestro.drift_correction.template_matching import TemplateMatchingDriftCorrection
from fibsem_maestro.microscope_control.microscope import create_microscope
from fibsem_maestro.microscope_control.settings import load_settings, save_settings
from fibsem_maestro.tools.dirs_management import make_dirs
from fibsem_maestro.tools.support import Point, find_in_dict, find_in_objects

colorama_init(autoreset=True)  # colorful console


class SerialControlLogger:
    def __init__(self, microscope, log_level, dirs_log, log_enabled):
        self.dirs_log = dirs_log
        self.log_enabled = log_enabled
        self._microscope = microscope
        self._electron = self._microscope.electron_beam
        self.log_params = {}  # logging dict (important parameters to log)
        # logger settings
        self.logger = logging.getLogger()  # Create a logger object.
        self.logger.setLevel(log_level)
        fmt = '%(module)s - %(levelname)s - %(message)s'
        self.logger_formatter = logging.Formatter(fmt)
        self.logging_file_handler = None
        self.set_log_file(0)

    def set_log_file(self, slice_number):
        if self.log_enabled:
            # make dir (log/slice_number
            os.makedirs(os.path.join(self.dirs_log, f'{slice_number:05}'), exist_ok=True)
            log_filename = os.path.join(self.dirs_log, f'{slice_number:05}/app.log')

            # remove last logging file handler
            if self.logging_file_handler is not None:
                self.logger.removeHandler(self.logging_file_handler)
            # set a new logging file handler
            self.logging_file_handler = logging.FileHandler(log_filename)  # Configure the logger to write into a file
            self.logging_file_handler.setFormatter(self.logger_formatter)
            self.logger.addHandler(self.logging_file_handler)  # Add the handler to the logger object

    def reset_log(self, slice_number):
        # logging dict (important parameters)
        self.log_params.clear()
        self.log_params['slice_number'] = slice_number

    def log(self):
        self.log_params['wd'] = self._electron.working_distance
        self.log_params['beam_shift_x'] = self._electron.beam_shift_x
        self.log_params['beam_shift_y'] = self._electron.beam_shift_y
        position = self._microscope.position
        self.log_params['stage_x'] = position.x
        self.log_params['stage_y'] = position.y

    def save_log(self, slice_number):
        with open(os.path.join(self.dirs_log, f'{slice_number:05}/log_dict.yaml'), 'w') as f:
            yaml.dump(self.log_params, f, default_flow_style=False)
        self.log_params.clear()


class SerialControl:
    def __init__(self, settings_path='settings.yaml'):
        self.image = None  # actual image
        self.image_resolution = 0  # initial image resolution = 0 # initial image res
        self._thread = None  # thread on the end of acquisition (for resolution calculation)

        with open(settings_path, "r") as yamlfile:
            settings = yaml.safe_load(yamlfile)
            print(f'Settings file {settings_path} successfully loaded')

        # read settings
        self.acquisition_settings = settings['acquisition']
        self.dirs_settings = settings['dirs']
        self.microscope_settings = settings['microscope']
        self.image_settings = settings['image']
        self.criterion_calculation_settings = settings['criterion_calculation']
        self.autofunction_settings = settings['autofunction']
        self.mask_settings = settings['mask']
        self.email_settings = settings['email']
        self.dc_settings = settings['drift_correction']

        self.library = self.acquisition_settings['library']
        self.wd_correction = self.acquisition_settings['wd_correction']
        self.y_correction = self.acquisition_settings['y_correction']
        self.additive_beam_shift = self.acquisition_settings['additive_beam_shift']
        self.settings_file = self.acquisition_settings['settings_file']
        self.variables_to_save = self.acquisition_settings['variables_to_save']

        self.dirs_output_images = self.dirs_settings['output_images']
        self.dirs_template_matching = self.dirs_settings['template_matching']

        self.image_name = self.microscope_settings['image_name']
        self.criterion_name = self.microscope_settings['criterion_name']

        self.actual_image_settings = find_in_dict(self.image_name, self.image_settings)
        self.actual_criterion = find_in_dict(self.criterion_name, self.criterion_calculation_settings)

        # make dirs if needed
        make_dirs(self.dirs_settings)

        self._microscope = self.initialize_microscope()
        self._electron = self._microscope.electron_beam

        self.logger = SerialControlLogger(self._microscope,
                                          self.acquisition_settings['log_level'],
                                          dirs_log=self.dirs_settings['log'],
                                          log_enabled=self.acquisition_settings['log'])

        self._masks = self.initialize_masks()
        self._autofunctions = self.initialize_autofunctions(settings)
        self._criterion_resolution = self.initialize_criterion_resolution()
        self._drift_correction = self.initialize_drift_correction()

    def initialize_microscope(self):
        """ microscope init"""
        try:
            # return the right class and call initializer
            microscope = create_microscope(self.library)({**self.microscope_settings, **self.actual_image_settings},
                                                         self.dirs_output_images)

            print('Microscope initialized')
        except Exception as e:
            logging.error("Microscope initialization failed! "+repr(e))
            raise RuntimeError('"Microscope initialization failed!') from e
        return microscope

    def initialize_masks(self):
        """ Masking init """
        try:
            # init all masks
            masks = [Masking(m) for m in self.mask_settings]
        except Exception as e:
            logging.error("Mask loading failed! Masks will be omitted. " + repr(e))
            masks = None
        return masks

    def initialize_autofunctions(self, settings):
        """ autofunction init """
        try:
            autofunctions = AutofunctionControl(self._microscope, settings,
                                                logging_enabled=self.logger.log_enabled,
                                                log_dir=self.logger.dirs_log,
                                                masks=self._masks)
            print(f'{len(autofunctions.af_values)} autofunctions found')
        except Exception as e:
            logging.error("Autofunction initialization failed! "+repr(e))
            raise RuntimeError('"Autofunction initialization failed!') from e
        return autofunctions

    def initialize_criterion_resolution(self):
        """ Resolution measurement init """
        # criterion of resolution calculation of final image - it uses parameters from criterion_calculation settings
        try:
            mask = find_in_objects(self.actual_criterion['mask_name'], self._masks)
            criterion_resolution = Criterion(self.actual_criterion, mask=mask, logging_enabled=self.logger.log_enabled,
                                             log_dir=self.logger.dirs_log)
            print(f'Image resolution criterion: {criterion_resolution.criterion_name}')
        except Exception as e:
            logging.error("Initialization of resolution criteria failed! " + repr(e))
            raise RuntimeError("Initialization of resolution criteria failed!") from e
        return criterion_resolution

    def initialize_drift_correction(self):
        """" drift correction init """
        if self.dc_settings['type'] == 'template_matching':
            try:
                drift_correction = TemplateMatchingDriftCorrection(self._microscope, self.dc_settings,
                                                                   template_matching_dir=self.dirs_template_matching,
                                                                   logging_dict=self.logger.log_params,
                                                                   logging_enabled=self.logger.log_enabled,
                                                                   log_dir=self.logger.dirs_log)
            except Exception as e:
                logging.error("Initialization of template matching failed! " + repr(e))
                raise RuntimeError("Initialization of template matching failed!") from e
        else:
            drift_correction = None
            print('No drift correction found')
        return drift_correction

    def separate_thread(self, slice_number):
        """ Thread on the end of imaging (parallel with milling)"""
        self.calculate_resolution(slice_number)
        self.logger.log_params['resolution'] = self.image_resolution
        del self.image
        self.logger.save_log(slice_number)  # save log dict

    def calculate_resolution(self, slice_number):
        """ Calculate resolution """
        try:
            self.image_resolution = self._criterion_resolution(self.image, slice_number=slice_number)
            print(Fore.GREEN + f'Calculated resolution: {self.image_resolution}')
        except Exception as e:
            logging.error('Image resolution calculation error. Setting resolution to 0.'+repr(e))
            print(Fore.RED + 'Resolution measurement failed')
            self.image_resolution = 0

    def correction(self):
        """ WD and Y correction"""

        # WD increment
        try:
            logging.info('WD increment: '+str(self.wd_correction))
            self._electron.working_distance += self.wd_correction
            print(Fore.GREEN + 'WD correction applied. '+str(self.wd_correction))
        except Exception as e:
            logging.error('Working distance settings failed! '+repr(e))
            print(Fore.RED + 'Working distance settings failed!')

        # y correction + beam shift
        try:
            logging.info('Y correction: '+str(self.y_correction))
            bs = self._electron.beam_shift
            delta_bs = Point(*self.additive_beam_shift) + Point(0, self.y_correction)
            bs = bs + delta_bs
            self._microscope.beam_shift_with_verification(bs)  # check y_increment direction
            print(Fore.GREEN + 'Y correction applied. '+str(delta_bs.to_dict()))
        except Exception as e:
            logging.error('Y correction failed! '+repr(e))
            print(Fore.RED + 'Y correction failed!')

    def autofunction(self, slice_number):
        """" Autofunctions handling """
        try:
            self._autofunctions(slice_number, self.image_resolution)
            if len(self._autofunctions.scheduler) == 0:
                print(Fore.GREEN + 'No autofunction')
            else:
                print(Fore.YELLOW + f'Current autofunctions: {self._autofunctions.scheduler}')
        except Exception as e:
            logging.error('Autofunction error. '+repr(e))
            print(Fore.RED + 'Autofunction error!')

    def acquire(self, slice_number):
        """ Acquire and save image """
        try:
            self.image = self._microscope.acquire_image(slice_number)
            print(Fore.GREEN + 'Image acquired')
        except Exception as e:
            logging.error('Image acquisition error. '+repr(e))
            print(Fore.RED + 'Image acquisition failed!')

    def drift_correction(self, slice_number):
        """ Drift correction handling """
        if self._drift_correction is not None:
            try:
                delta = self._drift_correction(self.image, slice_number)
                # it is drift correction based on masking
                if delta is not None:
                    print(Fore.GREEN + 'Drift correction applied. ' + str(delta.to_dict()))
            except Exception as e:
                logging.error('Drift correction error. ' + repr(e))
                print(Fore.RED + 'Application of drift correction failed!')

    def load_settings(self):
        """ Load microscope settings from file and set microscope """
        # set microscope
        try:
            logging.info('Microscope setting loading')
            load_settings(self._microscope, self.settings_file)
            self._microscope.beam = self._electron  # set electron as default beam
            print(Fore.GREEN + 'Microscope settings applied')
        except Exception as e:
            logging.error('Loading of microscope settings failed! ' + repr(e))
            print(Fore.RED + 'Application of microscope settings failed!')

    def save_settings(self):
        """ Save microscope settings from file from microscope """
        try:
            save_settings(self._microscope,
                          settings=self.variables_to_save,
                          path=self.settings_file)
            print(Fore.GREEN + 'Microscope settings saved')
        except Exception as e:
            logging.error('Microscope settings saving error! ' + repr(e))
            print(Fore.RED + 'Microscope settings saving failed!')

    def imaging(self, slice_number):
        # wait for resolution calculation if needed
        if self._thread is not None:
            self._thread.join()

        print(Fore.YELLOW + f'Current slice number: {slice_number}')

        self.logger.set_log_file(slice_number)  # set logging file (logging output)
        self.logger.reset_log(slice_number)   # set log of important parameters (dict to yaml)

        self.load_settings()  # load settings and set microscope
        self.correction()  # wd and y correction
        self.autofunction(slice_number)  # autofunctions handling
        self.logger.log()  # save settings and params
        self.acquire(slice_number)  # acquire image
        self.drift_correction(slice_number)  # drift correction

        # resolution calculation (separate thread)
        self._thread = threading.Thread(target=self.separate_thread, args=[slice_number])
        self._thread.start()

        self.save_settings()  # save settings
