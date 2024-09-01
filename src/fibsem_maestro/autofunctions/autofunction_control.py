import importlib
import logging

from fibsem_maestro.tools.email_attention import send_email
from fibsem_maestro.tools.support import Point


class AutofunctionControl:
    def __init__(self, microscope, af_settings, email_settings):
        self.settings = af_settings
        self.email_settings = email_settings
        self._microscope = microscope

        if self.settings['autofunction'] != 'none':
            # select and init sweeping class according to sweeping_strategy (settings.yaml)
            sweeping_module = importlib.import_module('fibsem_maestro.autofunctions.sweeping')
            Sweeping = getattr(sweeping_module, self.settings['sweeping_strategy'])
            sweeping = Sweeping(self._microscope, self.settings)
            # select criterion based on criteria (settings.yaml)
            criterion_module = importlib.import_module('fibsem_maestro.autofunctions.criteria')
            criterion_func = getattr(criterion_module, self.settings['criterion'])
            # select autofunction based on autofunction (settings.yaml)
            autofunction_module = importlib.import_module('fibsem_maestro.autofunctions.autofunction')
            Autofunction = getattr(autofunction_module, self.settings['autofunction'])
            self._autofunction = Autofunction(criterion_func, sweeping, self._microscope, self.settings)

        self.af_attempt = -1 # current index of autofunction attempts (-1 = no af)

    def __call__(self, slice_number, image_res):
        # autofunction if needed
        global af_attempt
        if self.settings['autofunction'] != 'none':
            # if too much number of attempts, send email
            if self.af_attempt >= len(self.settings['af_values']):
                try:
                    send_email(self.email_settings['sender'], self.email_settings['receiver'], "Maestro alert!",
                               f"{self.af_attempt} attempts of AF failed. Acquisition stopped!")
                except Exception as e:
                    logging.error("Sending email error. " + repr(e))

                print(f"Number of focusing attempts exceeds allowed level ({self.af_attempt}).")
                print("Perform manual inspection and press enter")
                input()
                af_attempt = 0  # set the first focusing step

            # if AF needed
            if (type(self.setting['execute']) is int and slice_number % self.setting['execute'] == 1) or
                (type(self.setting['execute']) is float and image_res > self.setting['execute'])

                af_value = self.settings['af_values'][af_attempt]  # current value to sweep
                logging.info(f'Autofunction needed')

                # Focusing on different area
                # Move to focusing area
                if self.settings["delta_x"] != 0:
                    self._microscope.relative_position(Point(x=self.settings['delta_x'], y=0))
                    logging.info(f"Stage relative move for focusing. dx={self.settings['delta_x']}")

                logging.info(f'Executed autofunction: {af_value}')
                # run af
                self._autofunction()

                # Moving back from focusing area
                self._microscope.relative_position(Point(x=-self.settings['delta_x'], y=0))
                logging.info(f"Stage relative move back. dx={-self.settings['delta_x']}")