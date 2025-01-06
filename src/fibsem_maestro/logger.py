import logging
import os


class SerialControlLogger:


    def save_log(self, slice_number):
        with open(fold_filename(self.dirs_log, slice_number, 'log_dict.yaml'), 'w') as f:
            yaml.dump(self.log_params, f, default_flow_style=False)
        self.log_params.clear()

class Logger:
    def __init__(self, settings, microscope, slice_number):
        self.log_params = {}
        self._microscope = microscope
        self._slice_number = slice_number
        self._electron = self._microscope.electron_beam
        self._ion = self._microscope.ion_beam

        self.settings_init(settings)

        # make dir
        os.makedirs(fold_filename(self.log_dir, slice_number), exist_ok=True)

        # python logger settings
        log_filename = fold_filename(self.log_dir, slice_number, 'app.log')
        self.logger = logging.getLogger()  # Create a logger object.
        fmt = '%(module)s - %(levelname)s - %(message)s'
        self.logger_formatter = logging.Formatter(fmt)
        self.logging_file_handler = logging.FileHandler(log_filename)  # Configure the logger to write into a file
        self.logging_file_handler.setFormatter(self.logger_formatter)
        self.logger.addHandler(self.logging_file_handler)  # Add the handler to the logger object


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
        self.log_params['ion_beam_shift_y'] = self._ion.beam_shift_y
