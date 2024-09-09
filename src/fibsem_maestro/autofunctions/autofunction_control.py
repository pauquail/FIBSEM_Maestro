import importlib
import logging
import os

from fibsem_maestro.autofunctions.criteria import Criterion
from fibsem_maestro.tools.email_attention import send_email
from fibsem_maestro.tools.support import Point, find_in_dict, find_in_objects


class AutofunctionControl:
    def __init__(self, microscope, settings, logging_enabled=False, log_dir=None, masks=None):
        # settings
        self.af_settings = settings['autofunction']

        self.email_settings = settings['email']
        self.criterion_settings = settings['criterion_calculation']
        self.imaging_settings = settings['imaging']

        self.max_attempts = self.af_settings['max_attempts']
        self.email_sender = self.email_settings['sender']
        self.email_receiver = self.email_settings['receiver']
        self.password_file = self.email_settings['password_file']
        self.image_name = self.af_settings['image_name']

        self._microscope = microscope
        self._log_dir = log_dir
        self._logging = logging_enabled
        self._masks = masks
        self.af_values = self.af_settings['af_values']
        self.autofunctions = [self.get_autofunction(x) for x in self.af_values]  # list of all autofunctions
        self.scheduler = []
        self.attempts = 0 # number of af attempts (early stopping)

    def get_autofunction(self, concrete_af_settings):
        sweeping_strategy = concrete_af_settings['sweeping_strategy']
        mask_name = concrete_af_settings['mask_name']
        image_name = concrete_af_settings['image_name']
        criterion_name = concrete_af_settings['criterion_name']
        autofunction = concrete_af_settings['autofunction']
        actual_image_settings = find_in_dict(image_name, self.imaging_settings)
        actual_criterion_settings = find_in_dict(criterion_name, self.criterion_settings)
        actual_criterion_mask = find_in_objects(mask_name, self._masks)

        # select and init sweeping class according to sweeping_strategy
        sweeping_module = importlib.import_module('fibsem_maestro.autofunctions.sweeping')
        Sweeping = getattr(sweeping_module, sweeping_strategy)
        sweeping = Sweeping(self._microscope.electron_beam, concrete_af_settings)

        # select criterion based on criteria (settings.yaml)
        criterion = Criterion(actual_criterion_settings, mask=actual_criterion_mask)
        # select autofunction based on autofunction setting (settings.yaml)
        autofunction_module = importlib.import_module('fibsem_maestro.autofunctions.autofunction')
        Autofunction = getattr(autofunction_module, autofunction)
        # pass merged settings (current af_value + autofunction settings)

        return Autofunction(criterion, sweeping, self._microscope, af_settings={**self.af_settings,
                                                                                **concrete_af_settings},
                            image_settings=actual_image_settings)

    def __call__(self, slice_number, image_res):
        # check firing conditions of all autofunctions
        for af in self.autofunctions:
            # Add af to scheduler if condition passed
            if af.check_firing(slice_number, image_res):
                if af not in self.scheduler:
                    self.scheduler.append(af)
                    logging.info(f'{af.name} autofunction added to scheduler')
                else:
                    logging.warning(f'Autofunction {af.name} already executed. It will not be added to the scheduler')

        # if too much number of attempts, send email
        if self.attempts >= self.max_attempts:
            try:
                send_email(self.email_sender, self.email_receiver, "Maestro alert!",
                           f"{self.attempts} attempts of AF failed. Acquisition stopped!")
            except Exception as e:
                logging.error("Sending email error. " + repr(e))

            print(f"Number of focusing attempts exceeds allowed level ({self.attempts}).")
            print("Perform manual inspection and press enter")
            input()
            self.af_attempt = 0  # set the first focusing step
            self.scheduler.clear()  # clear schedule queue

        # any AF in scheduler in queue
        if len(self.scheduler) > 0:
            self.attempts += 1  # attempts counter
            af = self.scheduler[0]

            # Focusing on different area
            af.move_stage_x()
            logging.info(f'Executed autofunction: {af.name}. Attempt no {self.attempts}.')
            # run af
            finished = af()  # run af

            # Moving back from focusing area
            af.move_stage_x(back=True)

            # remove from scheduler if needed
            if finished:
                self.scheduler.pop(0)
                logging.info(f'Autofunction {af.name} finished and removed from scheduler')
            else:
                logging.info(f'Autofunction {af.name} in progress')

            # logging
            if self._logging:
                if af.af_curve_plot is not None:
                    plot_filename = os.path.join(self._log_dir, f'{slice_number:05}/af_curve.png')
                    af.af_curve_plot.savefig(plot_filename)
                if af.mask_plot is not None:
                    mask_filename = os.path.join(self._log_dir, f'{slice_number:05}/mask.png')
                    af.mask_plot.savefig(mask_filename)
                if af.af_line_plot is not None:
                    line_filename = os.path.join(self._log_dir, f'{slice_number:05}/af_line.png')
                    af.af_line_plot.savefig(line_filename)
        else:
            self.attempts = 0 # zero attempts