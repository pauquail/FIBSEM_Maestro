from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import Qt

from fibsem_maestro.tools.support import find_in_dict
from gui_tools import populate_form, serialize_form
from imaging_setting_gui import ImagingSettings
from image_label import ImageLabel

class SemGui:
    def __init__(self, window, acquisition_settings, imaging_settings):
        self.window = window
        self.acquisition_settings = acquisition_settings
        self.imaging_settings = imaging_settings
        self.populate_form()
        self.build_connections()

        # image label
        self.window.imageLabel = ImageLabel()
        self.window.semVerticalLayout.insertWidget(0, self.window.imageLabel)
        self.window.semVerticalLayout.setAlignment(self.window.imageLabel, Qt.AlignTop | Qt.AlignLeft)
        self.window.imageLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        # selected imaging settings
        self.actual_image_settings = find_in_dict(acquisition_settings['image_name'],
                                                  imaging_settings)
        # imaging settings gui
        self.imaging_settings = ImagingSettings(self.actual_image_settings)
        self.window.semImagingVerticalLayout.addWidget(self.imaging_settings)

    def build_connections(self):
        self.window.getImagePushButton.clicked.connect(self.getImagePushButton_clicked)

    def populate_form(self):
        populate_form(self.acquisition_settings, excluded_settings=['image_name', 'criterion_name'],
                      layout=self.window.semFormLayout)

    def serialize_layout(self):
        serialize_form(self.window.semFormLayout, self.acquisition_settings)
        serialize_form(self.imaging_settings.imagingFormLayout, self.actual_image_settings)

    def getImagePushButton_clicked(self):
        pixmap = QPixmap('/home/cemcof/Downloads/oxford.jpg')
        self.window.imageLabel.setPixmap(pixmap)
