from PySide6.QtGui import QPixmap

from GUI.gui_tools import populate_form, serialize_form, create_ImageLabel
from fibsem_maestro.tools.support import Image, ScanningArea, Point


class FibGui:
    def __init__(self, window, fib_settings):
        self.window = window
        self.fib_settings = fib_settings
        self.populate_form()
        self.build_connections()

        self.fiducial_area = ScanningArea(Point(0,0),0,0)
        self.extended_fiducial_area = ScanningArea(Point(0,0),0,0)
        self.milling_area = ScanningArea(Point(0,0),0,0)
        self.milling_mark = ScanningArea(Point(0, 0), 0, 0)

        self.window.fibImageLabel = create_ImageLabel(self.window.fibVerticalLayout)
        self.window.fibImageLabel.rects_to_draw.append((self.fiducial_area, (255, 0, 0))) # RGB color
        self.window.fibImageLabel.rects_to_draw.append((self.extended_fiducial_area, (130, 150, 11)))  # RGB color
        self.window.fibImageLabel.rects_to_draw.append((self.milling_area, (0, 0, 255)))  # RGB color
        self.window.fibImageLabel.rects_to_draw.append((self.milling_mark, (30, 30, 255)))  # RGB color

    def build_connections(self):
        self.window.getFibImagePushButton.clicked.connect(self.getFibImagePushButton_clicked)
        self.window.setFibFiducialPushButton.clicked.connect(self.setFibFiducialPushButton_clicked)
        self.window.setFibAreaPushButton.clicked.connect(self.setFibAreaPushButton_clicked)

    def populate_form(self):
        populate_form(self.fib_settings, layout=self.window.fibFormLayout)

    def serialize_layout(self):
        serialize_form(self.window.fibFormLayout, self.fib_settings)

    def getFibImagePushButton_clicked(self):
        from autoscript_sdb_microscope_client.structures import AdornedImage
        image = Image.from_as(AdornedImage.load('/home/cemcof/Downloads/cell.tif'))
        #image = Image.from_as(AdornedImage.load('D:\ceitec_data\ins - fccb\data\raw\slice_00547_(0).tif'))

        self.window.fibImageLabel.setImage(image)

    def setFibFiducialPushButton_clicked(self):
        self.window.fibImageLabel.reset_zoom_pan()
        self.fiducial_area.update(self.window.fibImageLabel.get_selected_area())  # update fiducial
        pixel_size = self.window.fibImageLabel.image.pixel_size
        border = 0.1e-6 # TODO
        img_shape = self.window.fibImageLabel.image.shape
        left_top, size= self.fiducial_area.to_meters(img_shape, pixel_size)
        extended_fiducial_area = ScanningArea.from_meters(img_shape, pixel_size, left_top.x-border, left_top.y-border,
                                                 size[0]+2*border, size[1]+2*border)  # update extended fiducial area
        self.extended_fiducial_area.update(extended_fiducial_area)

    def setFibAreaPushButton_clicked(self):
        img_shape = self.window.fibImageLabel.image.shape
        self.window.fibImageLabel.reset_zoom_pan()
        self.milling_area.update(self.window.fibImageLabel.get_selected_area())  # update milling are

        # milling area marker
        pos, size = self.milling_area.to_img_coordinates(img_shape)
        direction = -1 # TODO
        if direction > 0:
            pos.y += 10 # move in y
        else:
            pos.y += size[1] - 20
        self.milling_mark.update(ScanningArea.from_image_coordinates(img_shape,pos.x, pos.y, 10,10))
