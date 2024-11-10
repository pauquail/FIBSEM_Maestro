
from PySide6.QtWidgets import QInputDialog

from fibsem_maestro.tools.support import find_in_dict
from fibsem_maestro.microscope_control.autoscript_control import BeamControl
from gui_tools import populate_form, serialize_form, create_ImageLabel, confirm_action_dialog, clear_layout, \
    get_module_members, get_setters



class AutofunctionsGui:
    def __init__(self, window, autofunctions_settings, mask_settings):
        self.window = window
        self.autofunctions_settings = autofunctions_settings
        self.mask_settings = mask_settings
        self.build_connections()

        af_names = [af['name'] for af in autofunctions_settings['af_values']]
        self.selected_af = None
        self.window.autofunctionComboBox.addItems(af_names)
        self.af_set()

    def build_connections(self):
        self.window.cloneAutofunctionPushButton.clicked.connect(self.cloneAutoFunctionPushButton_clicked)
        self.window.removeAutofunctionPushButton.clicked.connect(self.removeAutofunctionPushButton_clicked)
        self.window.autofunctionComboBox.currentIndexChanged.connect(self.autofunctionComboBox_changed)

    def serialize_layout(self):
        serialize_form(self.window.autofunctionFormLayout, self.selected_af)

    def cloneAutoFunctionPushButton_clicked(self):
        text, ok = QInputDialog.getText(self.window, "New autofunction", "Autofunction name: ")

        if ok:
            print(f"You entered: {text}")

    def removeAutofunctionPushButton_clicked(self):
        if confirm_action_dialog():
            pass

    def autofunctionComboBox_changed(self):
        self.af_set()

    def af_set(self):
        """ Autofunction selected by combo-box -> update all"""
        selected_af_text = self.window.autofunctionComboBox.currentText()
        self.selected_af = find_in_dict(selected_af_text, self.autofunctions_settings['af_values'])
        clear_layout(self.window.autofunctionFormLayout)
        # list of available autofunctions (only names)
        autofunctions = get_module_members('fibsem_maestro.autofunctions.autofunction', 'class')
        masks = ['none', *[x['name'] for x in self.mask_settings]]  # none + masks defined in settings
        sweepings = get_module_members('fibsem_maestro.autofunctions.sweeping', 'class')
        # all possible electron and ions setters
        sweeping_variables = ['electron_beam.' + x for x in get_setters(BeamControl)] + ['ion_beam.' + x for x in get_setters(BeamControl)]
        populate_form(self.selected_af, layout=self.window.autofunctionFormLayout,
                      specific_settings={'name': None, 'criterion_name': None, 'image_name': None,
                                         'autofunction': autofunctions, 'mask_name':masks,
                                         'sweeping_strategy': sweepings, 'variable': sweeping_variables })

