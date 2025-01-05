import os
import shutil
import sys
import version

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog
)
from PySide6.QtCore import QCoreApplication

from GUI.forms.EmailSettingsDialog import EmailSettingsDialog
from GUI.image_label_manger import ImageLabelManagers
from fib_gui import FibGui
from GUI.forms.FIBSEM_Maestro_GUI import Ui_MainWindow
from fibsem_maestro.serial_control import SerialControl
from fibsem_maestro.tools.dirs_management import findfile, make_dirs
from sem_gui import SemGui
from autofunctions_gui import AutofunctionsGui
from acb_gui import AcbGui
from driftcorr_gui import DriftCorrGui

default_settings_yaml_path = '../settings.yaml'  # default yaml settings

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, settings_yaml_path, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(QCoreApplication.translate("MainWindow", f"FIBSEM_Maestro v {version.VERSION}", None))
        self.build_connections()
        # create and configure SerialControl
        self.settings_init(settings_yaml_path)

    def settings_init(self, settings_yaml):
        self.serial_control = SerialControl(settings_yaml)
        self.sem_gui = SemGui(self)
        self.fib_gui = FibGui(self)
        self.autofunctions_gui = AutofunctionsGui(self)
        self.acb_gui = AcbGui(self)
        ImageLabelManagers.sem_manager.clear()  # clear image label managers


    def build_connections(self):
        self.actionAbout.triggered.connect(self.about_clicked)
        self.runPushButton.clicked.connect(self.runPushButton_clicked)
        self.stopPushButton.clicked.connect(self.stopPushButton_clicked)
        self.actionLoad.triggered.connect(self.actionLoad_clicked)
        self.actionSave.triggered.connect(self.actionSave_clicked)
        self.actionEmail.triggered.connect(self.actionEmail_clicked)

    def about_clicked(self):
        QMessageBox.about(
            self,
            "About FIBSEM_Maestro",
            f"<p>FIBSEM_Maestro v{version.VERSION}</p>"
            "<p>Pavel Krepelka</p>"
            "<p>CEITEC MU - Cryo-electron microscopy core facility</p>"
            "<p>pavel.krep@gmail.com</p>",
        )

    def runPushButton_clicked(self):
        self.apply_settings()
        max_slice, _ = findfile(self.serial_control.dirs_output_images)  # find the highest already acquired index
        self.serial_control.run(max_slice + 1)

    def stopPushButton_clicked(self):
        self.serial_control.stop()

    def actionSave_clicked(self):
        self.apply_settings()
        file, _ = QFileDialog.getSaveFileName(self, 'Save settings file', '', 'YAML Files (*.yaml)')
        if file:
            shutil.copy(settings_yaml_path, file)

    def actionLoad_clicked(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Load settings file', '', 'YAML Files (*.yaml)')
        if file:
            shutil.copy(file, settings_yaml_path)
            self.settings_init(file)

    def actionEmail_clicked(self):
        dialog = EmailSettingsDialog(self.serial_control.email_settings)
        if dialog.exec():
            dialog.save_settings()  # save settings to dict
            self.apply_settings()  # save settings to yaml file

    def closeEvent(self, event):
        """ Form closing event """
        self.apply_settings()  # save on form closing

    def apply_settings(self):

        # can be called in initialization, that is why some components may not exist
        if hasattr(self, 'sem_gui'):
            self.sem_gui.serialize_layout()
        if hasattr(self, 'fib_gui'):
            self.fib_gui.serialize_layout()
        if hasattr(self, 'autofunctions_gui'):
            self.autofunctions_gui.serialize_layout()
        if hasattr(self, 'driftcorr_gui'):
            self.driftcorr_gui.serialize_layout()
        if hasattr(self, 'acb_gui'):
            self.acb_gui.serialize_layout()

        self.serial_control.save_yaml_settings()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # folder path as argument
    if len(sys.argv) >= 2 and os.path.isdir(sys.argv[1]):
        folder_path = sys.argv[1]
    else:
        folder_path = QFileDialog.getExistingDirectory(None, 'Select Project Folder')

    if folder_path:  # If directory string is not empty
        settings_yaml_path = os.path.join(folder_path, 'settings.yaml')
        # if settings file does not exist - copy default
        if not os.path.exists(settings_yaml_path):
            shutil.copy(default_settings_yaml_path, settings_yaml_path)

        win = Window(settings_yaml_path)
        win.serial_control.change_dir_settings(folder_path)  # change dirs settings to correct project folder
        win.serial_control.save_yaml_settings()

        win.show()
        sys.exit(app.exec())
