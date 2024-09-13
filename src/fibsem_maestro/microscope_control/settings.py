import logging
import ast

from fibsem_maestro.microscope_control.abstract_control import MicroscopeControl


def save_settings(microscope: MicroscopeControl, settings: list, path):
    # populate settings dict with settings names and their values read from microscope
    settings_dict = {}
    for setting in settings:
        try:
            if '.' in setting:
                # inner attribute -> beam setting
                [beam, setting_attribute] = setting.split('.')
                value = getattr(getattr(microscope, beam), setting_attribute)
            else:
                # simple attribute
                value = getattr(microscope, setting)
        except Exception as e:
            logging.error(f'The value {setting} cannot be read from microscope. Setting to None.')
            logging.error(repr(e))
            value = None

        settings_dict[setting] = value
    # write to file
    with open(path, 'w') as f:
        f.write(str(settings_dict))


def load_settings(microscope: MicroscopeControl, path):
    # read settings from file
    with open(path, "r") as f:
        settings_dict = ast.literal_eval(f.read())

    # apply each setting to the microscope
    for setting, value in settings_dict.items():
        try:
            setattr(microscope, setting, value)
        except Exception as e:
            logging.error(f'The value {setting} cannot be set to {value} in microscope')
            logging.error(repr(e))
