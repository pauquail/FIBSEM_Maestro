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

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(QCoreApplication.translate("MainWindow", f"FIBSEM_Maestro v {version.VERSION}", None))
        self.build_connections()
        self.sem_gui = SemGui(self, serial_control.acquisition_settings, serial_control.image_settings, serial_control)
        self.fib_gui = FibGui(self, serial_control.fib_settings)
        self.autofunctions_gui = AutofunctionsGui(self, serial_control.autofunction_settings)

    def build_connections(self):
        self.applySettingsPushButton.clicked.connect(self.applySettingsPushButton_clicked)
        self.actionAbout.triggered.connect(self.about_clicked)
        self.actionResize.triggered.connect(self.resize_clicked)

    def about_clicked(self):
        QMessageBox.about(
            self,
            "About FIBSEM_Maestro",
            f"<p>FIBSEM_Maestro v{version.VERSION}</p>"
            "<p>Pavel Krepelka</p>"
            "<p>CEITEC MU - Cryo-electron microscopy core facility</p>"
            "<p>pavel.krep@gmail.com</p>",
        )

    def resize_clicked(self):
        self.resize(self.sizeHint())

    def applySettingsPushButton_clicked(self):
        self.sem_gui.serialize_layout()
        self.fib_gui.serialize_layout()
        serial_control.save_yaml_settings()


if __name__ == "__main__":
    serial_control = SerialControl('../settings.yaml')
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())