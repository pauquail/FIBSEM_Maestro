from pathlib import Path
import ast

from fibsem_maestro.microscope_control.abstract_control import MicroscopeControl


def save_settings(microscope: MicroscopeControl, settings: list, path: Path):
    # populate settings dict with settings names and their values
    settings_dict = {}
    for setting in settings:
        value = getattr(microscope, setting)
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
        setattr(microscope, setting, value)
