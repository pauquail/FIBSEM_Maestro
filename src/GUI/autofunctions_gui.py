
from PySide6.QtWidgets import QInputDialog

from image_label_manger import ImageLabelManagers
from fibsem_maestro.tools.support import find_in_dict, ScanningArea, Point
from fibsem_maestro.microscope_control.autoscript_control import BeamControl
from gui_tools import populate_form, serialize_form, create_ImageLabel, confirm_action_dialog, clear_layout, \
    get_module_members, get_setters



class AutofunctionsGui:
    def __init__(self, window, autofunctions_settings, mask_settings, image_settings, criterion_settings):
        self.window = window
        self.autofunctions_settings = autofunctions_settings
        self.image_settings = image_settings
        self.criterion_settings = criterion_settings
        self.mask_settings = mask_settings
        self.build_connections()

        self.window.autofunctionsImageLabel = create_ImageLabel(self.window.autofunctionsVerticalLayout)
        # add image label to the manager (for multiple image labels control)
        ImageLabelManagers.sem_manager.add_image(self.window.autofunctionsImageLabel)

        self.selected_af = None
        self._af_area = ScanningArea(Point(0,0),0,0)
        self.autofunctionComboBox_fill()
        self.af_set()

        self.window.autofunctionsImageLabel.rects_to_draw.append((self.af_area, (0, 255, 0)))

    def autofunctionComboBox_fill(self):
        self.window.autofunctionComboBox.clear()
        af_names = [af['name'] for af in self.autofunctions_settings]
        self.window.autofunctionComboBox.addItems(af_names)

    def build_connections(self):
        self.window.cloneAutofunctionPushButton.clicked.connect(self.cloneAutoFunctionPushButton_clicked)
        self.window.removeAutofunctionPushButton.clicked.connect(self.removeAutofunctionPushButton_clicked)
        self.window.setAfAreaPushButton.clicked.connect(self.setAfAreaPushButton_clicked)
        self.window.autofunctionComboBox.currentIndexChanged.connect(self.autofunctionComboBox_changed)

    def serialize_layout(self):
        serialize_form(self.window.autofunctionFormLayout, self.selected_af)
        serialize_form(self.window.autofunctionCriteriumFormLayout, find_in_dict(self.selected_af['criterion_name'], self.criterion_settings))
        serialize_form(self.window.autofunctionImagingFormLayout, find_in_dict(self.selected_af['image_name'], self.image_settings))

    def cloneAutoFunctionPushButton_clicked(self):
        text, ok = QInputDialog.getText(self.window, "New autofunction", "Autofunction name: ")

        if ok:
            self.selected_af = dict(self.selected_af)  # copy dict
            self.selected_af['name'] = text
            self.selected_af['criterion_name'] = text
            self.selected_af['image_name'] = text
            self.autofunctions_settings.append(self.selected_af)
            self.criterion_settings.append({'name': text})
            self.image_settings.append({'name': text})
            self.serialize_layout()
            self.autofunctionComboBox_fill()
            self.window.autofunctionComboBox.setCurrentText(text)


    def removeAutofunctionPushButton_clicked(self):
        if len(self.autofunctions_settings) > 1:
            if confirm_action_dialog():
                criterion = find_in_dict(self.selected_af['criterion_name'], self.criterion_settings)
                imaging = find_in_dict(self.selected_af['image_name'], self.image_settings)
                self.criterion_settings.remove(criterion)
                self.image_settings.remove(imaging)
                self.autofunctions_settings.remove(self.selected_af)
                self.autofunctionComboBox_fill()
                self.window.autofunctionComboBox.setCurrentIndex(0)


    def setAfAreaPushButton_clicked(self):
        self.af_area = self.window.autofunctionsImageLabel.get_selected_area()
        self.selected_af['af_area'] = self.af_area.to_dict()


    def autofunctionComboBox_changed(self):
        self.af_set()

    def af_set(self):
        """ Autofunction selected by combo-box -> update all"""
        selected_af_text = self.window.autofunctionComboBox.currentText()

        if selected_af_text == '':
            return

        self.selected_af = find_in_dict(selected_af_text, self.autofunctions_settings)

        # items for combo boxes
        # list of available autofunctions (only names)
        autofunctions = get_module_members('fibsem_maestro.autofunctions.autofunction', 'class')
        masks = ['none', *[x['name'] for x in self.mask_settings]]  # none + masks defined in settings
        sweepings = get_module_members('fibsem_maestro.autofunctions.sweeping', 'class')
        # all possible electron and ions setters
        sweeping_variables = ['electron_beam.' + x for x in get_setters(BeamControl)] + ['ion_beam.' + x for x in get_setters(BeamControl)]
        criteria = get_module_members('fibsem_maestro.image_criteria.criteria_math', 'func')

        populate_form(self.selected_af, layout=self.window.autofunctionFormLayout,
                      specific_settings={'name': None, 'criterion_name': None, 'image_name': None, 'af_area': None,
                                         'autofunction': autofunctions, 'mask_name': masks, # list is shown as combobox
                                         'sweeping_strategy': sweepings, 'variable': sweeping_variables })
        image_settings = find_in_dict(self.selected_af['image_name'], self.image_settings)
        populate_form(image_settings, layout=self.window.autofunctionImagingFormLayout, specific_settings={'name': None})
        criterion_settings = find_in_dict(self.selected_af['criterion_name'],self.criterion_settings)
        populate_form(criterion_settings, layout=self.window.autofunctionCriteriumFormLayout, specific_settings={'name': None, 'mask_name': masks,
                                                                                                                 'criterion': criteria})

        self.af_area = ScanningArea.from_dict(self.selected_af['af_area'])

    @property
    def af_area(self):
        return self._af_area

    @af_area.setter
    def af_area(self, value):
        self._af_area.update(value)  # update af area
