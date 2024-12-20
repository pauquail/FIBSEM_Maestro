# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'FIBSEM_Maestro_GUI.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
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
    QSpacerItem, QStatusBar, QTabWidget, QVBoxLayout,
    QWidget)

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
        self.actionResize = QAction(MainWindow)
        self.actionResize.setObjectName(u"actionResize")
        self.actionEmail = QAction(MainWindow)
        self.actionEmail.setObjectName(u"actionEmail")
        self.actionNewProject = QAction(MainWindow)
        self.actionNewProject.setObjectName(u"actionNewProject")
        self.actionLoadProject = QAction(MainWindow)
        self.actionLoadProject.setObjectName(u"actionLoadProject")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setEnabled(True)
        self.tabWidget.setStyleSheet(u"")
        self.tabFib = QWidget()
        self.tabFib.setObjectName(u"tabFib")
        self.verticalLayout1 = QVBoxLayout(self.tabFib)
        self.verticalLayout1.setObjectName(u"verticalLayout1")
        self.fibVerticalLayout = QVBoxLayout()
        self.fibVerticalLayout.setObjectName(u"fibVerticalLayout")
        self.fibImageLabel = QLabel(self.tabFib)
        self.fibImageLabel.setObjectName(u"fibImageLabel")

        self.fibVerticalLayout.addWidget(self.fibImageLabel)

        self.label_3 = QLabel(self.tabFib)
        self.label_3.setObjectName(u"label_3")
        font = QFont()
        font.setBold(True)
        self.label_3.setFont(font)

        self.fibVerticalLayout.addWidget(self.label_3)

        self.fibFormLayout = QFormLayout()
        self.fibFormLayout.setObjectName(u"fibFormLayout")

        self.fibVerticalLayout.addLayout(self.fibFormLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.getFibImagePushButton = QPushButton(self.tabFib)
        self.getFibImagePushButton.setObjectName(u"getFibImagePushButton")

        self.horizontalLayout_3.addWidget(self.getFibImagePushButton)

        self.setFibFiducialPushButton = QPushButton(self.tabFib)
        self.setFibFiducialPushButton.setObjectName(u"setFibFiducialPushButton")

        self.horizontalLayout_3.addWidget(self.setFibFiducialPushButton)

        self.setFibAreaPushButton = QPushButton(self.tabFib)
        self.setFibAreaPushButton.setObjectName(u"setFibAreaPushButton")

        self.horizontalLayout_3.addWidget(self.setFibAreaPushButton)


        self.fibVerticalLayout.addLayout(self.horizontalLayout_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.fibVerticalLayout.addItem(self.verticalSpacer_2)


        self.verticalLayout1.addLayout(self.fibVerticalLayout)

        self.tabWidget.addTab(self.tabFib, "")
        self.tabSem = QWidget()
        self.tabSem.setObjectName(u"tabSem")
        self.verticalLayout2 = QVBoxLayout(self.tabSem)
        self.verticalLayout2.setObjectName(u"verticalLayout2")
        self.semVerticalLayout = QVBoxLayout()
        self.semVerticalLayout.setObjectName(u"semVerticalLayout")
        self.imageLabel = QLabel(self.tabSem)
        self.imageLabel.setObjectName(u"imageLabel")

        self.semVerticalLayout.addWidget(self.imageLabel)

        self.label_2 = QLabel(self.tabSem)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.semVerticalLayout.addWidget(self.label_2)

        self.semFormLayout = QFormLayout()
        self.semFormLayout.setObjectName(u"semFormLayout")

        self.semVerticalLayout.addLayout(self.semFormLayout)

        self.calculateFromSlicePushButton = QPushButton(self.tabSem)
        self.calculateFromSlicePushButton.setObjectName(u"calculateFromSlicePushButton")

        self.semVerticalLayout.addWidget(self.calculateFromSlicePushButton)


        self.verticalLayout2.addLayout(self.semVerticalLayout)

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

        self.imageSettingsFormLayout = QFormLayout()
        self.imageSettingsFormLayout.setObjectName(u"imageSettingsFormLayout")

        self.semImagingVerticalLayout.addLayout(self.imageSettingsFormLayout)


        self.verticalLayout2.addLayout(self.semImagingVerticalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.getImagePushButton = QPushButton(self.tabSem)
        self.getImagePushButton.setObjectName(u"getImagePushButton")

        self.horizontalLayout.addWidget(self.getImagePushButton)

        self.setImagingPushButton = QPushButton(self.tabSem)
        self.setImagingPushButton.setObjectName(u"setImagingPushButton")

        self.horizontalLayout.addWidget(self.setImagingPushButton)

        self.testImagingPushButton = QPushButton(self.tabSem)
        self.testImagingPushButton.setObjectName(u"testImagingPushButton")

        self.horizontalLayout.addWidget(self.testImagingPushButton)

        self.fastScanCheckBox = QCheckBox(self.tabSem)
        self.fastScanCheckBox.setObjectName(u"fastScanCheckBox")
        self.fastScanCheckBox.setChecked(True)

        self.horizontalLayout.addWidget(self.fastScanCheckBox)


        self.verticalLayout2.addLayout(self.horizontalLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout2.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tabSem, "")
        self.tabAutofunctions = QWidget()
        self.tabAutofunctions.setObjectName(u"tabAutofunctions")
        self.verticalLayout_2 = QVBoxLayout(self.tabAutofunctions)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.autofunctionsVerticalLayout = QVBoxLayout()
        self.autofunctionsVerticalLayout.setObjectName(u"autofunctionsVerticalLayout")
        self.autofunctionsImageLabel = QLabel(self.tabAutofunctions)
        self.autofunctionsImageLabel.setObjectName(u"autofunctionsImageLabel")

        self.autofunctionsVerticalLayout.addWidget(self.autofunctionsImageLabel)

        self.autofunctionLabel = QLabel(self.tabAutofunctions)
        self.autofunctionLabel.setObjectName(u"autofunctionLabel")

        self.autofunctionsVerticalLayout.addWidget(self.autofunctionLabel)

        self.autofunctionComboBox = QComboBox(self.tabAutofunctions)
        self.autofunctionComboBox.setObjectName(u"autofunctionComboBox")

        self.autofunctionsVerticalLayout.addWidget(self.autofunctionComboBox)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.cloneAutofunctionPushButton = QPushButton(self.tabAutofunctions)
        self.cloneAutofunctionPushButton.setObjectName(u"cloneAutofunctionPushButton")

        self.horizontalLayout_4.addWidget(self.cloneAutofunctionPushButton)

        self.removeAutofunctionPushButton = QPushButton(self.tabAutofunctions)
        self.removeAutofunctionPushButton.setObjectName(u"removeAutofunctionPushButton")

        self.horizontalLayout_4.addWidget(self.removeAutofunctionPushButton)


        self.autofunctionsVerticalLayout.addLayout(self.horizontalLayout_4)

        self.setAfAreaPushButton = QPushButton(self.tabAutofunctions)
        self.setAfAreaPushButton.setObjectName(u"setAfAreaPushButton")

        self.autofunctionsVerticalLayout.addWidget(self.setAfAreaPushButton)

        self.autofunctionFormLayout = QFormLayout()
        self.autofunctionFormLayout.setObjectName(u"autofunctionFormLayout")

        self.autofunctionsVerticalLayout.addLayout(self.autofunctionFormLayout)

        self.label_4 = QLabel(self.tabAutofunctions)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)

        self.autofunctionsVerticalLayout.addWidget(self.label_4)

        self.autofunctionCriteriumFormLayout = QFormLayout()
        self.autofunctionCriteriumFormLayout.setObjectName(u"autofunctionCriteriumFormLayout")

        self.autofunctionsVerticalLayout.addLayout(self.autofunctionCriteriumFormLayout)

        self.label_5 = QLabel(self.tabAutofunctions)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font)

        self.autofunctionsVerticalLayout.addWidget(self.label_5)

        self.autofunctionImagingFormLayout = QFormLayout()
        self.autofunctionImagingFormLayout.setObjectName(u"autofunctionImagingFormLayout")

        self.autofunctionsVerticalLayout.addLayout(self.autofunctionImagingFormLayout)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.autofunctionsVerticalLayout.addItem(self.verticalSpacer_3)


        self.verticalLayout_2.addLayout(self.autofunctionsVerticalLayout)

        self.tabWidget.addTab(self.tabAutofunctions, "")
        self.tabAcb = QWidget()
        self.tabAcb.setObjectName(u"tabAcb")
        self.acbVerticalLayout = QVBoxLayout(self.tabAcb)
        self.acbVerticalLayout.setObjectName(u"acbVerticalLayout")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.acbImageLabel = QLabel(self.tabAcb)
        self.acbImageLabel.setObjectName(u"acbImageLabel")

        self.verticalLayout_3.addWidget(self.acbImageLabel)

        self.setAcbPushButton = QPushButton(self.tabAcb)
        self.setAcbPushButton.setObjectName(u"setAcbPushButton")

        self.verticalLayout_3.addWidget(self.setAcbPushButton)

        self.acbFormLayout = QFormLayout()
        self.acbFormLayout.setObjectName(u"acbFormLayout")

        self.verticalLayout_3.addLayout(self.acbFormLayout)


        self.acbVerticalLayout.addLayout(self.verticalLayout_3)

        self.tabWidget.addTab(self.tabAcb, "")
        self.tabDriftCorrection = QWidget()
        self.tabDriftCorrection.setObjectName(u"tabDriftCorrection")
        self.maskingVerticalLayout = QVBoxLayout(self.tabDriftCorrection)
        self.maskingVerticalLayout.setObjectName(u"maskingVerticalLayout")
        self.tabWidget.addTab(self.tabDriftCorrection, "")

        self.verticalLayout.addWidget(self.tabWidget)


        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.applySettingsPushButton = QPushButton(self.centralwidget)
        self.applySettingsPushButton.setObjectName(u"applySettingsPushButton")

        self.horizontalLayout_2.addWidget(self.applySettingsPushButton)

        self.pushRun = QPushButton(self.centralwidget)
        self.pushRun.setObjectName(u"pushRun")

        self.horizontalLayout_2.addWidget(self.pushRun)


        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1000, 31))
        self.menuSetting = QMenu(self.menubar)
        self.menuSetting.setObjectName(u"menuSetting")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        self.menuProject = QMenu(self.menubar)
        self.menuProject.setObjectName(u"menuProject")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuProject.menuAction())
        self.menubar.addAction(self.menuSetting.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuSetting.addAction(self.actionLoad)
        self.menuSetting.addAction(self.actionSave)
        self.menuSetting.addAction(self.actionEmail)
        self.menuHelp.addAction(self.actionAbout)
        self.menuView.addAction(self.actionResize)
        self.menuProject.addAction(self.actionNewProject)
        self.menuProject.addAction(self.actionLoadProject)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(3)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"FIBSEM_Maestro v 1.0.", None))
        self.actionLoad.setText(QCoreApplication.translate("MainWindow", u"Load", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.actionResize.setText(QCoreApplication.translate("MainWindow", u"Resize", None))
        self.actionEmail.setText(QCoreApplication.translate("MainWindow", u"Email", None))
        self.actionNewProject.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionLoadProject.setText(QCoreApplication.translate("MainWindow", u"Load", None))
        self.fibImageLabel.setText("")
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.getFibImagePushButton.setText(QCoreApplication.translate("MainWindow", u"Get image", None))
        self.setFibFiducialPushButton.setText(QCoreApplication.translate("MainWindow", u"Set fiducial", None))
        self.setFibAreaPushButton.setText(QCoreApplication.translate("MainWindow", u"Set slicing area", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabFib), QCoreApplication.translate("MainWindow", u"FIB", None))
        self.imageLabel.setText("")
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Acquisition", None))
        self.calculateFromSlicePushButton.setText(QCoreApplication.translate("MainWindow", u"Calculate from slice distance (38\u00b0)", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Imaging", None))
        self.getImagePushButton.setText(QCoreApplication.translate("MainWindow", u"Get image", None))
        self.setImagingPushButton.setText(QCoreApplication.translate("MainWindow", u"Set imaging", None))
        self.testImagingPushButton.setText(QCoreApplication.translate("MainWindow", u"Test imaging", None))
        self.fastScanCheckBox.setText(QCoreApplication.translate("MainWindow", u"Fast scan", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabSem), QCoreApplication.translate("MainWindow", u"SEM", None))
        self.autofunctionsImageLabel.setText("")
        self.autofunctionLabel.setText(QCoreApplication.translate("MainWindow", u"Autofunction", None))
        self.cloneAutofunctionPushButton.setText(QCoreApplication.translate("MainWindow", u"Clone autofunction", None))
        self.removeAutofunctionPushButton.setText(QCoreApplication.translate("MainWindow", u"Remove autofunction", None))
        self.setAfAreaPushButton.setText(QCoreApplication.translate("MainWindow", u"Set af area", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Criterium", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Imaging", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabAutofunctions), QCoreApplication.translate("MainWindow", u"Autofunctions", None))
        self.acbImageLabel.setText("")
        self.setAcbPushButton.setText(QCoreApplication.translate("MainWindow", u"Set ABC area", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabAcb), QCoreApplication.translate("MainWindow", u"ACB", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabDriftCorrection), QCoreApplication.translate("MainWindow", u"Drift corr", None))
        self.applySettingsPushButton.setText(QCoreApplication.translate("MainWindow", u"Apply settings", None))
        self.pushRun.setText(QCoreApplication.translate("MainWindow", u"Run", None))
        self.menuSetting.setTitle(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
        self.menuProject.setTitle(QCoreApplication.translate("MainWindow", u"Project", None))
    # retranslateUi

