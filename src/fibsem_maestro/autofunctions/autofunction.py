import logging
import numpy as np
import matplotlib.pyplot as plt
import time

from fibsem_maestro.image_criteria.criteria import Criterion
from fibsem_maestro.autofunctions.sweeping import BasicSweeping
from fibsem_maestro.tools.support import Point, fold_filename
from fibsem_maestro.tools.image_tools import get_stripes

class AutoFunction:
    def __init__(self, criterion: Criterion, sweeping: BasicSweeping, microscope,
                 auto_function_settings, image_settings, log_dir=None):
        """
        :param criterion: The focusing criterion instance.
        :param sweeping: The sweeping instance for controlling the sweep process.
        :param microscope: The microscope control instance.
        :param auto_function_settings: The settings for auto function. (af_values setting)
        :param image_settings: The settings for the image. (image setting)
        """
        # settings
        self._settings_init(auto_function_settings)
        self._image_settings = image_settings
        self._sweeping = sweeping  # sweeping class
        self._microscope = microscope  # microscope control class
        self._criterion = criterion  # focusing criterion class
        self._criterion.finalize_thread_func = self.get_image_finalize  # set the function called on resolution calculation (in separated thread)
        # init criterion dict (array of focusing crit for each variable value)
        self._criterion_values = {}
        self.af_curve_plot = None
        self.slice_number = None
        self.last_sweeping_value = None
        self._log_dir = log_dir

    def _settings_init(self, auto_function_settings):
        self.name = auto_function_settings['name']
        self.variable = auto_function_settings['variable']
        self.execute = auto_function_settings['execute']
        self.delta_x = auto_function_settings['delta_x']


    def set_sweep(self):
        self._sweeping.set_sweep()

    def _initialize_criteria_dict(self):
        """
        Initializes the criterion values dictionary.

        :return: None
        """
        self._criterion_values = {i: [] for i in list(self._sweeping.sweep_inner(0))}

    def _prepare(self, image_for_mask=None):
        """ Update mask if needed and set the microscope """
        # grab the image for masking if mask enabled
        if self._criterion.mask_used:
            self._criterion.mask.update_img(image_for_mask)
        self._microscope.apply_beam_settings(self._image_settings)  # apply resolution, li...

    def measure_resolution(self, image, slice_number=None, sweeping_value=None):
        # criterion calculation
        # run on separated thread - call self._get_image_finalize on the end of resolution calculation
        self._criterion(image, slice_number=slice_number, separate_thread=True, sweeping_value=sweeping_value)

    def wait_to_criterion_calculation(self):
        self._criterion.join_all_threads()

    def _get_image(self, value, slice_number=None):
        """
        Set the sweeping value, take image and measure criterion.
        :param value: The new value for the measure criterion.
        :return: None
        """
        # set value
        logging.info(f'Autofunction setting {self.variable} to {value}')
        self.last_sweeping_value = value
        self._sweeping.value = value
        # grab image with defined settings (in self._image_settings). The settings are updated in self._prepare
        image = self._microscope.beam.grab_frame()
        self.measure_resolution(image, slice_number, sweeping_value=value)


    def get_image_finalize(self, resolution, slice_number, **kwargs):
        """ Finalizing function called on the end of resolution calculation thread"""
        # criterion can be None of not enough masked regions
        if resolution is not None:
            self._criterion_values[kwargs['sweeping_value']].append(resolution)
        else:
            logging.warning('Criterion omitted (not enough masked region)!')
        logging.info(f"Criterion value: {resolution}")

    def save_log_files(self, slice_number):
        # logging plots
        if self._logging:
            filename_prefix = fold_filename(self._log_dir, slice_number, postfix=self.name)
            fig = self.af_curve_plot
            fig.savefig(filename_prefix+'_af_curve.png')
            plt.close(fig)
            if hasattr(self, 'line_focus_plot'):
                fig = self.line_focus_plot
                fig.savefig(filename_prefix+'_line_focus.png')
                plt.close(fig)

    def _evaluate(self, slice_number):
        """
        This method is used to evaluate the criteria and determine the best value. It also generates plots.
        """
        self._criterion.join_all_threads()  # wait to complete all resolution calculations

        # convert list of criteria to mean values for each sweeping variable value
        for key, value_list in list(self._criterion_values.items()):
            self._criterion_values[key] = np.mean(value_list)  # find the maximal value
        best_value = max(self._criterion_values, key=self._criterion_values.get)

        self._sweeping.value = best_value  # set best value
        logging.info(f'Autofunction best value {self.variable} is {best_value}.')
        # update af plot
        self.af_curve_plot = self._show_af_curve()
        self.save_log_files(slice_number)  # save af_curve_plot and line_plot

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

        plt.title('Focus criterion')
        return fig

    def check_firing(self, slice_number, image_resolution):
        """ Check if the firing condition is passed"""
        execute = self.execute

        # do not fire if execute = 0
        if execute == 0:
            return False

        # if execute (settings) is int - firing according to slice number
        # if execute (settings) is int - firing according to image resolution
        fire = (type(execute) is int and slice_number % execute == 0) or (type(
            execute) is float and image_resolution > execute)
        # do not fire on 0. slice
        if type(execute) is int and slice_number == 0:
            fire = False
        return fire

    def __call__(self, image_for_mask=None, slice_number=None):
        """
        :param image_for_mask: The image to be used for masking. Defaults to None.
        :return: True if the af process is finished, False if the process is not yet finished in step image mode.

        The __call__ method is used to execute the functionality of the class. It updates the mask image if needed and
        sets the microscope.
        It performs a sweeping process and evaluates the result.
        In both cases, it returns True if the process is finished and False if the process is not yet finished.
        """
        # Focusing on different area
        self._initialize_criteria_dict()
        self.move_stage_x()
        self._prepare(image_for_mask)  # update mask image if needed and set microscope
        for i, (repetition, s) in enumerate(self._sweeping.sweep()):
            logging.info(f'Autofunction step no {i+1}')
            self._get_image(s, slice_number)
        self._evaluate(slice_number)
        self.move_stage_x(back=True)
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
                 auto_function_settings, **kwargs):
        super().__init__(criterion, sweeping, microscope, auto_function_settings, **kwargs)
        self.pre_imaging_delay = auto_function_settings['pre_imaging_delay']
        self.keep_time = auto_function_settings['keep_time']
        self.forbidden_sections = auto_function_settings['forbidden_sections']
        self.line_focus_plot = None
        self._line_focuses = {}

    def _estimate_line_time(self):
        return (self._microscope.beam.dwell_time * self._microscope.beam.line_integration
                * self._microscope.beam.resolution[0])

    def _variable_sweeping(self, line_time):
        """
        Performs line variable sweeping during scan for a given line time.

        :param line_time: the time it takes to acquire a single line of data
        :return: None
        """
        actual_repetition = -1
        for step, (repetition, s) in enumerate(self._sweeping.sweep()):
            self._sweeping.value = s  # set value
            if repetition == 0:
                self._microscope.beam.start_acquisition()

            if not repetition == actual_repetition:
                logging.debug(f'Autofunction sweep cycle {repetition}')
                actual_repetition = repetition
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
        sweeping_steps = self._sweeping.steps
        for image_section_index, bin in get_stripes(img):
            if image_section_index not in self.forbidden_sections:
                    bin = np.array_split(bin, sweeping_steps)  # split bins to equal parts the equal to focus_steps parts
                    # go over all variable values
                    for bin_index, variable in enumerate(self._sweeping.sweep_inner(image_section_index)):
                        # each line
                        for line_index in bin[bin_index]:
                            # Autofunction._get_image_finalize is called be event -> the resolution is appended to self._criterion_values
                            f = self._criterion(img, line_number=line_index, slice_number=self.slice_number,
                                                sweeping_value=variable)

                            if f is not None:
                                self._line_focuses[line_index] = f
                            else:
                                logging.warning('Criterion omitted due to not enough masked regions.')

    def _line_focus(self, slice_number):
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
        img = self._microscope.beam.get_image()
        # calculate self._criterion_values
        self._process_image(img)
        # set focus plot
        self.line_focus_plot = self.show_line_focus(img)
        self._evaluate(slice_number)

    def __call__(self, image_for_mask=None, slice_number=None):
        """
        :param image_for_mask: The input image for creating a mask if needed.
        :return: True if the operation is successfully finished.

        """
        assert not self._microscope.beam.extended_resolution, "Line focus cannot work with extended resolution"
        self._initialize_criteria_dict()
        self.move_stage_x()  # focusing on different area
        self._prepare(image_for_mask)
        self._line_focus(slice_number)
        self.move_stage_x(back=True)
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
        values_y = np.array(list(self._line_focuses.values()))
        values_y -= min(values_y)
        scale = img.shape[1] / max(values_y)  # scale values to visible range
        values_x = list(self._line_focuses.keys())
        fig = plt.figure(figsize=(10, 5))
        plt.imshow(img, cmap='gray')
        plt.axis('off')
        plt.plot(values_y * scale, values_x, c='r')
        plt.tight_layout()
        plt.title('Line focus plot')
        return fig


class StepAutoFunction(AutoFunction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._step_number = 0  # actual step
        self.sweep_list = None

    def __call__(self, *args, **kwargs):
        """
        :param image_for_mask: The image to be used for masking. Defaults to None.
        :return: True if the af process is finished, False if the process is not yet finished in step image mode.

        The __call__ method is used to execute the functionality of the class. It updates the mask image if needed and
        sets the microscope.
        It performs a step-by-step process.
        In both cases, it returns True if the process is finished and False if the process is not yet finished.
        """
        # step image mode
        if self._step_number == 0:
            self.sweep_list = list(self._sweeping.sweep())
            self._initialize_criteria_dict()
        repetition, value = self.sweep_list[self._step_number]  # select sweeping variable based on current step
        logging.info(f'Performing step autofocus no. {self._step_number+1}')
        self.last_sweeping_value = value
        self._sweeping.value = value
        self._step_number += 1

    def _initialize_criteria_dict(self):
        self._criterion_values = {}

    def evaluate_image(self, image, slice_number):
        # new thread -> goto self.
        self.measure_resolution(image, slice_number=slice_number, sweeping_value=self.last_sweeping_value)

        if self._step_number >= len(self.sweep_list):
            self.wait_to_criterion_calculation() # join threads
            logging.info(f'Step-by-step autofocus finished.')
            self._evaluate(slice_number)
            self._step_number = 0  # restart steps
            return True  # af finished
        else:
            return False  # not finished yet

    def get_image_finalize(self, resolution, slice_number, **kwargs):
        """ Finalizing function called on the end of resolution calculation thread"""
        # criterion can be None of not enough masked regions
        if resolution is not None:
            self._criterion_values[self._step_number] = (kwargs['sweeping_value'], resolution)
        else:
            logging.warning('Criterion omitted (not enough masked region)!')
        logging.info(f"Criterion value: {resolution}")

    def _evaluate(self, slice_number):
        """ Evaluate data from all steps. Calculate difference between base resolution and the resolution alternated image"""
        result_dic = {i: [] for i in list(self._sweeping.sweep_inner(0))}
        for i in np.arange(1, len(self._criterion_values), step=2):  # (0,2,4... base resolution)
            sweep_value, sweep_resolution  = self._criterion_values[i]
            _, base_resolution = self._criterion_values[i-1]
            result_dic[sweep_value].append(sweep_resolution - base_resolution)
        self._criterion_values = result_dic
        super()._evaluate(slice_number)