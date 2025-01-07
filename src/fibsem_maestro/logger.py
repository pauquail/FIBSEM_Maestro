import logging
import os

import numpy as np
import yaml
from matplotlib import pyplot as plt

from fibsem_maestro.tools.support import fold_filename
from fibsem_maestro.autofunctions.autofunction import LineAutoFunction
class AutofocusLog:
    def __init__(self, af, slice_number, log_dir):
        self.af = af
        self.af_name = af.name
        self.curve_image = self.af_curve_image()  # image variable vs criterion
        filename_prefix = fold_filename(log_dir, slice_number, postfix=af.name)
        self.curve_image_filename = filename_prefix + '_af_curve.png'
        self.curve_image.savefig(self.curve_image_filename)  # save image to file
        plt.close(self.curve_image)

        if isinstance(af, LineAutoFunction):
            self.line_image = self.line_focus_image()  # on the fly focusing image
            self.line_image_filename = fold_filename(filename_prefix + '_line_focus.png')
            self.line_image.savefig(self.line_image_filename)
            plt.close(self.line_image)

        self.initial_value = self.af.initial_af_value
        self.final_value = self.af.final_af_value


    def af_curve_image(self):
        """
        Display the AF curve.

        :return: The figure object representing the AF curve plot.
        """
        criteria = list(self.af.criterion_values.values())
        values = list(self.af.criterion_values.keys())
        fig = plt.figure()
        plt.plot(values, criteria, 'r.')
        plt.axvline(x=values[len(values) // 2], color='b')  # make horizontal line in the middle
        plt.tight_layout()
        plt.title('Focus criterion')
        return fig

    def line_focus_image(self):
        """
        :param img: Image array
        :return: Figure object

        Displays an image with a line plot overlay representing focus values.

        The method takes an image array and plots a line representation of focus values
        on top of the image. The focus values are scaled to fit within the visible range
        of the image.
        """
        values_y = np.array(list(self.af.line_focuses.values()))
        values_y -= min(values_y)
        scale = self.af.line_focus_image.shape[1] / max(values_y)  # scale values to visible range
        values_x = list(self.af.line_focuses.keys())
        fig = plt.figure(figsize=(10, 5))
        plt.imshow(self.af.line_focus_image, cmap='gray')
        plt.axis('off')
        plt.plot(values_y * scale, values_x, c='r')
        plt.tight_layout()
        plt.title('Line focus plot')
        return fig

class Logger:
    def __init__(self, settings, microscope, slice_number):
        self.log_params = {}
        self._microscope = microscope
        self._slice_number = slice_number

        if microscope is not None:
            self._electron = self._microscope.electron_beam
            self._ion = self._microscope.ion_beam

        if settings is not None:
            self.settings_init(settings)
        else:
            self.log_dir = ''

        # make dir
        os.makedirs(fold_filename(self.log_dir, slice_number), exist_ok=True)

        # python logger settings
        log_filename = fold_filename(self.log_dir, slice_number, 'app.log')
        self.yaml_log_filaname = fold_filename(self.log_dir, slice_number, 'log_dict.yaml')
        self.logger = logging.getLogger()  # Create a logger object.
        fmt = '%(module)s - %(levelname)s - %(message)s'
        self.logger_formatter = logging.Formatter(fmt)
        self.logging_file_handler = logging.FileHandler(log_filename)  # Configure the logger to write into a file
        self.logging_file_handler.setFormatter(self.logger_formatter)
        self.logger.addHandler(self.logging_file_handler)  # Add the handler to the logger object

        self.fib_fiducial_template_image = None  # fiducial template for milling
        self.fib_fiducial_image = None  # image of milling fiducial
        self.fib_similarity_map = None  # template matching map for fiducial drift measurement

        self.af_curve_images = []  # list of images of autofocus curves

        self.log_af = None  # autofunction log

    def __del__(self):
        # remove logging file handler
        if self.logging_file_handler is not None:
            self.logger.removeHandler(self.logging_file_handler)

    def _settings_init(self, dirs_settings, general_settings):
        self.log_dir = dirs_settings['log']
        self.template_matching_dir = dirs_settings['template_matching']
        self.log_level = general_settings['log_level']

    def settings_init(self, settings):
        """ For global re-initialization of settings  (global settings always passed)"""
        self._settings_init(settings['dirs'], settings['general'])

    def log_microscope_settings(self):
        self.log_params['wd'] = self._electron.working_distance
        self.log_params['beam_shift_x'] = self._electron.beam_shift_x
        self.log_params['beam_shift_y'] = self._electron.beam_shift_y
        self.log_params['stigmator_x'] = self._electron.stigmator_x
        self.log_params['stigmator_y'] = self._electron.stigmator_y
        position = self._microscope.position
        self.log_params['stage_x'] = position.x
        self.log_params['stage_y'] = position.y
        self.log_params['stage_z'] = position.z
        self.log_params['ion_beam_shift_x'] = self._ion.beam_shift_x
        self.log_params['ion_beam_shift_y'] = self._ion.beam_shift_y4

    def save_log(self,):
        """Save yaml dict log to file"""
        with open(self.yaml_log_filaname, 'w') as f:
            yaml.dump(self.log_params, f, default_flow_style=False)

    def create_log_af(self, af):
        self.log_af = AutofocusLog(af, self._slice_number, self.log_dir)

logger = Logger(None, None, 0)  # actual logger. Will be update every cicle