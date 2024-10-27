import time

from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QPainter, QPen, QPixmap, QColor
from PySide6.QtCore import QRect, Qt, QPoint, QSize

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rect = QRect()
        self.adjusted_rect = QRect()  # zoom applied
        self.handles = [QRect() for _ in range(4)]
        self.handleSize = 10
        self.handleSelected = -1
        self.mousePressPos = None
        self.delta = QPoint(0,0)
        self.rect_delta = QPoint(0, 0)

        # zoom in/out
        self.scale = 1
        self.original_scale = 1  # scale after initial resize

        # image scaling
        self.original_scale_x = 1
        self.original_scale_y = 1

        self.original_pixmap = None

        # Setting up the buttons for zooming in and out
        self.zoom_in_button = QtWidgets.QPushButton("+", self)
        self.zoom_in_button.setFixedWidth(20)
        self.zoom_in_button.clicked.connect(self.zoom_in)

        self.zoom_out_button = QtWidgets.QPushButton("-", self)
        self.zoom_out_button.setFixedWidth(20)
        self.zoom_out_button.clicked.connect(self.zoom_out)

        # Positioning the buttons at the top left corner of ImageLabel
        self.zoom_in_button.move(5, 5)
        self.zoom_out_button.move(self.zoom_in_button.width()+5, 5)

        self.last_click_time = 0
        self.click_interval = 0.5


    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        lime = QColor(0, 255, 0)

        painter.setPen(QPen(lime, 2, Qt.SolidLine))
        painter.drawRect(self.adjusted_rect)

        painter.setPen(QPen(lime, 2, Qt.SolidLine))
        for handle in self.handles:
            if not handle.isNull():
                painter.fillRect(handle, lime)

    def mousePressEvent(self, event):
        mousePos = event.position().toPoint()
        self.mousePressPos = mousePos
        if event.buttons() == Qt.LeftButton:
            self.handleSelected = -1
            for i, handle in enumerate(self.handles):
                if handle.contains(mousePos):
                    self.handleSelected = i
            if self.handleSelected == -1:
                self.rect.setTopLeft(mousePos / self.scale)
                self.rect.setBottomRight(mousePos / self.scale)
            self.updateHandles()
            self.update()
        if event.button() == Qt.RightButton:
            current_time = time.time()
            if current_time - self.last_click_time < self.click_interval:
                change_scale = self.original_scale / self.scale
                self.zoom(change_scale)
            self.last_click_time = current_time

    def mouseMoveEvent(self, event):
        mousePos = event.position().toPoint()
        if event.buttons() == Qt.RightButton:
            self.delta += (mousePos - self.mousePressPos) / self.scale
            self.rect_delta += (mousePos - self.mousePressPos) / self.scale
            self.mousePressPos = mousePos
        elif event.buttons() == Qt.LeftButton:  # when left button is held down
            self.rect_delta = QPoint(0,0)
            if self.handleSelected >= 0:  # if a handle is selected
                self.resizeRectangle(mousePos)
            else:  # if no handle is selected, draw rectangle
                self.rect.setBottomRight(mousePos / self.scale)
                self.updateHandles()
        elif event.buttons() == Qt.NoButton:  # when mouse is just hovering
            handleHovered = -1
            for i, handle in enumerate(self.handles):
                if handle.contains(mousePos):
                    handleHovered = i
            if handleHovered != self.handleHovered:
                self.handleHovered = handleHovered
                self.update()
        self.update()

    def mouseReleaseEvent(self, event):
        self.handleSelected = -1
        self.mousePressPos = None
        self.update()

    def wheelEvent(self, event):
        """ Function to handle mouse wheel event """
        wheel_direction = event.angleDelta().y()

        if wheel_direction < 0:
            self.zoom_out()
        else:
            self.zoom_in()

    def resizeRectangle(self, mousePos):
        if self.handleSelected == 0:  # left
            dx = (mousePos.x() - self.mousePressPos.x()) / self.scale
            self.rect.setLeft(self.rect.left() + dx)
        elif self.handleSelected == 1:  # top
            dy = (mousePos.y() - self.mousePressPos.y()) / self.scale
            self.rect.setTop(self.rect.top() + dy)
        elif self.handleSelected == 2:  # right
            dx = (mousePos.x() - self.mousePressPos.x()) / self.scale
            self.rect.setRight(self.rect.right() + dx)
        elif self.handleSelected == 3:  # bottom
            dy = (mousePos.y() - self.mousePressPos.y()) / self.scale
            self.rect.setBottom(self.rect.bottom() + dy)
        self.mousePressPos = mousePos

    def update(self):
        super().update()
        self.updateHandles()
        self.repaint_pixmap()

    def updateHandles(self):
        handleSize = self.handleSize
        self.update_adjusted_rect()
        self.handles[0].setRect(self.adjusted_rect.left(), self.adjusted_rect.top() + self.adjusted_rect.height() // 2, handleSize,
                                handleSize)  # left
        self.handles[1].setRect(self.adjusted_rect.left() + self.adjusted_rect.width() // 2, self.adjusted_rect.top(), handleSize,
                                handleSize)  # top
        self.handles[2].setRect(self.adjusted_rect.right() - handleSize, self.adjusted_rect.top() + self.adjusted_rect.height() // 2, handleSize,
                                handleSize)  # right
        self.handles[3].setRect(self.adjusted_rect.left() + self.adjusted_rect.width() // 2, self.adjusted_rect.bottom() - handleSize, handleSize,
                                handleSize)  # bottom

    def setPixmap(self, pixmap):
        """ Resize if too big """
        screen = QtWidgets.QApplication.primaryScreen()
        size = screen.geometry().size()
        width = size.width() * 0.9
        height = size.height() * 0.6

        if pixmap.width() > width or pixmap.height() > height:
            # Keep aspect ratio and use smooth transformation while scaling
            scaled_pixmap = pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        else:
            scaled_pixmap = pixmap

        self.scale = scaled_pixmap.width() / pixmap.width()
        self.original_scale = self.scale
        self.original_pixmap = pixmap
        self.update()

    def zoom(self, scale):
        self.scale *= scale
        self.rect_delta *= scale
        self.delta *= scale
        self.update()

    def zoom_in(self):
        """Zoom in the image"""
        self.zoom(1.1)

    def zoom_out(self):
        """Zoom out the image"""
        self.zoom(1/1.1)

    def repaint_pixmap(self):
        """Repaint the pixmap with new scale"""
        original_pixmap = self.original_pixmap.copy()  # get a copy of original pixmap
        width = original_pixmap.width() * self.scale
        height = original_pixmap.height() * self.scale
        scaled_pixmap = original_pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.updateHandles()

        # shift
        shifted_pixmap = QPixmap(scaled_pixmap.size())
        shifted_pixmap.fill(Qt.white)
        painter = QPainter(shifted_pixmap)
        painter.drawPixmap(self.delta, scaled_pixmap)
        painter.end()

        super().setPixmap(shifted_pixmap)

    def update_adjusted_rect(self):
        x = self.rect.left() * self.scale + self.rect_delta.x()
        y = self.rect.top() * self.scale + self.rect_delta.y()
        width = self.rect.width() * self.scale
        height = self.rect.height() * self.scale
        self.adjusted_rect = QRect(x, y, width, height)