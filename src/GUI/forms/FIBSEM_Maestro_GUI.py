# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'FIBSEM_Maestro_GUI.ui'
##
## Created by: Qt User Interface Compiler version 6.7.3
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFormLayout, QGridLayout,
    QHBoxLayout, QLabel, QMainWindow, QMenu,
    QMenuBar, QPushButton, QSizePolicy, QSpacerItem,
    QStatusBar, QTabWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.setWindowModality(Qt.NonModal)
        MainWindow.resize(1000, 817)
        MainWindow.setStyleSheet(u"")
        self.actionLoad = QAction(MainWindow)
        self.actionLoad.setObjectName(u"actionLoad")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setStyleSheet(u"")
        self.tabSem = QWidget()
        self.tabSem.setObjectName(u"tabSem")
        self.verticalLayout1 = QVBoxLayout(self.tabSem)
        self.verticalLayout1.setObjectName(u"verticalLayout1")
        self.semVerticalLayout = QVBoxLayout()
        self.semVerticalLayout.setObjectName(u"semVerticalLayout")
        self.imageLabel = QLabel(self.tabSem)
        self.imageLabel.setObjectName(u"imageLabel")

        self.semVerticalLayout.addWidget(self.imageLabel)

        self.label_2 = QLabel(self.tabSem)
        self.label_2.setObjectName(u"label_2")
        font = QFont()
        font.setBold(True)
        self.label_2.setFont(font)

        self.semVerticalLayout.addWidget(self.label_2)

        self.semFormLayout = QFormLayout()
        self.semFormLayout.setObjectName(u"semFormLayout")

        self.semVerticalLayout.addLayout(self.semFormLayout)

        self.calculateFromSlicePushButton = QPushButton(self.tabSem)
        self.calculateFromSlicePushButton.setObjectName(u"calculateFromSlicePushButton")

        self.semVerticalLayout.addWidget(self.calculateFromSlicePushButton)


        self.verticalLayout1.addLayout(self.semVerticalLayout)

        self.semImagingVerticalLayout = QVBoxLayout()
        self.semImagingVerticalLayout.setObjectName(u"semImagingVerticalLayout")
        self.label = QLabel(self.tabSem)
        self.label.setObjectName(u"label")
        font1 = QFont()
        font1.setBold(True)
        font1.setItalic(False)
        self.label.setFont(font1)
        self.label.setTextFormat(Qt.AutoText)

        self.semImagingVerticalLayout.addWidget(self.label)


        self.verticalLayout1.addLayout(self.semImagingVerticalLayout)

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

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout1.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tabSem, "")
        self.tabFib = QWidget()
        self.tabFib.setObjectName(u"tabFib")
        self.tabWidget.addTab(self.tabFib, "")

        self.verticalLayout.addWidget(self.tabWidget)


        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.applySettingsPushButton = QPushButton(self.centralwidget)
        self.applySettingsPushButton.setObjectName(u"applySettingsPushButton")

        self.horizontalLayout_2.addWidget(self.applySettingsPushButton)


        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 0, 1, 1)

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
        self.menuHelp.addAction(self.actionAbout)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"FIBSEM_Maestro v 1.0.", None))
        self.actionLoad.setText(QCoreApplication.translate("MainWindow", u"Load", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.imageLabel.setText("")
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Acquisition", None))
        self.calculateFromSlicePushButton.setText(QCoreApplication.translate("MainWindow", u"Calculate from slice distance (38\u00b0)", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Imaging", None))
        self.getImagePushButton.setText(QCoreApplication.translate("MainWindow", u"Get image", None))
        self.setImagingAreaPushButton.setText(QCoreApplication.translate("MainWindow", u"Set imaging area", None))
        self.testImagingPushButton.setText(QCoreApplication.translate("MainWindow", u"Test imaging", None))
        self.fastScanCheckBox.setText(QCoreApplication.translate("MainWindow", u"Fast scan", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabSem), QCoreApplication.translate("MainWindow", u"SEM", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabFib), QCoreApplication.translate("MainWindow", u"FIB", None))
        self.applySettingsPushButton.setText(QCoreApplication.translate("MainWindow", u"Apply settings", None))
        self.menuSetting.setTitle(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi

