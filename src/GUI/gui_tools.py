from PySide6.QtWidgets import QLabel, QLineEdit

def populate_form(settings, excluded_settings, layout):
    for s in settings:
        if not s in excluded_settings:
            value = settings[s]
            if isinstance(value, (int, float)):
                layout.addRow(QLabel(s), QLineEdit(f'{value}'))
            elif isinstance(value, list) and len(value) == 1:
                layout.addRow(QLabel(s), QLineEdit(f'{value[0]}'))
            elif isinstance(value, list) and len(value) == 2:
                layout.addRow(QLabel(s + '_x'), QLineEdit(f'{value[0]}'))
                layout.addRow(QLabel(s + '_y'), QLineEdit(f'{value[1]}'))
            else:
                raise ValueError(f'Settings {s} has too many items!')