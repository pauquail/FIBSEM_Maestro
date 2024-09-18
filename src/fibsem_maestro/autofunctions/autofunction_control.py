import importlib
import logging

from fibsem_maestro.autofunctions.criteria import Criterion
from fibsem_maestro.tools.email_attention import send_email
from fibsem_maestro.tools.support import find_in_dict, find_in_objects


class AutofunctionControl:
    """ Initialize all autofunctions, it keep af queue and send emails """
    def __init__(self, microscope, settings, logging_enabled=False, log_dir=None, masks=None):
        # settings
        self.autofunction_settings = settings['autofunction']
        self.email_settings = settings['email']
        self.criterion_settings = settings['criterion_calculation']
        self.imaging_settings = settings['image']

        self.max_attempts = self.autofunction_settings['max_attempts']
        self.email_sender = self.email_settings['sender']
        self.email_receiver = self.email_settings['receiver']
        self.password_file = self.email_settings['password_file']

        self._microscope = microscope
        self._log_dir = log_dir
        self._logging = logging_enabled

        self._masks = masks
        self.af_values = self.autofunction_settings['af_values']
        # list of all autofunctions objects
        self.autofunctions = [self._get_autofunction(x) for x in self.af_values]
        self.scheduler = []  # queue of autofunctions waiting to execute
        self.attempts = 0  # number of af attempts (early stopping)

    def _get_autofunction(self, concrete_af_settings):
        """
        :param concrete_af_settings: Dictionary containing the settings for the given autofunction.
        :return: An instance of the chosen Autofunction class.

        This method retrieves the necessary settings from the provided `concrete_af_settings` dictionary and uses them
        to select and initialize the appropriate sweeping strategy and autofunction classes.
        It returns an instance of the chosen Autofunction class.
        """
        sweeping_strategy = concrete_af_settings['sweeping_strategy']
        mask_name = concrete_af_settings['mask_name']
        image_name = concrete_af_settings['image_name']
        criterion_name = concrete_af_settings['criterion_name']
        autofunction = concrete_af_settings['autofunction']

        # load correct image, criterion and mask settings
        actual_image_settings = find_in_dict(image_name, self.imaging_settings)
        actual_criterion_settings = find_in_dict(criterion_name, self.criterion_settings)
        actual_criterion_mask = find_in_objects(mask_name, self._masks)

        # init sweeping class
        sweeping_module = importlib.import_module('fibsem_maestro.autofunctions.sweeping')
        Sweeping = getattr(sweeping_module, sweeping_strategy)
        sweeping = Sweeping(self._microscope.electron_beam, concrete_af_settings)

        # init criterion class
        criterion = Criterion(actual_criterion_settings, mask=actual_criterion_mask, logging_enabled=self._logging,
                              log_dir=self._log_dir)
        # select autofunction based on autofunction setting (settings.yaml)
        autofunction_module = importlib.import_module('fibsem_maestro.autofunctions.autofunction')
        Autofunction = getattr(autofunction_module, autofunction)

        # pass merged settings (current af_value + autofunction settings)
        merged_settings = {
            **self.autofunction_settings,
            **concrete_af_settings
        }
        return Autofunction(
            criterion, sweeping,
            self._microscope,
            auto_function_settings=merged_settings,
            image_settings=actual_image_settings)

    def _email_attention(self):
        try:
            send_email(self.email_sender, self.email_receiver, "Maestro alert!",
                       f"{self.attempts} attempts of AF failed. Acquisition stopped!")
        except Exception as e:
            logging.error("Sending email error. " + repr(e))
        print(f"Number of focusing attempts exceeds allowed level ({self.attempts}).")
        print("Perform manual inspection and press enter")
        input()

    def save_log_files(self, filename_prefix):
        # logging plots
        if self._logging:
            fig = af.af_curve_plot()
            fig.savefig(filename_prefix+'_af_curve.png')
            if hasattr(af, 'line_focus_plot'):
                fig = af.line_focus_plot()
                fig.savefig(filename_prefix+'_line_focus.png')

    def __call__(self, slice_number, image_resolution, image_for_mask=None):
        """
        Autofunctions handling.
        :param slice_number: the number of the current image slice
        :param image_resolution: the resolution of the image
        :param image_for_mask: an optional image used for masking
        :return: None
        """
        # check firing conditions of all autofunctions
        for af in self.autofunctions:
            # Add af to scheduler if condition passed
            if af.check_firing(slice_number, image_resolution):
                if af not in self.scheduler:
                    self.scheduler.append(af)
                    logging.info(f'{af.name} autofunction added to scheduler')
                else:
                    logging.warning(f'Autofunction {af.name} already executed. It will not be added to the scheduler')

        # if too much number of attempts, send email
        if self.attempts >= self.max_attempts:
            self._email_attention()
            self.af_attempt = 0  # zero attempts
            self.scheduler.clear()  # clear schedule queue

        # any AF in scheduler in queue
        if len(self.scheduler) > 0:
            self.attempts += 1  # attempts counter
            af = self.scheduler[0]

            # Focusing on different area
            af.move_stage_x()
            logging.info(f'Executed autofunction: {af.name}. Attempt no {self.attempts}.')
            # run af
            if af(image_for_mask):  # run af
                # if finished
                self.scheduler.pop(0)  # remove the finished af

            self.save_log_files(self._log_dir + f'/{slice_number:05}/{af.name}')