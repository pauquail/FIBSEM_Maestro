from PySide6.QtGui import QPixmap

from fibsem_maestro.tools.support import find_in_dict
from gui_tools import populate_form, serialize_form, create_ImageLabel
from imaging_setting_gui import ImagingSettings

class AutofunctionsGui:
    def __init__(self, window, autofunctions_settings):
        self.window = window
        self.autofunctions_settings = autofunctions_settings
        af_names = [af.name for af in autofunctions_settings]
        self.window.autofunctionComboBox.addItems(af_names)
