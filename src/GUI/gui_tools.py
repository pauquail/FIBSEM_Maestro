import logging

from PySide6.QtWidgets import QLabel, QLineEdit, QFormLayout
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import Qt

from image_label import ImageLabel

def populate_form(settings, excluded_settings=[], layout=None):
    """ Populate layout by settings """
    for s in settings:
        if s not in excluded_settings:
            value = settings[s]
            # scalar
            if isinstance(value, (int, float, str)):
                line_edit = QLineEdit(f'{value}')
                line_edit.settings_name = s
                layout.addRow(QLabel(s), line_edit)
            # two-items array. x,y
            elif isinstance(value, list) and len(value) == 2:
                line_edit_x = QLineEdit(f'{value[0]}')
                line_edit_y = QLineEdit(f'{value[1]}')
                line_edit_x.settings_name = s + '_x'
                line_edit_y.settings_name = s + '_y'
                layout.addRow(QLabel(s + '_x'), line_edit_x)
                layout.addRow(QLabel(s + '_y'), line_edit_y)
            else:
                raise ValueError(f'Settings {s} has invalid format!')


def serialize_form(layout: QFormLayout, serialized_settings):
    """ Get settings dict from layout """
    x_val = None
    for i in range(layout.rowCount()):
        widget = layout.itemAt(i, QFormLayout.FieldRole).widget()
        if hasattr(widget, 'settings_name'):
            try:
                int(widget.text())
                value = int(widget.text())
            except ValueError:
                try:
                    float(widget.text())
                    value = float(widget.text())
                except ValueError:
                    value = widget
            settings_name = widget.settings_name
            if settings_name[-2:] == '_x':
                x_val = value
                continue
            elif settings_name[-2:] == '_y':
                value = [x_val, value]
                settings_name = widget.settings_name[:-2]

            serialized_settings[settings_name] = value
            logging.debug(f'{settings_name}: {value} updated')

def create_ImageLabel(layout):
    # image label
    label = ImageLabel()
    layout.insertWidget(0, label)
    layout.setAlignment(label, Qt.AlignTop | Qt.AlignLeft)
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return label