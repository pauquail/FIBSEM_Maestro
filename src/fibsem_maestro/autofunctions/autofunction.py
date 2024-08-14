import logging
import numpy as np
class AutoFunction:
    def __init__(self, criterion_function, sweeping_type, microscope, scan='image', **kwargs):
        self.__dict__.update(kwargs)  # save kwargs as properties
        self._sweeping = sweeping_type(microscope=microscope, **kwargs)
        self._scan = scan
        self._microscope = microscope
        self._criterion_function = criterion_function
        self._step_number = 0
        # init criterion dict (array of values for each variable value
        self._criterion = {}
        for i in range(len(list(self._sweeping.sweep()))):
            self._criterion[i] = []

    def set_value(self, value):
        logging.info(f'Autofunction setting {self.sweeping_var}: {value}')
        self._sweeping.value = value
        if self._scan.lower() == 'image':
            # add settings
            image = self._microscope.grab_image()
        else:
            logging.warning("Invalid scan type")
        criterion = self._criterion_function(image, self.px_size, self.lowest_detail, self.highest_detail)
        self._criterion[value].append(criterion)
        logging.info(f"Criterion value: {self._criterion[value]}")

    def evaluate(self):
        # convert list of criterions to mean values
        self._criterion = {key: np.mean(value_list) for key, value_list in self._criterion.items()}

    def __call__(self):
        for s in self._sweeping.sweep():
            self.set_value(s)
        self.evaluate()

    def step(self):
        sweep_list = list(self._sweeping.sweep())
        value = sweep_list[self._step_number]
        self.set_value(value)
        self._step_number += 1
        if self._step_number >= len(sweep_list):
            self.evaluate()
