from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QInputDialog

from fibsem_maestro.tools.support import find_in_dict
from gui_tools import populate_form, serialize_form, create_ImageLabel, confirm_action_dialog
from imaging_setting_gui import ImagingSettings

class AutofunctionsGui:
    def __init__(self, window, autofunctions_settings):
        self.window = window
        self.autofunctions_settings = autofunctions_settings
        self.build_connections()

        af_names = [af['name'] for af in autofunctions_settings['af_values']]
        self.window.autofunctionComboBox.addItems(af_names)

    def build_connections(self):
        self.window.newAutofunctionPushButton.clicked.connect(self.newAutofunctionPushButton_clicked)
        self.window.removeAutofunctionPushButton.clicked.connect(self.removeAutofunctionPushButton_clicked)

    def newAutofunctionPushButton_clicked(self):
        text, ok = QInputDialog.getText(self.window, "New autofunction", "Autofunction name: ")

        if ok:
            print(f"You entered: {text}")

    def removeAutofunctionPushButton_clicked(self):
        if confirm_action_dialog():
            pass

    def af_set(self):
        """ Autofunction selected by combo-box"""
        pass
