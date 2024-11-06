from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QInputDialog

from fibsem_maestro.tools.support import find_in_dict
from gui_tools import populate_form, serialize_form, create_ImageLabel, confirm_action_dialog, clear_layout


class AutofunctionsGui:
    def __init__(self, window, autofunctions_settings):
        self.window = window
        self.autofunctions_settings = autofunctions_settings
        self.build_connections()

        af_names = [af['name'] for af in autofunctions_settings['af_values']]
        self.window.autofunctionComboBox.addItems(af_names)
        self.af_set()

    def build_connections(self):
        self.window.cloneAutofunctionPushButton.clicked.connect(self.cloneAutoFunctionPushButton_clicked)
        self.window.removeAutofunctionPushButton.clicked.connect(self.removeAutofunctionPushButton_clicked)
        self.window.autofunctionComboBox.currentIndexChanged.connect(self.autofunctionComboBox_changed)

    def cloneAutoFunctionPushButton_clicked(self):
        text, ok = QInputDialog.getText(self.window, "New autofunction", "Autofunction name: ")

        if ok:
            print(f"You entered: {text}")

    def removeAutofunctionPushButton_clicked(self):
        if confirm_action_dialog():
            pass

    def autofunctionComboBox_changed(self):
        self.af_set()

    def af_set(self):
        """ Autofunction selected by combo-box"""
        selected_af_text = self.window.autofunctionComboBox.currentText()
        selected_af = find_in_dict(selected_af_text, self.autofunctions_settings['af_values'])
        clear_layout(self.window.autofunctionFormLayout)
        populate_form(selected_af, excluded_settings=['name','criterion_name','image_name'],layout=self.window.autofunctionFormLayout)