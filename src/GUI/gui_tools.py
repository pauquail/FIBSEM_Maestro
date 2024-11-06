import logging

from PySide6.QtWidgets import QLabel, QLineEdit, QFormLayout, QMessageBox
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import Qt

from image_label import ImageLabel

def populate_form(settings, excluded_settings=[], layout=None):
    """ Populate layout by settings """
    for s in settings:
        if s not in excluded_settings:
            value = settings[s]
            line_edit = QLineEdit()
            # scalar
            if isinstance(value, (int, float, str)):
                line_edit.setText(f'{value}')
            # array
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    if i == 0:
                        line_edit.setText(line_edit.text() + f'{v}')
                    else:
                        line_edit.setText(line_edit.text() + f',{v}')
            elif isinstance(value, dict):
                for k, v in value.items():
                    line_edit.setText(line_edit.text() + f'{k}:{v},')
            else:
                raise ValueError(f'Settings {s} has invalid format!')
            line_edit.settings_name = s
            layout.addRow(QLabel(s), line_edit)

def serialize_form(layout: QFormLayout, serialized_settings):
    """ Get settings dict from layout """
    x_val = None
    for i in range(layout.rowCount()):
        widget = layout.itemAt(i, QFormLayout.FieldRole).widget()
        if hasattr(widget, 'settings_name'):
            str_value = widget.text()
            try:
                value = int(str_value)
            except ValueError:
                try:
                    value = float(str_value)
                except ValueError:
                    try:
                        if ',' in str_value:
                            parts = str_value.split(',')
                            value = [float(v) for v in parts]
                    except ValueError:
                        raise ValueError(f'Settings "{str_value}" has invalid format!')

            settings_name = widget.settings_name
            serialized_settings[settings_name] = value
            logging.debug(f'{settings_name}: {value} updated')


def create_ImageLabel(layout):
    # image label
    label = ImageLabel()
    layout.insertWidget(0, label)
    layout.setAlignment(label, Qt.AlignTop | Qt.AlignLeft)
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return label


def confirm_action_dialog():
    msgBox = QMessageBox()
    msgBox.setWindowTitle("Confirmation")
    msgBox.setText("Are you sure?")
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    return msgBox.exec()

def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()