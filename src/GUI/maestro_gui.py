import sys
import version

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox
)
from PySide6.QtCore import QCoreApplication

from fib_gui import FibGui
from GUI.forms.FIBSEM_Maestro_GUI import Ui_MainWindow
from fibsem_maestro.serial_control import SerialControl
from sem_gui import SemGui
from autofunctions_gui import AutofunctionsGui
from acb_gui import AcbGui
from driftcorr_gui import DriftCorrGui

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(QCoreApplication.translate("MainWindow", f"FIBSEM_Maestro v {version.VERSION}", None))
        self.build_connections()
        self.sem_gui = SemGui(self, serial_control.acquisition_settings, serial_control.image_settings,
                              serial_control.criterion_calculation_settings, serial_control.mask_settings,
                              serial_control)
        self.fib_gui = FibGui(self, serial_control.fib_settings)
        self.autofunctions_gui = AutofunctionsGui(self, serial_control.autofunction_settings,
                                                  serial_control.mask_settings, serial_control.image_settings,
                                                  serial_control.criterion_calculation_settings)
        self.driftcorr_gui = DriftCorrGui(self, serial_control.dc_settings)
        self.acb_gui = AcbGui(self, serial_control.contrast_brightness_settings, serial_control.mask_settings)


    def build_connections(self):
        self.actionAbout.triggered.connect(self.about_clicked)
        self.runPushButton.clicked.connect(self.runPushButton_clicked)
        self.stopPushButton.clicked.connect(self.stopPushButton_clicked)

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

    def stopPushButton_clicked(self):
        pass

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

        serial_control.save_yaml_settings()


if __name__ == "__main__":
    serial_control = SerialControl('../settings.yaml')
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())