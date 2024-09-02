import importlib
import logging
import os

from fibsem_maestro.autofunctions.criteria import Criterion
from fibsem_maestro.tools.email_attention import send_email
from fibsem_maestro.tools.support import Point


class AutofunctionControl:
    def __init__(self, microscope, settings, logging=False, log_dir=None):

        self.af_settings = settings['autofunction']
        self.email_settings = settings['email_settings']
        self.mask_settings = settings['mask']
        self.criterion_settings = settings['criterion_calculation']
        self._microscope = microscope
        self._log_dir = log_dir
        self._logging = logging
        self.af_values = self.af_settings['af_values']
        self.autofunctions = [self.get_autofunction(x) for x in self.af_values]  # list of all autofunctions
        self.scheduler = []
        self.attempts = 0 # number of af attempts (early stopping)

    def get_autofunction(self, af_value):
        # select and init sweeping class according to sweeping_strategy
        sweeping_module = importlib.import_module('fibsem_maestro.autofunctions.sweeping')
        Sweeping = getattr(sweeping_module, af_value['sweeping_strategy'])
        sweeping = Sweeping(self._microscope, af_value)
        # select criterion based on criteria (settings.yaml)
        criterion = Criterion(self.criterion_settings, self.mask_settings, self.criterion_settings, mask=None)
        # select autofunction based on autofunction (settings.yaml)
        autofunction_module = importlib.import_module('fibsem_maestro.autofunctions.autofunction')
        Autofunction = getattr(autofunction_module, af_value['autofunction'])
        return Autofunction(criterion, sweeping, self._microscope, self.af_settings)

    def move_stage_x(self, back=False):
        x = 1 if back else -1
        # Move to focusing area
        if self.af_settings["delta_x"] != 0:
            self._microscope.relative_position(Point(x=self.af_settings['delta_x']*x, y=0))
            logging.info(f"Stage relative move for focusing. dx={self.af_settings['delta_x']*x}")

    def __call__(self, slice_number, image_res):

        # check firing conditions of all autofunctions
        for af in self.autofunctions:
            execute = af['execute']
            af_name = af['variable']
            # Add af to scheduler if condition passed
            if (type(execute) is int and slice_number % execute == 0) or (type(
                    execute) is float and image_res > execute):
                if af not in self.scheduler:
                    self.scheduler.append(af)
                    logging.info(f'{af_name} autofunction added to scheduler')
                else:
                    logging.warning(f'Autofunction {af_name} already executed. It will not be added to the scheduler')

        # if too much number of attempts, send email
        if self.attempts >= self.af_settings['max_attempts']:
            try:
                send_email(self.email_settings['sender'], self.email_settings['receiver'], "Maestro alert!",
                           f"{self.attempts} attempts of AF failed. Acquisition stopped!")
            except Exception as e:
                logging.error("Sending email error. " + repr(e))

            print(f"Number of focusing attempts exceeds allowed level ({self.attempts}).")
            print("Perform manual inspection and press enter")
            input()
            self.af_attempt = 0  # set the first focusing step
            self.scheduler.clear() # clear schedule queue

        # any AF in scheduler in queue
        if len(self.scheduler) > 0:
            self.attempts += 1 # attempts counter
            af = self.scheduler[0]
            af_name = af['variable']

            # Focusing on different area
            self.move_stage_x()
            logging.info(f'Executed autofunction: {af_name}. Attempt no {self.attempts}.')
            # run af
            finished = af()  # run af

            # Moving back from focusing area
            self.move_stage_x(back=True)

            # remove from scheduler if needed
            if finished:
                self.scheduler.pop(0)
                logging.info(f'Autofunction {af_name} finished and removed from scheduler')
            else:
                logging.info(f'Autofunction {af_name} in progress')

            # logging
            if self._logging:
                if af.af_curve_plot is not None:
                    plot_filename = os.path.join(self._log_dir, 'af_curve.png')
                    af.af_curve_plot.savefig(plot_filename)
                if af.mask_plot is not None:
                    mask_filename = os.path.join(self._log_dir, 'mask.png')
                    af.mask_plot.savefig(mask_filename)
                if af.af_line_plot is not None:
                    line_filename = os.path.join(self._log_dir, 'af_line.png')
                    af.af_line_plot.savefig(line_filename)
        else:
            self.attempts = 0 # zero attempts