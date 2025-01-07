import concurrent.futures
import logging
import os

from colorama import Fore, init as colorama_init
import yaml

from fibsem_maestro.autofunctions.autofunction import StepAutoFunction
from fibsem_maestro.autofunctions.autofunction_control import AutofunctionControl
from fibsem_maestro.contrast_brightness.automatic_contrast_brightness import AutomaticContrastBrightness
from fibsem_maestro.error_handler import ErrorHandler
from fibsem_maestro.image_criteria.criteria import Criterion
from fibsem_maestro.mask.masking import MaskingModel
from fibsem_maestro.drift_correction.template_matching import TemplateMatchingDriftCorrection
from fibsem_maestro.microscope_control.microscope import create_microscope
from fibsem_maestro.microscope_control.settings import load_settings, save_settings
from fibsem_maestro.milling.milling import Milling
from fibsem_maestro.tools.dirs_management import make_dirs
from fibsem_maestro.tools.support import Point, find_in_dict, find_in_objects
import fibsem_maestro.logger as log

colorama_init(autoreset=True)  # colorful console

class StoppingFlag:
    def __init__(self, microscope):
        self._stopping_flag = False
        self.microscope = microscope
    def __call__(self):
        if self._stopping_flag:
            logging.warning('Stopping executed')
            self.microscope.electron_beam.stop_acquisition()
            self.microscope.ion_beam.stop_acquisition()
            self._stopping_flag = False
            return True
        else:
            return False

    @property
    def stopping_flag(self):
        return self._stopping_flag

    @stopping_flag.setter
    def stopping_flag(self, value):
        self._stopping_flag = value


class SerialControl:
    def __init__(self, settings_path='settings.yaml'):
        self._stopping_flag = False
        self.image = None  # actual image
        self.image_resolution = 0  # initial image resolution = 0 # initial image res
        self.future = None  # thread for acquisition running
        self.settings_path = settings_path

        self.settings_init()
        # make dirs if needed
        make_dirs(self.dirs_settings)

        self._microscope = self.initialize_microscope()
        self._electron = self._microscope.electron_beam

        self.stopping = StoppingFlag(self._microscope)
        self.error_handler = ErrorHandler(self.settings, self.stopping)

        # events
        self.event_acquisition_start = []
        self.event_acquisition_stop = []

        self._masks = self.initialize_masks()
        self._milling = self.initialize_milling()
        self._autofunctions = self.initialize_autofunctions(self.settings)
        self._acb = self.initialize_acb()
        self._criterion_resolution = self.initialize_criterion_resolution()
        self._criterion_resolution.finalize_thread_func = self.finalize_calculate_resolution
        self._drift_correction = self.initialize_drift_correction()

    def settings_init(self):
        settings = self.read_yaml_settings()
        # read settings
        self.settings = settings
        self.general_settings = settings['general']
        self.fib_settings = settings['milling']
        self.acquisition_settings = settings['acquisition']
        self.dirs_settings = settings['dirs']
        self.microscope_settings = settings['microscope']
        self.image_settings = settings['image']
        self.criterion_calculation_settings = settings['criterion_calculation']
        self.autofunction_settings = settings['autofunction']
        self.contrast_brightness_settings = settings['contrast_brightness']
        self.mask_settings = settings['mask']
        self.email_settings = settings['email']
        self.dc_settings = settings['drift_correction']

        self.library = self.general_settings['library']
        self.additive_beam_shift = self.general_settings['additive_beam_shift']
        self.sem_settings_file = self.general_settings['sem_settings_file']
        self.variables_to_save = self.general_settings['variables_to_save']
        self.error_behaviour = self.general_settings['error_behaviour']

        self.wd_correction = self.acquisition_settings['wd_correction']
        self.y_correction = self.acquisition_settings['y_correction']

        self.dirs_output_images = self.dirs_settings['output_images']
        self.dirs_template_matching = self.dirs_settings['template_matching']

        self.image_name = self.acquisition_settings['image_name']
        self.criterion_name = self.acquisition_settings['criterion_name']
        self.imaging_enabled = self.acquisition_settings['imaging_enabled']

        self.actual_image_settings = find_in_dict(self.image_name, self.image_settings)
        self.actual_criterion = find_in_dict(self.criterion_name, self.criterion_calculation_settings)


        for attr_name, attr_value in vars(self).items():
            if hasattr(attr_name, 'settings_init'):
                logging.info(f'Re-initializing {attr_name}')
                attr_name.settings_init(settings)

    def read_yaml_settings(self):
        with open(self.settings_path, "r") as yamlfile:
            settings = yaml.safe_load(yamlfile)
            print(f'Settings file {self.settings_path} successfully loaded')
        return settings

    def save_yaml_settings(self):
        with open(self.settings_path, "w") as yamlfile:
            yaml.safe_dump(self.settings, yamlfile)
            print(f'Settings file {self.settings_path} successfully saved')

    def initialize_microscope(self):
        """ microscope init"""
        try:
            # return the right class and call initializer
            microscope = create_microscope(self.library)(self.actual_image_settings, self.microscope_settings,
                                                         self.dirs_output_images)

            print('Microscope initialized')
        except Exception as e:
            logging.error("Microscope initialization failed! "+repr(e))
            raise RuntimeError('Microscope initialization failed!') from e
        return microscope

    def initialize_milling(self):
        """ Slicing init """
        try:
            milling = Milling(self._microscope, self.fib_settings)
            print('Milling initialized')
        except Exception as e:
            logging.error("Milling initialization failed! " + repr(e))
            raise RuntimeError("Milling initialization failed!") from e
        return milling

    def initialize_masks(self):
        """ Masking init """
        try:
            # init all masks
            masks = [MaskingModel(m) for m in self.mask_settings]
        except Exception as e:
            logging.error("Mask loading failed!" + repr(e))
            raise RuntimeError("Mask loading failed!") from e
        return masks

    def initialize_autofunctions(self, settings):
        """ autofunction init """
        try:
            autofunctions = AutofunctionControl(self._microscope, settings,
                                                log_dir=self.logger.dirs_log,
                                                masks=self._masks)
            print(f'Autofunctions found: {[x.name for x in autofunctions.autofunctions]}')
        except Exception as e:
            logging.error("Autofunction initialization failed! "+repr(e))
            raise RuntimeError('"Autofunction initialization failed!') from e
        return autofunctions

    def initialize_acb(self):
        """ Auto contrast-brightness init """
        try:
            acb = AutomaticContrastBrightness(self.contrast_brightness_settings, self._microscope, self.logger.log_params,
                                             log_dir=self.logger.dirs_log)
            print('ACB initialized')
        except Exception as e:
            logging.error("ACB initialization failed! " + repr(e))
            raise RuntimeError("ACB initialization failed!") from e
        return acb

    def initialize_criterion_resolution(self):
        """ Resolution measurement init """
        # criterion of resolution calculation of final image - it uses parameters from criterion_calculation settings
        try:
            mask = find_in_objects(self.actual_criterion['mask_name'], self._masks)
            criterion_resolution = Criterion(self.actual_criterion, mask=mask,
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
                                                                   log_dir=self.logger.dirs_log)
            except Exception as e:
                logging.error("Initialization of template matching failed! " + repr(e))
                raise RuntimeError("Initialization of template matching failed!") from e
        else:
            drift_correction = None
            print('No drift correction found')
        return drift_correction

    def check_af_on_acquired_image(self, slice_number):
        # autofunction on acquired image
        aaf = self._autofunctions.active_autofunction
        if aaf is not None and isinstance(aaf, StepAutoFunction):
            logging.info(f'Autofunction on acquired image invoked! {aaf.name}')
            aaf.evaluate_image(self.image_name, slice_number=slice_number)

    def wait_for_af_criterion_calculation(self):
        aaf = self._autofunctions.active_autofunction
        if aaf is not None and isinstance(aaf, StepAutoFunction):
            aaf.wait_to_criterion_calculation()

    def finalize_calculate_resolution(self, resolution, slice_number, **kwargs):
        """ Thread on the end of imaging (parallel with milling)"""
        self.logger.log_params['resolution'] = self.image_resolution
        print(Fore.GREEN + f'Calculated resolution: {self.image_resolution}')
        if hasattr(self, 'image'):
            del self.image

        self.logger.save_log(slice_number)  # save log dict

    def milling(self, slice_number):
        """ Cut slice (with drift correction by fiducial)  """
        try:
            self._milling(slice_number)
        except Exception as e:
            logging.error('Milling error'+repr(e))
            print(Fore.RED + 'Milling failed')
            self.error_handler(e)

    def calculate_resolution(self, slice_number):
        """ Calculate resolution """
        try:
            # go to self.finalize_calculate_resolution on thread finishing
            self.image_resolution = self._criterion_resolution(self.image, slice_number=slice_number,
                                                               separate_thread=True)
        except Exception as e:
            logging.error('Image resolution calculation error. Setting resolution to 0.'+repr(e))
            print(Fore.RED + 'Resolution measurement failed')
            self.image_resolution = 0
            self.error_handler(e)

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
            self.error_handler(e)

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
            self.error_handler(e)

    def autofunction(self, slice_number):
        """" Autofunctions handling """
        try:
            self._autofunctions(slice_number, self.image_resolution)
            if len(self._autofunctions.scheduler) == 0:
                print(Fore.GREEN + 'The autofunction queue is empty.')
            else:
                print(Fore.YELLOW + f'Waiting autofunctions: {[x.name for x in self._autofunctions.scheduler]}')
        except Exception as e:
            logging.error('Autofunction error. '+repr(e))
            print(Fore.RED + 'Autofunction error!')
            self.error_handler(e)

    def auto_contrast_brightness(self, slice_number):
        try:
            self._autofunctions(slice_number, self.image_resolution)
            if len(self._autofunctions.scheduler) == 0:
                print(Fore.GREEN + 'The autofunction queue is empty.')
            else:
                print(Fore.YELLOW + f'Waiting autofunctions: {[x.name for x in self._autofunctions.scheduler]}')
        except Exception as e:
            logging.error('Autofunction error. ' + repr(e))
            print(Fore.RED + 'Autofunction error!')
            self.error_handler(e)

    def acquire(self, slice_number):
        """ Acquire and save image """
        try:
            self._microscope.acquire_image(slice_number)
            print(Fore.GREEN + 'Image acquired')
        except Exception as e:
            logging.error('Image acquisition error. '+repr(e))
            print(Fore.RED + 'Image acquisition failed!')
            self.error_handler(e)

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
                self.error_handler(e)

    def load_sem_settings(self):
        """ Load microscope settings from file and set microscope """
        # set microscope
        try:
            logging.info('Microscope setting loading')
            load_settings(self._microscope, self.sem_settings_file)
            self._microscope.beam = self._electron  # set electron as default beam
            print(Fore.GREEN + 'Microscope settings applied')
        except Exception as e:
            logging.error('Loading of microscope settings failed! ' + repr(e))
            print(Fore.RED + 'Application of microscope settings failed!')
            self.error_handler(e)

    def save_sem_settings(self):
        """ Save microscope settings from file from microscope """
        settings_to_save = self.variables_to_save
        try:
            save_settings(self._microscope,
                          settings=settings_to_save,
                          path=self.sem_settings_file)
            print(Fore.GREEN + 'Microscope settings saved')
        except Exception as e:
            logging.error('Microscope settings saving error! ' + repr(e))
            print(Fore.RED + 'Microscope settings saving failed!')
            self.error_handler(e)

    def stop(self):
        self.stopping.stopping_flag = True

    def run(self, start_slice_number):
        if not self.running:
            # fire start event
            for event_start in self.event_acquisition_start:
                event_start()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                self.future = executor.submit(self.run_async, start_slice_number)
        else:
            logging.warning('Acquisition already running! Attempt to stop')
            self.stop()

    @property
    def running(self):
        return self.future is not None and self.future.running()

    def run_async(self, start_slice_number):
        slice_number = start_slice_number
        while self.cycle(slice_number):
            logging.info(f'---Slice {slice_number} completed ---')

        # remove logger of current slice
        if self.logger is not None:
            del self.logger

        # fire stop event
        for event_stop in self.event_acquisition_stop:
            event_stop()

    def cycle(self, slice_number):
        # wait for resolution calculation if needed anf AF main imaging criterion calculation
        self._criterion_resolution.join_all_threads()
        self.wait_for_af_criterion_calculation()
        if self.stopping():
            return False
        self.settings_init()  # read settings.yaml and reinit all
        print(Fore.YELLOW + f'Current slice number: {slice_number}')
        logging.info(f'Current slice number: {slice_number}')

        del log.logger
        log.logger = log.Logger(self.settings, self.microscope, slice_number)

        if self.imaging_enabled:
            self._microscope.beam = self._microscope.ion_beam  # switch to ions
            self.milling(slice_number)  # FIB milling (slicing)
            if self.stopping():
                return False

            self._microscope.beam = self._microscope.electron_beam  # switch to electrons
            self.load_sem_settings()  # load settings and set microscope
            if self.stopping():
                return False
            self.correction()  # wd and y correction
            if self.stopping():
                return False
            self.autofunction(slice_number)  # autofunctions handling
            if self.stopping():
                return False
            self.logger.log_microscope_settings()  # save microscope settings
            self.acquire(slice_number)  # acquire image
            if self.stopping():
                return False
            self.check_af_on_acquired_image(slice_number)  # check if the autofunction on main_imaging is activated
            if self.stopping():
                return False
            self.drift_correction(slice_number)  # drift correction
            if self.stopping():
                return False
            self.auto_contrast_brightness(slice_number)
            if self.stopping():
                return False
            # resolution calculation
            self.calculate_resolution(slice_number)
        else:
            self.logger.log_microscope_settings()  # save microscope settings
            print(Fore.RED + 'Imaging skipped!')
            logging.warning('Imaging skipped because imaging is disabled in configuration!')
        return True


    def change_dir_settings(self, new_dir):
        self.dirs_settings['output_images'] = os.path.join(new_dir, 'images')
        self.dirs_settings['log'] = os.path.join(new_dir, 'logs')
        self.dirs_settings['template_matching'] = os.path.join(new_dir, 'templates')

    @property
    def microscope(self):
        return self._microscope
