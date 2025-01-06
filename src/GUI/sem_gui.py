from PySide6.QtCore import QRect
from PySide6.QtGui import QPixmap

from fibsem_maestro.microscope_control.autoscript_control import AutoscriptMicroscopeControl
from fibsem_maestro.tools.dirs_management import findfile
from fibsem_maestro.tools.support import find_in_dict
from gui_tools import populate_form, serialize_form, create_ImageLabel, get_module_members
from fibsem_maestro.tools.support import Image, ScanningArea, Point
from image_label_manger import ImageLabelManagers

class SemGui:
    def __init__(self, window):
        self.window = window
        self.acquisition_settings = self.window.serial_control.acquisition_settings
        self.criterion_settings = self.window.serial_control.criterion_calculation_settings
        self.imaging_settings = self.window.serial_control.image_settings
        self.mask_settings = self.window.serial_control.mask_settings
        # selected imaging settings
        self.actual_image_settings = find_in_dict(self.acquisition_settings['image_name'],
                                                  self.imaging_settings)
        self.actual_criterion_settings = find_in_dict(self.acquisition_settings['criterion_name'],
                                                      self.criterion_settings)
        self.serial_control = self.window.serial_control
        self.populate_form()
        self.build_connections()

        self.window.imageLabel = create_ImageLabel(self.window.semVerticalLayout)

        # add image label to the manager (for multiple image labels control)
        ImageLabelManagers.sem_manager.add_image(self.window.imageLabel)

    def build_connections(self):
        self.window.getImagePushButton.clicked.connect(self.getImagePushButton_clicked)
        self.window.setImagingPushButton.clicked.connect(self.setImagingPushButton_clicked)
        self.window.testImagingPushButton.clicked.connect(self.testImagingPushButton_clicked)


    def populate_form(self):
        populate_form(self.acquisition_settings, layout=self.window.semFormLayout,
                      specific_settings={'image_name':None, 'criterion_name':None})
        populate_form(self.actual_image_settings, layout=self.window.imageSettingsFormLayout,
                      specific_settings={'name':None, 'criterion_name':None})

        masks = ['none', *[x['name'] for x in self.mask_settings]]  # none + masks defined in settings
        criteria = get_module_members('fibsem_maestro.image_criteria.criteria_math', 'func')
        populate_form(self.actual_criterion_settings, layout=self.window.imageCriterionFormLayout,
                      specific_settings={'name': None, 'mask_name': masks, 'criterion': criteria})

    def serialize_layout(self):
        serialize_form(self.window.semFormLayout, self.acquisition_settings)
        serialize_form(self.window.imageSettingsFormLayout, self.actual_image_settings)
        serialize_form(self.window.imageCriterionFormLayout, self.actual_criterion_settings)

    def getImagePushButton_clicked(self):
        # if acquisition running -> get last image
        if self.serial_control.running:
            _, img_filename = findfile(self.serial_control.dirs_output_images)
            # load image if AS is used
            if isinstance(self.serial_control.microscope, AutoscriptMicroscopeControl):
                from autoscript_sdb_microscope_client.structures import AdornedImage
                image = Image.from_as(AdornedImage.load(img_filename))
            else:
                raise NotImplementedError('Image loading of non-autoscript type is not implemented')
        else:
            #image = self.serial_control.microscope.electron_beam.get_image()
            import matplotlib.image as mpimg
            image = mpimg.imread('oxford.jpg')
            image = Image(image, 10e-9)

        ImageLabelManagers.sem_manager.update_image(image)

    def setImagingPushButton_clicked(self):
        """ Set imaging on selected area """
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
        """Acquire image and show im imageLabel"""
        # Load microscope settings from file
        self.serial_control.load_settings()
        applied_images_settings = self.actual_image_settings

        # Fast scan checkbox reduces dwell or LI
        if self.window.fastScanCheckBox.isChecked():
            if applied_images_settings['dwell'] > 200e-9:
                applied_images_settings['dwell'] = 200e-9
            if applied_images_settings['images_line_integration'] > 1:
                applied_images_settings['images_line_integration'] //= 2

        # Apply settings and grab image
        self.serial_control.microscope.apply_beam_settings(applied_images_settings)
        image = self.serial_control.microscope.electron_beam.grab_frame()
        self.window.imageLabel.setImage(image)
