import logging
import typing

from PySide6.QtCore import QRect

from GUI.gui_tools import create_ImageLabel, serialize_form, populate_form, get_module_members
from GUI.image_label import ImageLabel
from image_label_manger import ImageLabelManagers
from fibsem_maestro.tools.support import ScanningArea, Point


class DriftCorrGui:
    def __init__(self, window):
        self.window = window
        self.drift_correction_settings = self.window.serial_control.drift_correction_settings
        self.populate_form()

        self.window.driftcorrImageLabel = create_ImageLabel(self.window.driftcorrVerticalLayout)

        self.driftcorr_areas = DriftCorrAreas(self.drift_correction_settings['driftcorr_areas'],
                                              image_label=self.window.driftcorrImageLabel)
        self.build_connections()

        # add image label to the manager (for multiple image labels control)
        ImageLabelManagers.sem_manager.add_image(self.window.driftcorrImageLabel)

    def build_connections(self):
        self.window.addDriftCorrPushButton.clicked.connect(self.addDriftCorrPushButton_clicked)
        self.window.removeDriftCorrPushButton.clicked.connect(self.removeDriftCorrPushButton_clicked)

    def populate_form(self):
        driftcorr_methods = get_module_members('fibsem_maestro.drift_correction', 'mod')
        populate_form(self.drift_correction_settings, layout=self.window.driftCorrFormLayout,
                      specific_settings={'type': driftcorr_methods, 'driftcorr_areas': None})

    def serialize_layout(self):
        serialize_form(self.window.driftCorrFormLayout, self.drift_correction_settings)

    def addDriftCorrPushButton_clicked(self):
        new_driftcorr_area = self.window.driftcorrImageLabel.get_selected_area()
        self.driftcorr_areas.add(new_driftcorr_area)
        self.drift_correction_settings['driftcorr_areas'] = self.driftcorr_areas.to_dict()
        # # update view
        self.window.driftcorrImageLabel.rect = QRect()  # clear the drawing rectangle
        self.window.driftcorrImageLabel.update()

    def removeDriftCorrPushButton_clicked(self):
        self.driftcorr_areas.clear()
        self.drift_correction_settings['driftcorr_areas'] = self.driftcorr_areas.to_dict()
        self.window.driftcorrImageLabel.update()

class DriftCorrAreas:
    def __init__(self, driftcorr_areas: typing.List[dict], image_label: ImageLabel):
        self.image_label = image_label
        self._data = []
        try:
            [self.add(ScanningArea.from_dict(x)) for x in driftcorr_areas]
        except:
            logging.error(f'Conversion of {driftcorr_areas} to scanning areas failed! All areas are omitted')

    def add(self, value: ScanningArea):
        self._data.append(value)
        self.image_label.rects_to_draw.append((value, (255, 0, 255)))

    def get(self, index: int) -> ScanningArea:
        return self._data[index]

    def clear(self):
        self._data = []
        self.image_label.rects_to_draw = []

    def to_dict(self) -> typing.List[dict]:
        return [x.to_dict() for x in self._data]
