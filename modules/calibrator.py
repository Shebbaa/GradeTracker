"""
Inferno Grade Tracker — Calibrator (v3)

ZoneSelector: рисуешь зону вокруг кнопки «2» в дневнике.
ColorPicker: кликаешь по ГОЛУБОМУ ФОНУ выбранной «2».

Логика: когда препод нажимает «2» — фон кнопки становится
голубым. Пипетка захватывает именно этот голубой цвет.
Детектор следит за зоной: голубой появился = двойка выбрана.
"""

import numpy as np
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QCursor


class ZoneSelector(QWidget):
    zone_selected = pyqtSignal(int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        self.showFullScreen()

        self._origin = QPoint()
        self._current = QPoint()
        self._drawing = False

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 100))

        p.setPen(QColor(255, 60, 60))
        p.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
            "\n🔥 ЗОНА КАЗНИ — обведи область кнопки «2» в дневнике\n"
            "Выдели зону где появляется кнопка оценки\n[ESC] отмена")

        if self._drawing:
            rect = QRect(self._origin, self._current).normalized()
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            p.fillRect(rect, Qt.GlobalColor.transparent)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            p.setPen(QPen(QColor(255, 30, 30), 3, Qt.PenStyle.DashLine))
            p.drawRect(rect)
            p.setPen(QColor(255, 200, 50))
            p.setFont(QFont("Consolas", 11))
            p.drawText(rect.x(), rect.y() - 5, f"{rect.width()}×{rect.height()}")
        p.end()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._origin = ev.pos()
            self._current = ev.pos()
            self._drawing = True
            self.update()

    def mouseMoveEvent(self, ev):
        if self._drawing:
            self._current = ev.pos()
            self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self._drawing:
            self._drawing = False
            rect = QRect(self._origin, self._current).normalized()
            if rect.width() > 5 and rect.height() > 5:
                tl = self.mapToGlobal(rect.topLeft())
                self.zone_selected.emit(tl.x(), tl.y(), rect.width(), rect.height())
            self.close()

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_Escape:
            self.close()


class ColorPicker(QWidget):
    """
    Пипетка: кликаешь по ГОЛУБОМУ ФОНУ выбранной кнопки «2».
    Скриншот экрана делается ДО показа оверлея, чтобы
    читать реальные пиксели, а не полупрозрачный фон.
    """
    color_picked = pyqtSignal(list)  # [h, s, v]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

        screen = QApplication.primaryScreen()
        # Скриншот ДО показа оверлея
        self._screenshot = screen.grabWindow(0) if screen else None

        if screen:
            self.setGeometry(screen.geometry())
        self.showFullScreen()

        self._preview_color = QColor(128, 128, 128)
        self._cursor_pos = QPoint(0, 0)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_preview)
        self._timer.start(30)

    def _update_preview(self):
        if not self._screenshot:
            return
        pos = QCursor.pos()
        self._cursor_pos = self.mapFromGlobal(pos)
        img = self._screenshot.toImage()
        if not img.isNull() and 0 <= pos.x() < img.width() and 0 <= pos.y() < img.height():
            self._preview_color = QColor(img.pixel(pos.x(), pos.y()))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        # Очень лёгкий затемнитель
        p.fillRect(self.rect(), QColor(0, 0, 0, 30))

        p.setPen(QColor(255, 60, 60))
        p.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
            "\n🎯 ПИПЕТКА — кликни по ГОЛУБОМУ ФОНУ выбранной «2»\n"
            "(сначала нажми «2» в дневнике чтобы фон стал голубым)\n[ESC] отмена")

        cx, cy = self._cursor_pos.x(), self._cursor_pos.y()

        # Перекрестие
        p.setPen(QPen(QColor(255, 255, 255, 120), 1, Qt.PenStyle.DashLine))
        p.drawLine(cx, 0, cx, self.height())
        p.drawLine(0, cy, self.width(), cy)

        # Инфо-панель у курсора
        ix = cx + 25
        iy = cy - 65
        if ix + 200 > self.width():
            ix = cx - 225
        if iy < 10:
            iy = cy + 25

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 210))
        p.drawRoundedRect(ix, iy, 200, 58, 8, 8)

        # Кружок цвета
        p.setBrush(self._preview_color)
        p.setPen(QPen(QColor(255, 255, 255), 2))
        p.drawEllipse(ix + 8, iy + 9, 40, 40)

        r, g, b = self._preview_color.red(), self._preview_color.green(), self._preview_color.blue()
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("Consolas", 10))
        p.drawText(ix + 58, iy + 23, f"R:{r} G:{g} B:{b}")
        p.drawText(ix + 58, iy + 43, f"#{r:02x}{g:02x}{b:02x}")
        p.end()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            hsv = self._pick_at(QCursor.pos())
            if hsv:
                self.color_picked.emit(hsv)
            self._timer.stop()
            self.close()

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_Escape:
            self._timer.stop()
            self.close()

    def _pick_at(self, pos) -> list:
        if not self._screenshot:
            return None
        img = self._screenshot.toImage()
        x, y = pos.x(), pos.y()
        if img.isNull() or x < 0 or y < 0 or x >= img.width() or y >= img.height():
            return None

        c = QColor(img.pixel(x, y))
        r, g, b = c.red(), c.green(), c.blue()

        try:
            import cv2
            pixel = np.uint8([[[b, g, r]]])
            hsv = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)
            return [int(hsv[0][0][0]), int(hsv[0][0][1]), int(hsv[0][0][2])]
        except ImportError:
            r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
            mx, mn = max(r_, g_, b_), min(r_, g_, b_)
            d = mx - mn
            if d == 0:
                h = 0
            elif mx == r_:
                h = 60 * (((g_ - b_) / d) % 6)
            elif mx == g_:
                h = 60 * (((b_ - r_) / d) + 2)
            else:
                h = 60 * (((r_ - g_) / d) + 4)
            s = 0 if mx == 0 else (d / mx) * 255
            v = mx * 255
            return [int(h / 2), int(s), int(v)]
