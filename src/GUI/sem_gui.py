from maestro_gui import Window
from gui_tools import populate_form

class SemGui:
    def __init__(self, window: Window, acquisition_settings, imaging_settings):
        self.window = window
        self.acquisition_settings = acquisition_settings
        self.imaging_settings = imaging_settings
        self.set_events()

    def set_events(self):
        self.window.getImagePushButton.clicked.connect(self.getImagePushButton_clicked)

    def populate_form(self):
        populate_form(self.acquisition_settings, excluded_settings=['image_name', 'criterion_name'],
                      www]
        # add Calculate from slice distance (38deg)
    def getImagePushButton_clicked(self):
        QPixmap