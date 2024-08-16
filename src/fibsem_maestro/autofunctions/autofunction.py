import logging
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from datetime import time

from fibsem_maestro.microscope_control.abstract_control import MicroscopeControl
from fibsem_maestro.autofunctions.sweeping import BasicSweeping
from fibsem_maestro.tools.support import Imaging


class AutoFunction:
    """
    Sets the selected variable and measure criterion.
    It selects the variable with the highest criterion.
    """
    def __init__(self, criterion_function, sweeping: BasicSweeping, microscope: MicroscopeControl, scan='image',
                 show_plot=True, beam=Imaging.electron, **kwargs):
        """
        Initializes autofunction.

        :param criterion_function: The function used to determine the criterion value.
        :param sweeping: An instance of the any sweeping class (BasicSweeping, CircularSweeping).
        :param microscope: An instance of the MicroscopeControl class.
        :param scan: The scan type to be performed (image, line) (default: 'image').
        :param show_plot: Determines whether to show a plot (default: True).
        :param kwargs: Additional keyword arguments for criterion function.
        :param beam: Select beam for autofunction (Imaging enum).
        """
        self.__dict__.update(kwargs)  # save kwargs as properties
        self._sweeping = sweeping
        self._scan = scan
        self._microscope = microscope
        self._criterion_function = criterion_function
        self._step_number = 0
        self._show_plot = show_plot
        self.beam = self._microscope.beam(beam)
        # init criterion dict (array of values for each variable value
        self._criterion = {}
        for i in range(len(list(self._sweeping.sweep()))):
            self._criterion[i] = []
        if show_plot:
            # init matplotlib
            try:
                matplotlib.use('TkAgg')
            except:
                print("TkAgg backend cannot be used")
            plt.ion()

    def set_value_measure_criterion(self, value):
        """
        Sets the value, take image and measure criterion.

        :param value: The new value for the measure criterion.
        :return: None
        """
        logging.info(f'Autofunction setting {self.sweeping_var}: {value}')
        self._sweeping.value = value
        if self._scan.lower() == 'image':
            image = self._microscope.grab_image()
        else:
            logging.warning("Invalid scan type")
        criterion = self._criterion_function(image, self.px_size, self.lowest_detail, self.highest_detail)
        self._criterion[value].append(criterion)
        logging.info(f"Criterion value: {self._criterion[value]}")

    def evaluate(self):
        """
        This method is used to evaluate the criteria and determine the best value. It also generates plots if required.

        :return: A tuple containing the best value and a list of plots (if generated).
        """
        # convert list of criteria to mean values
        self._criterion = {key: np.mean(value_list) for key, value_list in self._criterion.items()}
        best_value = max(self._criterion, key=self._criterion)
        self._sweeping.value = best_value  # set best value
        logging.info(f'Autofunction best value {self.sweeping_var} is {best_value}.')

        plots = []
        if self._show_plot:
            af_fig = self.show_af_curve()
            plots.append(af_fig)
            if self._scan.lower() == 'line':
                line_fig = self.show_line_focus()
                plots.append(line_fig)

        return best_value, plots

    def line_focus(self):
        # estimate line time
        self.beam.select_modality()  # select quad and beam
        line_time = (self.beam.dwell_time * self.beam.line_integration
                     * self.beam.resolution[0])
        self._microscope.blank_screen()

        for step, s in enumerate(self._sweeping.sweep()):
            if step == 0:
                self.beam.start_acquisition()
            self._microscope.total_blank()
            if step == 0:
                time.sleep(self.pre_imaging_delay)
            time.sleep(self.keep_time * line_time)
            self._microscope.total_unblank()
            time.sleep(self.keep_time * line_time)
        self.beam.stop_acquisition()

        img = self.beam.get_image().data


    def __call__(self):
        """
        Perform all steps of setting values, grab images (or line) and criteria measurement.
        :return:
        """
        self.beam.select_modality()  # select quad and beam

        for s in self._sweeping.sweep():
            self.set_value_measure_criterion(s)
        return self.evaluate()

    def step(self):
        """
        Make a one step forward in setting values, grab image (or line) and measurement of criteria.
        :return:
        """
        assert self._scan.lower() == 'image', "Step autofunction only supports image"
        self.beam.select_modality()  # select quad and beam
        sweep_list = list(self._sweeping.sweep())
        value = sweep_list[self._step_number]
        self.set_value_measure_criterion(value)
        self._step_number += 1
        if self._step_number >= len(sweep_list):
            return self.evaluate()

    def show_af_curve(self):
        criteria = list(self._criterion.values())
        values = list(self._criterion.keys())
        fig = plt.figure()
        plt.plot(values, criteria , 'r.')
        plt.axvline(x=values[len(values) // 2], color='b')  # make horizontal line in the middle
        plt.tight_layout()
        fig.canvas.draw()
        fig.canvas.flush_events()
        return fig

    def show_line_focus(self, img):
        assert self._scan.lower() == 'line', "Line graph is supported only by line mode"
        values = list(self._criterion.keys())
        scale = img.shape[0] / max(values)  # scale values to visible range
        fig = plt.figure(figsize=(10, 5))
        plt.imshow(img, cmap='gray')
        plt.axis('off')
        plt.plot(values * scale, np.arange(0, len(values)), c='r')
        plt.tight_layout()
        fig.canvas.draw()
        fig.canvas.flush_events()
        return fig