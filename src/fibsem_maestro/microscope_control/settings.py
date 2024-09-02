import logging
from pathlib import Path
import ast

from fibsem_maestro.microscope_control.abstract_control import MicroscopeControl


def save_settings(microscope: MicroscopeControl, settings: list, path: Path):
    # populate settings dict with settings names and their values read from microscope
    settings_dict = {}
    for setting in settings:
        try:
            value = getattr(microscope, setting)
        except:
            logging.error(f'The value {setting} cannot be read from microscope. Setting to None.')
            value = None

        settings_dict[setting] = value
    # write to file
    with path.open('w') as f:
        f.write(str(settings_dict))


def load_settings(microscope: MicroscopeControl, path: Path):
    # read settings from file
    with path.open('r') as f:
        settings_dict = ast.literal_eval(f.read())

    # apply each setting to the microscope
    for setting, value in settings_dict.items():
        try:
            setattr(microscope, setting, value)
        except:
            logging.error(f'The value {setting} cannot be set to {value} in microscope')
