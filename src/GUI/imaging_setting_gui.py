from PySide6.QtWidgets import QWidget

from GUI.forms.imaging_GUI import Ui_imagingForm
from GUI.gui_tools import populate_form


class ImagingSettings(QWidget, Ui_imagingForm):
    def __init__(self, imaging_settings):
        super().__init__()
        self.setupUi(self)

        self.imaging_settings = imaging_settings
        populate_form(self.imaging_settings, excluded_settings=['name', 'criterion_name'],
                      layout=self.imagingFormLayout)

