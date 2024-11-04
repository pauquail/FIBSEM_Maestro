from PySide6.QtGui import QPixmap

from fibsem_maestro.tools.support import find_in_dict
from gui_tools import populate_form, serialize_form, create_ImageLabel
from imaging_setting_gui import ImagingSettings
from fibsem_maestro.tools.support import Image, ScanningArea, Point

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
        from autoscript_sdb_microscope_client.structures import AdornedImage
        #pixmap = QPixmap('/home/cemcof/Downloads/oxford.jpg')
        image = Image.from_as(AdornedImage.load('/home/cemcof/Downloads/cell.tif'))
        self.window.imageLabel.setImage(image)

    def setImagingPushButton_clicked(self):
        pixel_size = self.window.imageLabel.image.pixel_size
        img_shape = self.window.imageLabel.image.shape
        imaging_area = self.window.imageLabel.get_selected_area().to_meters()

    def testImagingPushButton_clicked(self):
        pass