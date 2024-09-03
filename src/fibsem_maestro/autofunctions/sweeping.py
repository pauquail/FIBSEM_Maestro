import logging
import numpy as np
import math

from fibsem_maestro.tools.support import Point


class BasicSweeping:
    """
    Class for basic linear sweeping of any Microscope attribute.
    """
    def __init__(self, microscope, settings):
        self._microscope = microscope
        self._sweeping_var = settings['variable']
        self._range = settings['sweeping_range']
        self._max_limits = settings['sweeping_max_limits']
        self._steps = int(settings['sweeping_steps'])
        self._total_cycles = int(settings['sweeping_total_cycles'])

        self._base = None # initial sweeping variable
        self.set_sweep()

    @property
    def value(self):
        return getattr(self._microscope, self._sweeping_var)

    @value.setter
    def value(self, value):
        setattr(self._microscope, self._sweeping_var, value)

    def set_sweep(self):
        self._base = self.value

    def sweep_inner(self, repetition):
        """ Basic sweeping"""
        # ensure zig zag manner
        if repetition % 2 == 0:
            sweep_space = np.linspace(self._base - self._range[0], self._base + self._range[1], self._steps)
        else:
            sweep_space = np.linspace(self._base + self._range[1], self._base - self._range[0], self._steps)
        for s in sweep_space:
            if self._max_limits[0] < s < self._max_limits[1]:
                yield s
            else:
                logging.warning(f'Sweep of {self._sweeping_var} if out of range ({s}')

    def sweep(self):
        """
        Performs a sweep of a variable within specified limits.

        :return: A generator object that yields values within the specified limits.
        :rtype: generator object
        """
        for repetition in range(self._total_cycles):
            for s in self.sweep_inner(repetition):
                yield s


    def items_number(self):
        """ Returns the number of items in the sweeping variable. """
        i = 0
        for _ in self.sweep():
            i += 1
        return i

class SpiralSweeping(BasicSweeping):
    def __init__(self, microscope, settings):
        super().__init__(microscope, settings)
        self._step_per_cycle = int(settings['sweeping_steps'])
        self._cycles = int(settings['sweeping_spiral_cycles'])

    def sweep_inner(self, repetition):
        """ Basic sweeping"""
        if repetition % 2 == 0:
            sweep_space = np.arange(self._steps)
        else:
            sweep_space = np.arange(self._steps)[::-1]

        for s in sweep_space:
            cycle_no = s // self._step_per_cycle  # cycle number
            step_no = s % self._step_per_cycle  # step number in the cycle
            radius = (self._range / self._cycles) * (cycle_no + 1)  # avoid zero radius
            angle = (2 * np.pi / self._step_per_cycle) * step_no

            if cycle_no % 2 == 1:  # add angle shift for better covering
                angle += (2 * np.pi / self._step_per_cycle) / 2

            x = np.cos(angle) * radius
            y = np.sin(angle) * radius

            value = self._base + Point(x, y)
            value_r = math.sqrt(value.x ** 2 + value.y ** 2)  # distance from zero (radius)

            if value_r < self._max_limits:
                yield value
            else:
                logging.warning(f'Sweep of {self._sweeping_var} if out of range ({s}')


    def sweep(self):
        """
        Perform a sweeping motion in a spiral pattern, generating a sequence of points.

        :return: A generator that yields the points of the sweeping motion.
        """
        for repetition in range(self._total_cycles):
            for r in self.sweep_inner(repetition):
                yield r