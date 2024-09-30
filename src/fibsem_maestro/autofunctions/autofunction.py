import logging
import numpy as np
import matplotlib.pyplot as plt
import time

from fibsem_maestro.image_criteria.criteria import Criterion
from fibsem_maestro.autofunctions.sweeping import BasicSweeping
from fibsem_maestro.tools.support import Point
from fibsem_maestro.tools.image_tools import get_stripes

class AutoFunction:
    def __init__(self, criterion: Criterion, sweeping: BasicSweeping, microscope,
                 auto_function_settings, image_settings):
        """
        :param criterion: The focusing criterion instance.
        :param sweeping: The sweeping instance for controlling the sweep process.
        :param microscope: The microscope control instance.
        :param auto_function_settings: The settings for auto function. (af_values setting)
        :param image_settings: The settings for the image. (image setting)
        """
        # settings
        self._initialize_settings(auto_function_settings)
        self._image_settings = image_settings
        self._sweeping = sweeping  # sweeping class
        self._microscope = microscope  # microscope control class
        self._criterion = criterion  # focusing criterion class
        # init criterion dict (array of focusing crit for each variable value)
        self._criterion_values = {}
        self._initialize_criteria_dict()
        self.af_curve_plot = None

    def _initialize_settings(self, auto_function_settings):
        self.name = auto_function_settings['name']
        self.variable = auto_function_settings['variable']
        self.execute = auto_function_settings['execute']
        self.delta_x = auto_function_settings['delta_x']

    def _initialize_criteria_dict(self):
        """
        Initializes the criterion values dictionary.

        :return: None
        """
        self._criterion_values = {i: [] for i in range(len(list(self._sweeping.sweep())))}

    def _prepare(self, image_for_mask=None):
        """ Update mask if needed and set the microscope """
        # grab the image for masking if mask enabled
        if self._criterion.mask_used:
            self._criterion.mask.update_img(image_for_mask)
        self._microscope.apply_beam_settings(self._image_settings)  # apply resolution, li...

    def _get_image(self, value):
        """
        Set the sweeping value, take image and measure criterion.
        :param value: The new value for the measure criterion.
        :return: None
        """
        # set value
        logging.info(f'Autofunction setting {self.variable} to {value}')
        self._sweeping.value = self.variable
        # grab image with defined settings (in self._image_settings). The settings are updated in self._prepare
        image = self._microscope.beam.grab_frame()
        # criterion calculation
        criterion = self._criterion(image)
        if criterion is not None:
            # criterion can be None of not enough masked regions
            self._criterion_values[value].append(criterion)
        else:
            logging.warning('Criterion omitted!')
        logging.info(f"Criterion value: {self._criterion_values[value]}")

    def _evaluate(self):
        """
        This method is used to evaluate the criteria and determine the best value. It also generates plots.
        """
        # convert list of criteria to mean values for each sweeping variable value
        self._criterion_values = {key: np.mean(value_list) for key, value_list in self._criterion_values}
        # find the maximal value
        best_value = max(self._criterion_values, key=self._criterion_values.get)
        self._sweeping.value = best_value  # set best value
        logging.info(f'Autofunction best value {self.variable} is {best_value}.')
        # update af plot
        self.af_curve_plot = self._show_af_curve()

    def _show_af_curve(self):
        """
        Display the AF curve.

        :return: The figure object representing the AF curve plot.
        """
        criteria = list(self._criterion_values.values())
        values = list(self._criterion_values.keys())
        fig = plt.figure()
        plt.plot(values, criteria, 'r.')
        plt.axvline(x=values[len(values) // 2], color='b')  # make horizontal line in the middle
        plt.tight_layout()
        return fig

    def check_firing(self, slice_number, image_resolution):
        """ Check if the firing condition is passed"""
        execute = self.execute
        # if execute (settings) is int - firing according to slice number
        # if execute (settings) is int - firing according to image resolution
        fire = (type(execute) is int and slice_number % execute == 0) or (type(
            execute) is float and image_resolution > execute)
        # do not fire on 0. slice
        if type(execute) is int and slice_number == 1:
            fire = False
        return fire

    def __call__(self, image_for_mask=None):
        """
        :param image_for_mask: The image to be used for masking. Defaults to None.
        :return: True if the af process is finished, False if the process is not yet finished in step image mode.

        The __call__ method is used to execute the functionality of the class. It updates the mask image if needed and
        sets the microscope.
        It performs a sweeping process and evaluates the result.
        In both cases, it returns True if the process is finished and False if the process is not yet finished.
        """
        self._prepare(image_for_mask)  # update mask image if needed and set microscope
        for s in self._sweeping.sweep():
            self._get_image(s)
        self._evaluate()
        return True  # af finished

    def move_stage_x(self, back=False):
        """ Focusing on near area"""
        x = 1 if back else -1
        # Move to focusing area
        if self.delta_x != 0:
            self._microscope.relative_position(Point(x=self.delta_x * x, y=0))
            logging.info(f"Stage relative move for focusing. dx={self.delta_x * x}")

    @property
    def mask(self):
        """ Get mask object if used """
        if self._criterion.mask_used:
            return self._criterion.mask
        else:
            return None


class LineAutoFunction(AutoFunction):
    def __init__(self, criterion, sweeping: BasicSweeping, microscope,
                 auto_function_settings, image_settings):
        super().__init__(criterion, sweeping, microscope, auto_function_settings, image_settings)
        self.pre_imaging_delay = auto_function_settings['pre_imaging_delay']
        self.keep_time = auto_function_settings['keep_time']
        self.forbidden_sections = auto_function_settings['forbidden_sections']
        self.line_focus_plot = None
        self._line_focuses = []

    def _estimate_line_time(self):
        return (self._microscope.beam.dwell_time * self._microscope.beam.line_integration
                * self._microscope.beam.resolution[0])

    def _variable_sweeping(self, line_time):
        """
        Performs line variable sweeping during scan for a given line time.

        :param line_time: the time it takes to acquire a single line of data
        :return: None
        """
        for step, s in enumerate(self._sweeping.sweep()):
            logging.debug(f'Sweep cycle {step}')
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

    def _process_image(self, img):
        """
        It fills self._criterion_values based on given image with sweep value

        :param img: The image to be processed.
        :type img: numpy.ndarray
        :return: None
        """
        focus_steps = len(self._sweeping)
        for image_section_index, bin in get_stripes(img):
            if image_section_index not in self.forbidden_sections:
                    bin = np.array_split(bin, focus_steps)  # split bins to equal parts the equal to focus_steps parts
                    # go over all variable values
                    for bin_index, variable in enumerate(self._sweeping.sweep_inner(image_section_index)):
                        # each line
                        for line_index in bin[bin_index]:
                            f = self._criterion(img[line_index], line_index)

                            if f is not None:
                                self._criterion_values[variable].append(f)
                                self._line_focuses[line_index] = f
                            else:
                                logging.warning('Criterion omitted')

    def _line_focus(self):
        """
        Executes line focus operation.
        It starts scan with variable sweeping and evaluates results
        :return: None
        """
        # line time estimation
        line_time = self._estimate_line_time()
        self._microscope.blank_screen()
        # variable sweeping
        self._variable_sweeping(line_time)
        # get image
        img = self._microscope.beam.get_image().data
        # calculate self._criterion_values
        self._process_image(img)
        # set focus plot
        self.line_focus_plot = self.show_line_focus(img)
        self._evaluate()

    def __call__(self, image_for_mask=None):
        """
        :param image_for_mask: The input image for creating a mask if needed.
        :return: True if the operation is successfully finished.

        """
        assert not self._microscope.beam.extended_resolution, "Line focus cannot work with extended resolution"

        self._prepare(image_for_mask)
        self._line_focus()
        return True  # af finished

    def show_line_focus(self, img):
        """
        :param img: Image array
        :return: Figure object

        Displays an image with a line plot overlay representing focus values.

        The method takes an image array and plots a line representation of focus values
        on top of the image. The focus values are scaled to fit within the visible range
        of the image.
        """
        values_y = list(self._criterion_values.values())
        scale = img.shape[0] / max(values_y)  # scale values to visible range
        values_x = list(self._criterion_values.keys())
        fig = plt.figure(figsize=(10, 5))
        plt.imshow(img, cmap='gray')
        plt.axis('off')
        plt.plot(values_y * scale, values_x, c='r.')
        plt.tight_layout()
        return fig


class StepAutoFunction(AutoFunction):
    def __init__(self, criterion: Criterion, sweeping: BasicSweeping, microscope,
                 auto_function_settings, image_settings):
        super().__init__(criterion, sweeping, microscope, auto_function_settings, image_settings)
        self._step_number = 0  # actual step

    def __call__(self, image_for_mask=None):
        """
        :param image_for_mask: The image to be used for masking. Defaults to None.
        :return: True if the af process is finished, False if the process is not yet finished in step image mode.

        The __call__ method is used to execute the functionality of the class. It updates the mask image if needed and
        sets the microscope.
        It performs a step-by-step process.
        In both cases, it returns True if the process is finished and False if the process is not yet finished.
        """
        self._prepare(image_for_mask)  # update mask image if needed and set microscope

        # step image mode
        sweep_list = list(self._sweeping.sweep())
        value = sweep_list[self._step_number]  # select sweeping variable based on current step
        logging.info(f'Performing autofocus step no. {self._step_number}')
        self._get_image(value)
        self._step_number += 1
        if self._step_number >= len(sweep_list):
            logging.info(f'Step-by-step autofocus finished. Result: {self._criterion_value}')
            self._evaluate()
            self._step_number = 0  # restart steps
            return True  # af finished
        else:
            return False  # not finished yet
