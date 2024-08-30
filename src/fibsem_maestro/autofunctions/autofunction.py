import logging
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import time

from fibsem_maestro.autofunctions.criteria import criterion_on_masked_image
from fibsem_maestro.microscope_control.abstract_control import MicroscopeControl
from fibsem_maestro.autofunctions.sweeping import BasicSweeping


class AutoFunction:
    """
    Sets the selected variable and measure criterion.
    It selects the variable with the highest criterion.
    """
    def __init__(self, criterion_function, sweeping: BasicSweeping, beam, scan='image',
                 show_plot=True, mask=None, **kwargs):
        """
        Initializes autofunction.

        :param criterion_function: The function used to determine the criterion value.
        :param sweeping: An instance of the any sweeping class (BasicSweeping, CircularSweeping).
        :param scan: The scan type to be performed (image, line) (default: 'image').
        :param show_plot: Determines whether to show a plot (default: True).
        :param kwargs: Additional keyword arguments for criterion function.
        :param beam: Select beam for autofunction.
        """
        self.__dict__.update(kwargs)  # save kwargs as properties
        self._sweeping = sweeping
        self._scan = scan
        self._beam = beam
        self._criterion_function = criterion_function
        self._step_number = 0
        self._show_plot = show_plot
        self._mask = mask
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

    def _get_image(self, value):
        """
        Sets the value, take image and measure criterion.

        :param value: The new value for the measure criterion.
        :return: None
        """
        logging.info(f'Autofunction setting {self.sweeping_var}: {value}')
        self._sweeping.value = value
        if self._scan.lower() == 'image':
            image = self._beam.grab_image()
        else:
            logging.warning("Invalid scan type")
        if self._mask is not None:
            criterion = self._criterion_function(image, self.px_size, self.lowest_detail, self.highest_detail)
        else:
            criterion = criterion_on_masked_image(image, self._mask, self.min_fraction, self._criterion_function,
                                                  self.px_size, self.lowest_detail, self.highest_detail)
        if criterion is not None:
            self._criterion[value].append(criterion)
        else:
            logging.warning('Criterion omitted')

        logging.info(f"Criterion value: {self._criterion[value]}")

    def _evaluate(self):
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

    def __call__(self, step_mode=False):
        """
        Perform all steps of setting values, grab images (or line) and criteria measurement.

        :param step_mode: Determines whether to perform step mode (it acquires only one image step by step)
        :return:
        """
        self._beam.select_modality()  # select quad and beam

        if self._scan.lower() == 'image':
            # non-step image mode
            if not step_mode:
                for s in self._sweeping.sweep():
                    self._get_image(s)
                return self._evaluate()
            else:
                # step image mode
                sweep_list = list(self._sweeping.sweep())
                value = sweep_list[self._step_number]  # select sweeping variable based on current step
                self._get_image(value)
                self._step_number += 1
                if self._step_number >= len(sweep_list):
                    return self._evaluate()

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

class LineAutoFunction(AutoFunction):
    def line_focus(self):
        # estimate line time
        self._beam.select_modality()  # select quad and beam
        # line time estimation
        line_time = (self._beam.dwell_time * self._beam.line_integration
                     * self._beam.resolution[0])
        self._beam.blank_screen()

        # variable sweeping
        for step, s in enumerate(self._sweeping.sweep()):
            if step == 0:
                self._beam.start_acquisition()
            # blank and wait
            self._beam.total_blank()
            if step == 0:
                time.sleep(self.pre_imaging_delay)
            time.sleep(self.keep_time * line_time)
            # unblank and wait
            self._beam.total_unblank()
            time.sleep(self.keep_time * line_time)
        self._beam.stop_acquisition()

        img = self._beam.get_image().data

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
                if image_section_index not in self.forbiden_sections:
                    bin = np.arange(x0 + 1, x1)  # list of bin indices
                    bin = np.array_split(bin, focus_steps)  # split bins to equal focus_steps parts
                    # go over all variable values
                    for bin_index, focus_criterion in enumerate(self._sweeping.sweep_inner(image_section_index)):
                        # each line
                        for line_index in bin[bin_index]:
                            if self._mask is not None:
                                f = self._criterion_function(img[line_index], self.px_size, self.lowest_detail,
                                                                     self.highest_detail)
                            else:
                                f = criterion_on_masked_image(img[line_index], self._mask, self.min_fraction,
                                                                      self._criterion_function,
                                                                      self.px_size, self.lowest_detail,
                                                                      self.highest_detail)

                            if f is not None:
                                self._criterion[focus_criterion].append(f)
                                self._line_focuses[line_index] = f
                            else:
                                logging.warning('Criterion omitted')
                image_section_index += 1
        return self._evaluate()

    def __call__(self, step_mode=False):
        self._beam.select_modality()  # select quad and beam
        if step_mode:
            raise NotImplementedError("Not implemented yet")
        return self.line_focus()

    def show_line_focus(self, img):
        assert self._scan.lower() == 'line', "Line graph is supported only by line mode"
        values_y = list(self._criterion.values())
        scale = img.shape[0] / max(values_y)  # scale values to visible range
        values_x = list(self._criterion.keys())
        fig = plt.figure(figsize=(10, 5))
        plt.imshow(img, cmap='gray')
        plt.axis('off')
        plt.plot(values_y * scale, values_x, c='r.')
        plt.tight_layout()
        fig.canvas.draw()
        fig.canvas.flush_events()
        return fig
