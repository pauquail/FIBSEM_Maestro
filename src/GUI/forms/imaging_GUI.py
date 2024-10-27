# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'imaging_GUI.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFormLayout, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_imagingForm(object):
    def setupUi(self, imagingForm):
        if not imagingForm.objectName():
            imagingForm.setObjectName(u"imagingForm")
        imagingForm.resize(400, 300)
        self.verticalLayout = QVBoxLayout(imagingForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.imagingFormLayout = QFormLayout()
        self.imagingFormLayout.setObjectName(u"imagingFormLayout")

        self.verticalLayout.addLayout(self.imagingFormLayout)


        self.retranslateUi(imagingForm)

        QMetaObject.connectSlotsByName(imagingForm)
    # setupUi

    def retranslateUi(self, imagingForm):
        imagingForm.setWindowTitle(QCoreApplication.translate("imagingForm", u"Imaging", None))
    # retranslateUi

