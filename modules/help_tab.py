"""
Вкладка «Помощь» / Credits: авторы, контакты, ассеты из памяти (в т.ч. .enc).
"""
from __future__ import annotations

import math

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtGui import QColor, QFont

from modules.config import ASSETS_DIR
from modules.asset_loader import load_pixmap, load_movie


STEPAN_AVATAR = ASSETS_DIR / "avatarka_stepan.gif"
MARK_AVATAR = ASSETS_DIR / "avatarka_mark.png"
TELEGRAM_ICON = ASSETS_DIR / "telegram.png"


class AuthorCard(QFrame):
    """
    Карточка автора: скругление, тень, пульс/дыхание свечения, усиление при наведении.
    """

    def __init__(
        self,
        *,
        title: str,
        role: str,
        avatar_path,
        use_movie: bool,
        accent: QColor,
        variant: str,
        telegram: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("authorCard")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(320, 178)

        self._accent = QColor(accent)
        self._variant = variant
        self._hovering = False

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(18)
        self._shadow.setOffset(0, 5)
        self._shadow.setColor(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 130))
        self.setGraphicsEffect(self._shadow)

        self._timer = QTimer(self)
        self._timer.setInterval(90 if variant == "purple_pulse" else 140)
        self._timer.timeout.connect(self._tick_anim)
        self._glow_t = 0.0
        self._timer.start()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        title_l = QLabel(title)
        title_l.setFont(QFont("Impact", 14))
        title_l.setStyleSheet("color: #ffeedd; letter-spacing: 1px;")
        lay.addWidget(title_l)

        role_l = QLabel(role)
        role_l.setWordWrap(True)
        role_l.setStyleSheet(f"color: {self._accent.name()}; font-size: 11px; font-weight: bold;")
        lay.addWidget(role_l)

        row = QHBoxLayout()
        row.setSpacing(10)

        av = QLabel()
        av.setFixedSize(72, 72)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet("background: rgba(0,0,0,0.35); border-radius: 10px;")

        if use_movie:
            mv = load_movie(avatar_path)
            if mv:
                av.setMovie(mv)
                mv.start()
            else:
                pm = load_pixmap(avatar_path)
                if not pm.isNull():
                    av.setPixmap(
                        pm.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    )
        else:
            pm = load_pixmap(avatar_path)
            if not pm.isNull():
                av.setPixmap(
                    pm.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )

        row.addWidget(av)

        tg_row = QHBoxLayout()
        tg_ic = QLabel()
        tg_pm = load_pixmap(TELEGRAM_ICON)
        if not tg_pm.isNull():
            tg_ic.setPixmap(tg_pm.scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        tg_ic.setFixedSize(24, 24)
        tg_row.addWidget(tg_ic)
        h = QLabel(telegram)
        h.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        h.setStyleSheet("color: #88ccff;")
        tg_row.addWidget(h)
        tg_row.addStretch(1)
        row.addLayout(tg_row, 1)

        lay.addLayout(row)
        self._apply_style(0.5)

    def _tick_anim(self):
        if self._hovering:
            return
        self._glow_t += 0.11 if self._variant == "purple_pulse" else 0.07
        k = (math.sin(self._glow_t) + 1) * 0.5
        self._apply_style(k)
        br = 12 + k * (18 if self._variant == "purple_pulse" else 14)
        self._shadow.setBlurRadius(br + 6)

    def _apply_style(self, k: float):
        c = QColor(self._accent)
        c.setAlpha(int(100 + k * 110))
        self._shadow.setColor(c)
        border = QColor(self._accent)
        border.setAlpha(int(130 + k * 90))
        self.setStyleSheet(
            f"QFrame#authorCard {{"
            f"background: rgba(14, 8, 18, 230);"
            f"border: 2px solid {border.name()};"
            f"border-radius: 16px;"
            f"}}"
        )

    def enterEvent(self, event):
        self._hovering = True
        self._shadow.setBlurRadius(36)
        hc = QColor(self._accent)
        hc.setAlpha(240)
        self._shadow.setColor(hc)
        self.setFixedSize(334, 188)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovering = False
        self.setFixedSize(320, 178)
        super().leaveEvent(event)


def build_help_tab() -> QWidget:
    root = QWidget()
    outer = QVBoxLayout(root)
    outer.setContentsMargins(4, 4, 4, 4)
    outer.setSpacing(0)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

    inner = QWidget()
    inner.setStyleSheet("background:transparent;")
    vl = QVBoxLayout(inner)
    vl.setSpacing(16)
    vl.setContentsMargins(6, 8, 6, 12)

    hdr = QLabel(
        "Если заметите баги или хотите добавить другого преподавателя в наше приложение,\n"
        "напишите авторам."
    )
    hdr.setWordWrap(True)
    hdr.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    hdr.setFont(QFont("Impact", 12))
    hdr.setStyleSheet("color: #ff5533; letter-spacing: 0.5px; padding: 6px 4px;")
    hdr_shadow = QGraphicsDropShadowEffect(hdr)
    hdr_shadow.setBlurRadius(22)
    hdr_shadow.setColor(QColor(255, 60, 20, 200))
    hdr_shadow.setOffset(0, 0)
    hdr.setGraphicsEffect(hdr_shadow)
    vl.addWidget(hdr)

    row_stepan = QHBoxLayout()
    row_stepan.addStretch(1)
    stepan = AuthorCard(
        title="Степан",
        role="Разработчик технической части",
        avatar_path=STEPAN_AVATAR,
        use_movie=True,
        accent=QColor("#aa44ff"),
        variant="purple_pulse",
        telegram="@Shebbaaaa",
    )
    row_stepan.addWidget(stepan)
    row_stepan.addStretch(1)
    vl.addLayout(row_stepan)

    row_mark = QHBoxLayout()
    row_mark.addStretch(1)
    mark = AuthorCard(
        title="Марк",
        role="Разработчик контентной части",
        avatar_path=MARK_AVATAR,
        use_movie=False,
        accent=QColor("#44ddbb"),
        variant="mint_breath",
        telegram="@ElBiba",
    )
    row_mark.addWidget(mark)
    row_mark.addStretch(1)
    vl.addLayout(row_mark)

    vl.addStretch(1)
    scroll.setWidget(inner)
    outer.addWidget(scroll)
    return root
