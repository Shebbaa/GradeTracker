"""
Вкладка лидерборда: запрос к Supabase в фоне (QThread), таблица топа по total_fives.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from modules.config import get_rank
from modules.cloud_profile import CloudProfileService


class LeaderboardWorker(QThread):
    """Сетевой запрос без блокировки GUI."""

    rows_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, svc: CloudProfileService):
        super().__init__()
        self._svc = svc

    def run(self):
        try:
            rows = self._svc.fetch_leaderboard(80)
            self.rows_ready.emit(rows)
        except Exception as e:
            self.error.emit(str(e))


def _display_title(row: dict) -> str:
    t = (row.get("title") or "").strip()
    if t:
        return t
    n = int(row.get("total_fives") or 0)
    return get_rank(n)[0]


class LeaderboardTab(QWidget):
    def __init__(self, cloud_service: CloudProfileService, parent=None):
        super().__init__(parent)
        self._svc = cloud_service
        self._worker: LeaderboardWorker | None = None

        vl = QVBoxLayout(self)
        hl = QHBoxLayout()
        title = QLabel("Топ преподавателей по суммарным двойкам")
        title.setStyleSheet("font-weight:bold; font-size:13px; color:#ffaaaa;")
        hl.addWidget(title)
        hl.addStretch()
        self.btn_refresh = QPushButton("Обновить")
        self.btn_refresh.clicked.connect(self.refresh)
        hl.addWidget(self.btn_refresh)
        vl.addLayout(hl)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["#", "ФИО", "Двоек", "Титул"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #1a0c0c; color: #f0dede; gridline-color: #442222; "
            "alternate-background-color: #2a1515; selection-background-color: #553030; "
            "selection-color: #fff8f8; }"
            "QTableCornerButton::section { background: #2a1515; }"
            "QHeaderView::section { background-color: #301010; color: #ffcccc; padding: 4px; "
            "border: 1px solid #553333; font-weight: bold; }"
        )
        vl.addWidget(self.table)

        self.status = QLabel("")
        self.status.setStyleSheet("color:#886666; font-size:11px;")
        vl.addWidget(self.status)

        self.refresh()

    def refresh(self):
        if self._worker and self._worker.isRunning():
            return
        self.status.setText("Загрузка…")
        self.btn_refresh.setEnabled(False)
        self._worker = LeaderboardWorker(self._svc)
        self._worker.rows_ready.connect(self._on_rows)
        self._worker.error.connect(self._on_err)
        self._worker.finished.connect(lambda: self.btn_refresh.setEnabled(True))
        self._worker.start()

    def _on_rows(self, rows: list):
        fg = QBrush(QColor("#f0dede"))
        self.table.setRowCount(0)
        for i, row in enumerate(rows):
            self.table.insertRow(i)
            fio = (row.get("fio") or "").strip() or "—"
            twos = int(row.get("total_fives") or 0)
            tit = _display_title(row)

            it0 = QTableWidgetItem(str(i + 1))
            it0.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it1 = QTableWidgetItem(fio)
            it2 = QTableWidgetItem(str(twos))
            it2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it3 = QTableWidgetItem(tit)

            for it in (it0, it1, it2, it3):
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                it.setForeground(fg)

            self.table.setItem(i, 0, it0)
            self.table.setItem(i, 1, it1)
            self.table.setItem(i, 2, it2)
            self.table.setItem(i, 3, it3)

        self.status.setText(f"Записей: {len(rows)}")

    def _on_err(self, msg: str):
        self.status.setText(f"Ошибка: {msg}")
