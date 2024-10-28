import logging

from PySide6.QtWidgets import QLabel, QLineEdit


def populate_form(settings, excluded_settings, layout):
    """ Populate layout by settings """
    for s in settings:
        if s not in excluded_settings:
            value = settings[s]
            # unbox if needed
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            # scalar
            if isinstance(value, (int, float)):
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
                raise ValueError(f'Settings {s} has too many items!')


def serialize_form(layout, serialized_settings):
    """ Get settings dict from layout """
    x_val = None
    for i in range(layout.rowCount()):
        item = layout.itemAt(i)
        widget = item.widget() if item else None
        if isinstance(widget, QLineEdit):
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