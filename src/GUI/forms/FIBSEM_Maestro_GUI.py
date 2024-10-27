# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'FIBSEM_Maestro_GUI.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMenu, QMenuBar, QPushButton, QSizePolicy,
    QStatusBar, QTabWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        #MainWindow.setWindowModality(Qt.NonModal)
        MainWindow.resize(1000, 817)
        MainWindow.setStyleSheet(u"background-color: rgb(45, 51, 89);\n"
"color: rgb(85, 255, 0);")
        self.actionLoad = QAction(MainWindow)
        self.actionLoad.setObjectName(u"actionLoad")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabSem = QWidget()
        self.tabSem.setObjectName(u"tabSem")
        self.verticalLayout1 = QVBoxLayout(self.tabSem)
        self.verticalLayout1.setObjectName(u"verticalLayout1")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.imageLabel = QLabel(self.tabSem)
        self.imageLabel.setObjectName(u"imageLabel")
        self.imageLabel.setMinimumSize(QSize(0, 300))

        self.verticalLayout_2.addWidget(self.imageLabel)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.imageSettingsLabel = QLabel(self.tabSem)
        self.imageSettingsLabel.setObjectName(u"imageSettingsLabel")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.imageSettingsLabel)

        self.imageSettingsComboBox = QComboBox(self.tabSem)
        self.imageSettingsComboBox.setObjectName(u"imageSettingsComboBox")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.imageSettingsComboBox)

        self.Label = QLabel(self.tabSem)
        self.Label.setObjectName(u"Label")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.Label)

        self.changeImageSettingsPushButton = QPushButton(self.tabSem)
        self.changeImageSettingsPushButton.setObjectName(u"changeImageSettingsPushButton")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.changeImageSettingsPushButton)


        self.verticalLayout_2.addLayout(self.formLayout)


        self.verticalLayout1.addLayout(self.verticalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.getImagePushButton = QPushButton(self.tabSem)
        self.getImagePushButton.setObjectName(u"getImagePushButton")

        self.horizontalLayout.addWidget(self.getImagePushButton)

        self.setImagingAreaPushButton = QPushButton(self.tabSem)
        self.setImagingAreaPushButton.setObjectName(u"setImagingAreaPushButton")

        self.horizontalLayout.addWidget(self.setImagingAreaPushButton)

        self.testImagingPushButton = QPushButton(self.tabSem)
        self.testImagingPushButton.setObjectName(u"testImagingPushButton")

        self.horizontalLayout.addWidget(self.testImagingPushButton)

        self.fastScanCheckBox = QCheckBox(self.tabSem)
        self.fastScanCheckBox.setObjectName(u"fastScanCheckBox")
        self.fastScanCheckBox.setChecked(True)

        self.horizontalLayout.addWidget(self.fastScanCheckBox)


        self.verticalLayout1.addLayout(self.horizontalLayout)

        self.tabWidget.addTab(self.tabSem, "")
        self.tabFib = QWidget()
        self.tabFib.setObjectName(u"tabFib")
        self.tabWidget.addTab(self.tabFib, "")

        self.verticalLayout.addWidget(self.tabWidget)


        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1000, 22))
        self.menuSetting = QMenu(self.menubar)
        self.menuSetting.setObjectName(u"menuSetting")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuSetting.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuSetting.addAction(self.actionLoad)
        self.menuSetting.addAction(self.actionSave)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"FIBSEM_Maestro v 1.0.", None))
        self.actionLoad.setText(QCoreApplication.translate("MainWindow", u"Load", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.imageLabel.setText("")
        self.imageSettingsLabel.setText(QCoreApplication.translate("MainWindow", u"Image settings", None))
        self.Label.setText("")
        self.changeImageSettingsPushButton.setText(QCoreApplication.translate("MainWindow", u"Change image settings", None))
        self.getImagePushButton.setText(QCoreApplication.translate("MainWindow", u"Get image", None))
        self.setImagingAreaPushButton.setText(QCoreApplication.translate("MainWindow", u"Set imaging area", None))
        self.testImagingPushButton.setText(QCoreApplication.translate("MainWindow", u"Test imaging", None))
        self.fastScanCheckBox.setText(QCoreApplication.translate("MainWindow", u"Fast scan", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabSem), QCoreApplication.translate("MainWindow", u"SEM", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabFib), QCoreApplication.translate("MainWindow", u"FIB", None))
        self.menuSetting.setTitle(QCoreApplication.translate("MainWindow", u"Setting", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi

