from PyQt5.QtWidgets import QWidget, QStyle, QStyleOptionSlider, QSlider
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint

class QRangeSlider(QWidget):
    rangeChanged = pyqtSignal(tuple)

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self._min = 0
        self._max = 100
        self._low = 20
        self._high = 80
        self._moving = None
        self.setMinimumHeight(30)
        self.setMouseTracking(True)

    def setMinimum(self, value):
        self._min = value
        self.update()

    def setMaximum(self, value):
        self._max = value
        self.update()

    def setValue(self, value_tuple):
        self._low, self._high = value_tuple
        self.update()
        self.rangeChanged.emit((self._low, self._high))

    def value(self):
        return (self._low, self._high)

    def mousePressEvent(self, event):
        pos = event.pos().x() if self.orientation == Qt.Horizontal else event.pos().y()
        low_pos = self._pos_from_value(self._low)
        high_pos = self._pos_from_value(self._high)
        if abs(pos - low_pos) < 10:
            self._moving = 'low'
        elif abs(pos - high_pos) < 10:
            self._moving = 'high'
        else:
            self._moving = None

    def mouseMoveEvent(self, event):
        if not self._moving:
            return
        pos = event.pos().x() if self.orientation == Qt.Horizontal else event.pos().y()
        value = self._value_from_pos(pos)
        if self._moving == 'low':
            if value < self._min:
                value = self._min
            if value > self._high:
                value = self._high
            self._low = value
        elif self._moving == 'high':
            if value > self._max:
                value = self._max
            if value < self._low:
                value = self._low
            self._high = value
        self.update()
        self.rangeChanged.emit((self._low, self._high))

    def mouseReleaseEvent(self, event):
        self._moving = None

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QColor
        painter = QPainter(self)
        rect = self.rect()
        # Draw background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(200, 200, 200))
        painter.drawRect(rect)
        # Draw range
        low_pos = self._pos_from_value(self._low)
        high_pos = self._pos_from_value(self._high)
        if self.orientation == Qt.Horizontal:
            painter.setBrush(QColor(100, 200, 250))
            painter.drawRect(low_pos, 0, high_pos - low_pos, rect.height())
            # Draw handles
            painter.setBrush(QColor(50, 150, 200))
            painter.drawRect(low_pos - 5, 0, 10, rect.height())
            painter.drawRect(high_pos - 5, 0, 10, rect.height())
        else:
            # Vertical orientation not implemented in this simple version
            pass

    def _pos_from_value(self, value):
        rect = self.rect()
        return int((value - self._min) / (self._max - self._min) * rect.width())

    def _value_from_pos(self, pos):
        rect = self.rect()
        value = int(pos / rect.width() * (self._max - self._min) + self._min)
        return min(max(value, self._min), self._max)