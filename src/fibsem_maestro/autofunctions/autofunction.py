import logging
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import time

from fibsem_maestro.autofunctions.criteria import Criterion
from fibsem_maestro.microscope_control.abstract_control import MicroscopeControl
from fibsem_maestro.autofunctions.sweeping import BasicSweeping


class AutoFunction:
    """
    Sets the selected variable and measure criterion.
    It selects the variable with the highest criterion.
    """
    def __init__(self, criterion: Criterion, sweeping: BasicSweeping, microscope,
                 af_settings=None):
        """
        Initializes autofunction.

        :param criterion_function: The function used to determine the criterion value.
        :param sweeping: An instance of the any sweeping class (BasicSweeping, CircularSweeping).
        :param mask: Mask class for smart masking.

        """
        # settings
        self.variable = af_settings['variable']
        self.step_mode = af_settings['step_mode']
        self.execute = af_settings['execute']
        self.af_name = af_settings['name']

        self._sweeping = sweeping
        self._microscope = microscope
        self._criterion = criterion
        self._step_number = 0
        # init criterion dict (array of values for each variable value
        self._criterion_values = {}
        for i in range(len(list(self._sweeping.sweep()))):
            self._criterion_values[i] = []

        self.af_curve_plot = None
        self.masks_plot = None

    def _get_image(self, value):
        """
        Sets the value, take image and measure criterion.

        :param value: The new value for the measure criterion.
        :return: None
        """
        logging.info(f'Autofunction setting {self.variable} to {value}')
        self._sweeping.value = self.variable

        # settings
        image = self._microscope.beam.grab_frame()

        #  update mask if step mode active and masking enabled
        if self._criterion.mask_used is not None:
            self._criterion.mask.set_mask(image)
            logging.debug('Mask updated')

        criterion = self._criterion(image)

        if criterion is not None:
            self._criterion_values[value].append(criterion)
        else:
            logging.warning('Criterion omitted')

        logging.info(f"Criterion value: {self._criterion_values[value]}")

    def _evaluate(self):
        """
        This method is used to evaluate the criteria and determine the best value. It also generates plots if required.

        :return: A tuple containing the best value and a list of plots (if generated).
        """
        # convert list of criteria to mean values
        self._criterion_values = {key: np.mean(value_list) for key, value_list in self._criterion_values.items()}
        best_value = max(self._criterion_values, key=self._criterion_values)
        self._sweeping.value = best_value  # set best value
        sweeping_var = self.variable
        logging.info(f'Autofunction best value {sweeping_var} is {best_value}.')

        self.af_curve_plot = self.show_af_curve()

    def __call__(self):
        """
        Perform all steps of setting values, grab images (or line) and criteria measurement.

        :return:
        """
        # non-step image mode
        if not self.step_mode:
            for s in self._sweeping.sweep():
                self._get_image(s)
            self._evaluate()
            return True # af finished
        else:
            # step image mode
            sweep_list = list(self._sweeping.sweep())
            value = sweep_list[self._step_number]  # select sweeping variable based on current step
            self._get_image(value)
            self._step_number += 1
            if self._step_number >= len(sweep_list):
                self._evaluate()
                self._step_number = 0 # restart steps
                return True # af finished
            else:
                return False # not finished yet

    def show_af_curve(self):
        criteria = list(self._criterion_values.values())
        values = list(self._criterion_values.keys())
        fig = plt.figure()
        plt.plot(values, criteria , 'r.')
        plt.axvline(x=values[len(values) // 2], color='b')  # make horizontal line in the middle
        plt.tight_layout()
        return fig

    def check_firing(self, slice_number, image_res):
        execute = self.execute

        return (type(execute) is int and slice_number % execute == 0) or (type(
                execute) is float and image_res > execute)

    @property
    def name(self):
        return self.af_name



class LineAutoFunction(AutoFunction):
    def __init__(self, criterion, sweeping: BasicSweeping, microscope,
                 af_settings=None):
        super().__init__(criterion, sweeping, microscope, af_settings)
        self.pre_imaging_delay = af_settings['pre_imaging_delay']
        self.keep_time = af_settings['keep_time']
        self.forbidden_sections = af_settings['forbidden_sections']

        self._line_focuses = []

    def line_focus(self):
        # grab the image for masking if mask used
        if self._criterion.mask_used:
            self._criterion.mask.update_img(self._microscope.beam)
            logging.debug('New mask grabbed')

        # line time estimation
        line_time = (self._microscope.beam.dwell_time * self._microscope.beam.line_integration
                     * self._microscope.beam.resolution[0])
        self._microscope.beam.blank_screen()

        # variable sweeping
        for step, s in enumerate(self._sweeping.sweep()):
            if step == 0:
                self._microscope.beam.start_acquisition()
            # blank and wait
            self._microscope.total_blank()
            if step == 0:
                time.sleep(self.pre_imaging_delay)
            time.sleep(self.keep_time * line_time)
            # unblank and wait
            self._microscope.total_unblank()
            time.sleep(self.keep_time * line_time)
        self._microscope.beam.stop_acquisition()

        img = self._microscope.beam.get_image().data

        # image processing
        # identify the blank spaces
        xproj = np.sum(img, axis=1)  # identify blank line by min function
        zero_pos = np.where(xproj < 10)[0]  # position of all blank lines
        focus_steps = self._sweeping.items_number()
        # go through the sections
        image_section_index = 0  # actual image section
        for i in range(len(zero_pos) - 1):  # iterate all blank lines - find the image section
            x0 = zero_pos[i]
            x1 = zero_pos[i + 1]  # 2 blank lines
            # if these 2 blank lines are far from each other (it makes the image section)
            if x1 - x0 >= focus_steps:
                if image_section_index not in self.forbidden_sections:
                    bin = np.arange(x0 + 1, x1)  # list of bin indices
                    bin = np.array_split(bin, focus_steps)  # split bins to equal focus_steps parts
                    # go over all variable values
                    for bin_index, focus_criterion in enumerate(self._sweeping.sweep_inner(image_section_index)):
                        # each line
                        for line_index in bin[bin_index]:
                            f = self._criterion(img[line_index], line_index)

                            if f is not None:
                                self._criterion_values[focus_criterion].append(f)
                                self._line_focuses[line_index] = f
                            else:
                                logging.warning('Criterion omitted')
                image_section_index += 1
        # set focus plot
        self.line_focus_plot = self.show_line_focus(img)
        self._evaluate()

    def __call__(self):
        if self.step_mode:
            raise NotImplementedError("Not implemented yet")
        self.line_focus()
        return True # af finished

    def show_line_focus(self, img):
        values_y = list(self._criterion_values.values())
        scale = img.shape[0] / max(values_y)  # scale values to visible range
        values_x = list(self._criterion_values.keys())
        fig = plt.figure(figsize=(10, 5))
        plt.imshow(img, cmap='gray')
        plt.axis('off')
        plt.plot(values_y * scale, values_x, c='r.')
        plt.tight_layout()
        return fig
