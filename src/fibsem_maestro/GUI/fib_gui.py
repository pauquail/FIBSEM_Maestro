from fibsem_maestro.GUI.gui_tools import populate_form, serialize_form, create_ImageLabel
from fibsem_maestro.tools.support import Image, ScanningArea, Point


class FibGui:
    def __init__(self, window):
        self.window = window
        self.fib_settings = self.window.serial_control.fib_settings
        self.populate_form()
        self.build_connections()

        self._fiducial_area = ScanningArea(Point(0,0),0,0)
        self._extended_fiducial_area = ScanningArea(Point(0,0),0,0)
        self._milling_area = ScanningArea(Point(0,0),0,0)
        self._milling_mark = ScanningArea(Point(0, 0), 0, 0)

        self.window.fibImageLabel = create_ImageLabel(self.window.fibVerticalLayout)
        self.window.fibImageLabel.rects_to_draw.append((self._fiducial_area, (255, 0, 0))) # RGB color
        self.window.fibImageLabel.rects_to_draw.append((self._extended_fiducial_area, (130, 150, 11)))  # RGB color
        self.window.fibImageLabel.rects_to_draw.append((self._milling_area, (0, 0, 255)))  # RGB color
        self.window.fibImageLabel.rects_to_draw.append((self._milling_mark, (30, 30, 255)))  # RGB color

    def build_connections(self):
        self.window.getFibImagePushButton.clicked.connect(self.getFibImagePushButton_clicked)
        self.window.setFibFiducialPushButton.clicked.connect(self.setFibFiducialPushButton_clicked)
        self.window.setFibAreaPushButton.clicked.connect(self.setFibAreaPushButton_clicked)

    def populate_form(self):
        populate_form(self.fib_settings, layout=self.window.fibFormLayout,
                      specific_settings={'variables_to_save':None,'settings_file':None,'fiducial_area':None,
                                         'milling_area':None})

    def serialize_layout(self):
        serialize_form(self.window.fibFormLayout, self.fib_settings)

    def getFibImagePushButton_clicked(self):
        from autoscript_sdb_microscope_client.structures import AdornedImage
        image = Image.from_as(AdornedImage.load('/home/cemcof/Downloads/cell.tif'))
        #image = Image.from_as(AdornedImage.load('D:\ceitec_data\ins - fccb\data\raw\slice_00547_(0).tif'))

        self.window.fibImageLabel.setImage(image)
        self.fiducial_area = ScanningArea.from_dict(self.fib_settings['fiducial_area'])
        self.milling_area = ScanningArea.from_dict(self.fib_settings['milling_area'])


    def setFibFiducialPushButton_clicked(self):
        self.serialize_layout()  # update fib_settings (fiducial_margin)
        self.window.fibImageLabel.reset_zoom_pan()
        self.fiducial_area = self.window.fibImageLabel.get_selected_area()
        # update settings
        self.fib_settings['fiducial_area'] = self.fiducial_area.to_dict()

    def setFibAreaPushButton_clicked(self):
        self.serialize_layout()  # update fib_settings (direction)
        self.window.fibImageLabel.reset_zoom_pan()
        self.milling_area = self.window.fibImageLabel.get_selected_area()
        # update settings
        self.fib_settings['milling_area'] = self.milling_area.to_dict()

    @property
    def milling_area(self):
        return self._milling_area


    @milling_area.setter
    def milling_area(self, value):
        self._milling_area.update(value)
        # update milling area mark
        img_shape = self.window.fibImageLabel.image.shape
        # milling area marker
        pos, size = self._milling_area.to_img_coordinates(img_shape)
        direction = self.fib_settings['direction']
        if direction > 0:
            pos.y += 10  # move in y
        else:
            pos.y += size[1] - 20
        self._milling_mark.update(ScanningArea.from_image_coordinates(img_shape, pos.x, pos.y, 10, 10))

    @property
    def fiducial_area(self):
        return self._fiducial_area

    @fiducial_area.setter
    def fiducial_area(self, value):
        self._fiducial_area.update(value)  # update fiducial
        # update extended fiducial area
        pixel_size = self.window.fibImageLabel.image.pixel_size
        img_shape = self.window.fibImageLabel.image.shape
        border = self.fib_settings['fiducial_margin']
        left_top, size= self._fiducial_area.to_meters(img_shape, pixel_size)
        """ Calculate and show the extended fiducial area (fiducial area + border)"""
        extended_fiducial_area = ScanningArea.from_meters(img_shape, pixel_size, left_top.x-border, left_top.y-border,
                                                 size[0]+2*border, size[1]+2*border)  # update extended fiducial area
        self._extended_fiducial_area.update(extended_fiducial_area)