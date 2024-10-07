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
        self.sweeping_var = settings['variable']
        self.range = settings['sweeping_range']
        self.max_limits = settings['sweeping_max_limits']
        self.steps = int(settings['sweeping_steps'])
        self.total_cycles = int(settings['sweeping_total_cycles'])

        self._base = None  # initial sweeping variable
        self.set_sweep()

    @property
    def value(self):
        """ Get sweeping variable """
        return getattr(self._microscope, self.sweeping_var)

    @value.setter
    def value(self, value):
        """ Set sweeping variable """
        setattr(self._microscope, self.sweeping_var, value)

    def set_sweep(self):
        """ Set sweeping start point """
        self._base = self.value

    def define_sweep_space(self, repetition):
        # ensure zig zag manner
        if repetition % 2 == 0:
            sweep_space = np.linspace(self._base + self.range[0], self._base + self.range[1],
                                      self.steps)  # self.range[0] is negative
        else:
            sweep_space = np.linspace(self._base + self.range[1], self._base + self.range[0], self.steps)
        return sweep_space

    def sweep_inner(self, repetition):
        """ Basic sweeping"""
        sweep_space = self.define_sweep_space(repetition)
        for s in sweep_space:
            if self.max_limits[0] < s < self.max_limits[1]:
                yield s
            else:
                logging.warning(f'Sweep of {self.sweeping_var} if out of range ({s}')
                # return limit value
                yield self.max_limits[0] if s < self.max_limits[0] else self.max_limits[1]

    def sweep(self):
        """
        Performs a sweep of a variable within specified limits.

        :return: A generator object that yields values within the specified limits.
        :rtype: generator object
        """
        for repetition in range(self.total_cycles):
            logging.info(f'Sweep cycle {repetition} of {self.total_cycles}')
            for s in self.sweep_inner(repetition):
                yield repetition, s


class BasicInterleavedSweeping(BasicSweeping):
    """ Basic sweeping interleaved by base sweeping values """
    def define_sweep_space(self, *args, **kwargs):
        # if no of steps is odd -> remove 1. The base wd must be excluded
        if self.steps % 2 == 1:
            self.steps -= 1

        sweep_space = np.linspace(self._base + self.range[0], self._base + self.range[1], self.steps)  # self.range[0] is negative
        interleave = np.ones(len(sweep_space)) * self._base
        # Merge arrays in interleaved fashion
        merged_arr = np.dstack((interleave, sweep_space)).reshape(-1)
        return merged_arr


class SpiralSweeping(BasicSweeping):
    def __init__(self, microscope, settings):
        super().__init__(microscope, settings)
        self.step_per_cycle = int(settings['sweeping_steps'])
        self.cycles = int(settings['sweeping_spiral_cycles'])

    def sweep_inner(self, repetition):
        """ Basic sweeping"""
        if repetition % 2 == 0:
            sweep_space = np.arange(self.steps)
        else:
            sweep_space = np.arange(self.steps)[::-1]

        for s in sweep_space:
            cycle_no = s // self.step_per_cycle  # cycle number
            step_no = s % self.step_per_cycle  # step number in the cycle
            radius = (self.range / self.cycles) * (cycle_no + 1)  # avoid zero radius
            angle = (2 * np.pi / self.step_per_cycle) * step_no

            if cycle_no % 2 == 1:  # add angle shift for better covering
                angle += (2 * np.pi / self.step_per_cycle) / 2

            x = np.cos(angle) * radius
            y = np.sin(angle) * radius

            value = self._base + Point(x, y)
            value_r = math.sqrt(value.x ** 2 + value.y ** 2)  # distance from zero (radius)

            if value_r < self.max_limits:
                yield value
            else:
                logging.warning(f'Sweep of {self.sweeping_var} if out of range ({s}')

    def sweep(self):
        """
        Perform a sweeping motion in a spiral pattern, generating a sequence of points.

        :return: A generator that yields the points of the sweeping motion.
        """
        for repetition in range(self.total_cycles):
            for r in self.sweep_inner(repetition):
                yield r
