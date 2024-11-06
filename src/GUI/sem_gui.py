from PySide6.QtGui import QPixmap

from fibsem_maestro.tools.support import find_in_dict
from gui_tools import populate_form, serialize_form, create_ImageLabel
from fibsem_maestro.tools.support import Image, ScanningArea, Point

class SemGui:
    def __init__(self, window, acquisition_settings, imaging_settings, serial_control):
        self.window = window
        self.acquisition_settings = acquisition_settings
        self.imaging_settings = imaging_settings
        # selected imaging settings
        self.actual_image_settings = find_in_dict(acquisition_settings['image_name'],
                                                  imaging_settings)
        self.serial_control = serial_control
        self.populate_form()
        self.build_connections()

        self.window.imageLabel = create_ImageLabel(self.window.semVerticalLayout)

    def build_connections(self):
        self.window.getImagePushButton.clicked.connect(self.getImagePushButton_clicked)
        self.window.setImagingPushButton.clicked.connect(self.setImagingPushButton_clicked)
        self.window.testImagingPushButton.clicked.connect(self.testImagingPushButton_clicked)


    def populate_form(self):
        populate_form(self.acquisition_settings, excluded_settings=['image_name', 'criterion_name'],
                      layout=self.window.semFormLayout)
        populate_form(self.actual_image_settings, excluded_settings=['name', 'criterion_name'],
                      layout=self.window.imageSettingsFormLayout)

    def serialize_layout(self):
        serialize_form(self.window.semFormLayout, self.acquisition_settings)
        serialize_form(self.window.imageSettingsFormLayout, self.actual_image_settings)

    def getImagePushButton_clicked(self):
        image = self.serial_control.microscope.acquire_image()
        self.window.imageLabel.setImage(image)

    def setImagingPushButton_clicked(self):
        pixel_size = self.window.imageLabel.image.pixel_size
        img_shape = self.window.imageLabel.image.shape
        shift, fov = self.window.imageLabel.get_selected_area().to_meters(img_shape, pixel_size)  # drew image
        shift = shift - Point((img_shape[0]//2)*pixel_size, (img_shape[1]//2)*pixel_size)  # distance to image center
        # apply shift and fov change
        self.serial_control.microscope.beam_shift_with_verification(shift)
        self.serial_control.microscope.electron_beam.resolution = fov
        self.serial_control.save_settings()  # save microscope settings to file
        self.window.imageLabel.rect = QRect()  # clear the rectangle
        image = self.serial_control.microscope.acquire_image()  # update image
        self.window.imageLabel.setImage(image)


    def testImagingPushButton_clicked(self):
        self.serial_control.load_settings()  # load microscope settings from file
        # acquire image and show im imageLabel
        image = self.serial_control.microscope.acquire_image()
        self.window.imageLabel.setImage(image)
