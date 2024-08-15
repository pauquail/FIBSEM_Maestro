import logging
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

class AutoFunction:
    def __init__(self, criterion_function, sweeping_type, microscope: MicroscopeControl, scan='image', show_plot=True,
                 plot_path=None, **kwargs):
        self.__dict__.update(kwargs)  # save kwargs as properties
        self._sweeping = sweeping_type(microscope=microscope, **kwargs)
        self._scan = scan
        self._microscope = microscope
        self._criterion_function = criterion_function
        self._step_number = 0
        self._show_plot = show_plot
        # init criterion dict (array of values for each variable value
        self._criterion = {}
        for i in range(len(list(self._sweeping.sweep()))):
            self._criterion[i] = []

    def set_value_measure_criterion(self, value):
        logging.info(f'Autofunction setting {self.sweeping_var}: {value}')
        self._sweeping.value = value
        # add settings
        # assert 8b
        if self._scan.lower() == 'image':
            image = self._microscope.grab_image()
        else:
            logging.warning("Invalid scan type")
        criterion = self._criterion_function(image, self.px_size, self.lowest_detail, self.highest_detail)
        self._criterion[value].append(criterion)
        logging.info(f"Criterion value: {self._criterion[value]}")

    def evaluate(self):
        # convert list of criteria to mean values
        self._criterion = {key: np.mean(value_list) for key, value_list in self._criterion.items()}
        best_value = max(self._criterion, key=self._criterion)
        self._sweeping.value = best_value  # set best value
        logging.info(f'Autofunction best value {self.sweeping_var} is {value}.')

        plots = []
        if self._show_plot:
            af_fig = self.show_af_curve()
            plots.append(af_fig)
            if self._scan.lower() == 'line':
                line_fig = self.show_line_focus()
                plots.append(line_fig)

        return best_value, plots

    def __call__(self):
        for s in self._sweeping.sweep():
            self.set_value_measure_criterion(s)
        return self.evaluate()

    def step(self):
        sweep_list = list(self._sweeping.sweep())
        value = sweep_list[self._step_number]
        self.set_value_measure_criterion(value)
        self._step_number += 1
        if self._step_number >= len(sweep_list):
            return self.evaluate()

    def show_af_curve(self):
        try:
            matplotlib.use('TkAgg')
        except:
            print("TkAgg backend cannot be used")
        criteria = list(self._criterion.values())
        values = list(self._criterion.keys())
        plt.ion()
        fig = plt.figure()
        plt.plot(values, criteria , 'r.')
        plt.axvline(x=values[len(values) // 2], color='b')  # make horizontal line in the middle
        plt.tight_layout()
        fig.canvas.draw()
        fig.canvas.flush_events()
        return fig

    def show_line_focus(self, img):
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