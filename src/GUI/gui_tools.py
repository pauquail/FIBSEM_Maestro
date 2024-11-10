import importlib
import logging
import inspect

from PySide6.QtWidgets import QLabel, QLineEdit, QFormLayout, QMessageBox, QComboBox, QCheckBox
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import Qt

from image_label import ImageLabel


def populate_form(settings, layout=None, specific_settings={}):
    """ Populate layout by settings.
    specific_settings - dict of non-textbox settings
      - None - omit
      - List - combo box """

    for s in settings:
        value_edit = None

        if s in specific_settings:
            if isinstance(specific_settings[s], list):
                value_edit = QComboBox()
                value_edit.addItems(specific_settings[s])
                value_edit.setCurrentText(settings[s])
        else:
            value = settings[s]
            value_edit = QLineEdit()
            # bool
            if isinstance(value, bool):
                value_edit = QCheckBox()
                value_edit.setChecked(value)
            # scalar
            elif isinstance(value, (int, float, str)):
                value_edit.setText(f'{value}')
            # array
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    if i == 0:
                        value_edit.setText(value_edit.text() + f'{v}')
                    else:
                        value_edit.setText(value_edit.text() + f',{v}')
            elif isinstance(value, dict):
                for k, v in value.items():
                    value_edit.setText(value_edit.text() + f'{k}:{v},')
            else:
                raise ValueError(f'Settings {s} has invalid format!')

        if value_edit is not None:
            value_edit.settings_name = s
            layout.addRow(QLabel(s), value_edit)


def serialize_form(layout: QFormLayout, serialized_settings):
    """ Get settings dict from layout """
    for i in range(layout.rowCount()):
        field_item = layout.itemAt(i, QFormLayout.FieldRole)
        if field_item is not None:
            widget = field_item.widget()
            if hasattr(widget, 'settings_name'):
                if isinstance(widget, QComboBox):
                    str_value = widget.currentText()
                else:
                    str_value = widget.text()

                if isinstance(widget, QCheckBox):
                    value = widget.isChecked()
                else:
                    try:
                        value = int(str_value)
                    except ValueError:
                        try:
                            value = float(str_value)
                        except ValueError:
                            try:
                                if ',' in str_value:
                                    # string value with ','
                                    parts = str_value.split(',')
                                    value = [float(v) for v in parts]
                                else:
                                    # string value
                                    value = str_value
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


def get_module_members(module_path: str, member_type: str):
    """
    Retrieve a list of class names or function names from a module at the given module path.

    Args:
        module_path (str): The Python path of the module to inspect
        member_type (str): The type of members to return, either 'class' to return classes, or 'func' to return functions.

    Returns:
        List[str]: A list of member names of the specified member_type from the module at module_path.

    Raises:
        ValueError: If member_type is not either 'class' or 'func', it raises ValueError with relevant information.
    """
    if member_type == 'class':
        inspect_member = inspect.isclass
    elif member_type == 'func':
        inspect_member = inspect.isfunction
    else:
        raise ValueError(f'Unknown member type: {member_type}')
    imported_module = importlib.import_module(module_path)
    return [cls[0] for cls in inspect.getmembers(imported_module, inspect_member)
            if cls[1].__module__ == imported_module.__name__]


def get_setters(cls):
    """
    Retrieves all setters defined in the given class.

    Args:
        cls (class): The class to investigate.

    Returns:
        List[str]: A list of setters' names defined in the class.
    """
    return [name for name, value in inspect.getmembers(cls) if isinstance(value, property) and value.fset is not None]