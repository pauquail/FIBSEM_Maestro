from PySide6.QtGui import QPixmap

from GUI.gui_tools import populate_form, serialize_form, create_ImageLabel
from fibsem_maestro.tools.support import Image

class FibGui:
    def __init__(self, window, fib_settings):
        self.window = window
        self.fib_settings = fib_settings
        self.populate_form()
        self.build_connections()

        self.window.fibImageLabel = create_ImageLabel(self.window.fibVerticalLayout)

    def build_connections(self):
        self.window.getFibImagePushButton.clicked.connect(self.getFibImagePushButton_clicked)

    def populate_form(self):
        populate_form(self.fib_settings, layout=self.window.fibFormLayout)

    def serialize_layout(self):
        serialize_form(self.window.fibFormLayout, self.fib_settings)

    def getFibImagePushButton_clicked(self):
        from autoscript_sdb_microscope_client.structures import AdornedImage
        image = Image.from_as(AdornedImage.load('/home/cemcof/Downloads/cell.tif'))
        self.window.fibImageLabel.setImage(image)