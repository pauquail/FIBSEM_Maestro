from PySide6.QtGui import QPixmap

from fibsem_maestro.tools.support import find_in_dict
from gui_tools import populate_form, serialize_form, create_ImageLabel
from imaging_setting_gui import ImagingSettings

class SemGui:
    def __init__(self, window, acquisition_settings, imaging_settings):
        self.window = window
        self.acquisition_settings = acquisition_settings
        self.imaging_settings = imaging_settings
        self.populate_form()
        self.build_connections()

        self.window.imageLabel = create_ImageLabel(self.window.semVerticalLayout)

        # selected imaging settings
        self.actual_image_settings = find_in_dict(acquisition_settings['image_name'],
                                                  imaging_settings)
        # imaging settings gui
        self.imaging_settings = ImagingSettings(self.actual_image_settings)
        self.window.semImagingVerticalLayout.addWidget(self.imaging_settings)

    def build_connections(self):
        self.window.getImagePushButton.clicked.connect(self.getImagePushButton_clicked)
        self.window.setImagingPushButton.clicked.connect(self.setImagingPushButton_clicked)
        self.window.testImagingPushButton.clicked.connect(self.testImagingPushButton_clicked)


    def populate_form(self):
        populate_form(self.acquisition_settings, excluded_settings=['image_name', 'criterion_name'],
                      layout=self.window.semFormLayout)

    def serialize_layout(self):
        serialize_form(self.window.semFormLayout, self.acquisition_settings)
        serialize_form(self.imaging_settings.imagingFormLayout, self.actual_image_settings)

    def getImagePushButton_clicked(self):
        pixmap = QPixmap('/home/cemcof/Downloads/oxford.jpg')
        self.window.imageLabel.setPixmap(pixmap)

    def setImagingPushButton_clicked(self):
        pass

    def testImagingPushButton_clicked(self):
        pass