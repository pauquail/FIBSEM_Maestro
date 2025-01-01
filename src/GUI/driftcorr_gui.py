from PySide6.QtCore import QRect

from GUI.gui_tools import create_ImageLabel, serialize_form, populate_form, get_module_members
from image_label_manger import ImageLabelManagers
from fibsem_maestro.tools.support import ScanningArea, Point


class DriftCorrGui:
    def __init__(self, window, drift_correction_settings):
        self.window = window
        self.drift_correction_settings = drift_correction_settings

        self.populate_form()

        self.contrast_brightness_settings['acb_area']
        self.driftcorr_areas = DriftCorrAreas()
        self.acb_area = ScanningArea.from_dict()

        self.build_connections()

        self.window.acbImageLabel = create_ImageLabel(self.window.acbVerticalLayout_2)
        # add image label to the manager (for multiple image labels control)
        ImageLabelManagers.sem_manager.add_image(self.window.acbImageLabel)

        self.window.acbImageLabel.rects_to_draw.append((self.acb_area, (0, 0, 255)))

    def build_connections(self):
        #self.window.setAcbPushButton.clicked.connect(self.setAcbPushButton_clicked)

    def populate_form(self):
        driftcorr_methods = get_module_members('fibsem_maestro.drift_correction', 'mod')
        populate_form(self.drift_correction_settings, layout=self.window.driftCorrFormLayout,
                      specific_settings={'type': driftcorr_methods, 'driftcorr_areas': None})

    def serialize_layout(self):
        serialize_form(self.window.driftCorrFormLayout, self.drift_correction_settings)

    def setAcbPushButton_clicked(self):
        # self.acb_area = self.window.acbImageLabel.get_selected_area()
        # self.contrast_brightness_settings['acb_area'] = self.acb_area.to_dict()
        # # update view
        # self.window.acbImageLabel.rect = QRect()  # clear the drawing rectangle
        # self.window.acbImageLabel.update()

class DriftCorrAreas:
    def __init__(self):
        self._data = []

    def add(self, value):
        self._data.append(value)

    def get(self, index):
        return self._data[index]

    def set(self, index, value):
        if index < len(self._data):
            self._data[index].update(value)
        else:
            print("Index out of bounds!")