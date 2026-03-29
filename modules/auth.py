"""
Inferno Grade Tracker — Auth Screen (v2, no registration)
Вход только по ФИО через Supabase (таблица profiles).
Регистрация — только через Supabase-админа.
Реферальный код коллеги вводится один раз при первом входе.
"""
from __future__ import annotations

import json

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import (
    QFont,
    QColor,
    QPainter,
    QLinearGradient,
    QBrush,
    QPen,
)

from modules.app_paths import APP_DATA_DIR
from modules.cloud_profile import CloudProfileService
from modules.login_sync import login_or_create_profile

USERS_FILE = APP_DATA_DIR / "users.json"
FONT_FAMILY = "'Segoe UI', 'Inter', 'Roboto', 'Arial', sans-serif"
FONT_FAMILY_DISPLAY = "'Impact', 'Arial Black', 'Segoe UI Black', sans-serif"


def _norm_fio(s: str) -> str:
    return " ".join(s.strip().split()).lower()


def load_users() -> list:
    if not USERS_FILE.exists():
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_users(users: list):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


class LoginWorker(QThread):
    """Сетевой логин (только LOGIN, без регистрации) вне GUI-потока."""

    finished_ok = pyqtSignal(dict, bool)
    finished_err = pyqtSignal(str)

    def __init__(
        self,
        fio: str,
        svc: CloudProfileService,
        snapshot: dict,
        referral_code: str = "",
    ):
        super().__init__()
        self._fio = fio
        self._svc = svc
        self._snapshot = snapshot
        self._referral_code = referral_code

    def run(self):
        try:
            # Всегда LOGIN — регистрация только через Supabase-админа
            prof, created = login_or_create_profile(
                self._svc,
                self._fio,
                local_total_twos=int(self._snapshot["total_twos"]),
                local_gold=int(self._snapshot["gold"]),
                local_keys=int(self._snapshot["keys"]),
                local_title=str(self._snapshot["title"]),
                register_mode=False,
                nickname="",
                referral_code=self._referral_code,
            )
            self.finished_ok.emit(prof, created)
        except PermissionError as e:
            # Преподаватель не найден в базе
            self.finished_err.emit(
                "Преподаватель не найден в базе.\n"
                "Обратитесь к администратору для регистрации."
            )
        except Exception as e:
            self.finished_err.emit(str(e))


class AuthScreen(QWidget):
    """Экран авторизации: ввод ФИО, проверка в Supabase.
    Регистрация — только через Supabase-админа (SQL/Table Editor).
    Реферальный код вводится один раз при первом входе."""

    auth_success = pyqtSignal(str, str, dict, bool)

    def __init__(
        self,
        parent=None,
        cloud_service: CloudProfileService | None = None,
        local_snapshot_fn=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("INFERNO — АВТОРИЗАЦИЯ")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 520)
        self._cloud = cloud_service
        self._local_snapshot_fn = local_snapshot_fn
        self._worker: LoginWorker | None = None
        self._build_ui()

    # ── Фон ──────────────────────────────────────────────────
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self.height()
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(20, 2, 2, 245))
        grad.setColorAt(0.5, QColor(10, 0, 0, 250))
        grad.setColorAt(1.0, QColor(25, 5, 3, 245))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)
        p.setPen(QPen(QColor(255, 30, 0, 160), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)
        p.end()

    # ── Построение UI ─────────────────────────────────────────
    def _build_ui(self):
        ml = QVBoxLayout(self)
        ml.setSpacing(10)
        ml.setContentsMargins(30, 25, 30, 25)

        # Заголовок
        title = QLabel("🔥 INFERNO 🔥")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color:#ff2020; font-size:36px; font-weight:bold; "
            f"font-family:{FONT_FAMILY_DISPLAY}; letter-spacing:3px;"
        )
        tg = QGraphicsDropShadowEffect()
        tg.setColor(QColor(255, 40, 0, 180))
        tg.setBlurRadius(30)
        tg.setOffset(0, 0)
        title.setGraphicsEffect(tg)
        ml.addWidget(title)

        sub = QLabel("GRADE TRACKER")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(
            f"color:#662222; font-size:14px; font-weight:bold; "
            f"font-family:{FONT_FAMILY}; letter-spacing:5px;"
        )
        ml.addWidget(sub)

        ml.addSpacing(10)

        INPUT_STYLE = f"""
            QLineEdit {{
                background: rgba(15,3,3,200);
                color: #ff8888;
                border: 2px solid #662222;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 15px;
                font-weight: bold;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border-color: #ff4040;
                color: #ffaaaa;
            }}
        """

        # ── ФИО ──
        fio_label = QLabel("Введите ФИО (как в базе кафедры):")
        fio_label.setStyleSheet(
            f"color:#aa6666; font-size:13px; font-weight:bold; font-family:{FONT_FAMILY};"
        )
        ml.addWidget(fio_label)

        self.fio_input = QLineEdit()
        self.fio_input.setPlaceholderText("Фамилия Имя Отчество")
        self.fio_input.setStyleSheet(INPUT_STYLE)
        self.fio_input.returnPressed.connect(self._try_submit)
        ml.addWidget(self.fio_input)

        # ── Реферальный код (только если ещё не был введён) ──
        self._ref_label = QLabel("Код коллеги (только при первом входе, необязательно):")
        self._ref_label.setStyleSheet(
            f"color:#aa6666; font-size:12px; font-weight:bold; font-family:{FONT_FAMILY};"
        )
        ml.addWidget(self._ref_label)

        self.referral_input = QLineEdit()
        self.referral_input.setPlaceholderText("Например: INFERNO-742")
        self.referral_input.setStyleSheet(INPUT_STYLE)
        self.referral_input.returnPressed.connect(self._try_submit)
        ml.addWidget(self.referral_input)

        # Примечание о регистрации
        reg_note = QLabel(
            "Нет аккаунта? Обратитесь к администратору."
        )
        reg_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        reg_note.setWordWrap(True)
        reg_note.setStyleSheet(
            f"color:#553333; font-size:10px; font-family:{FONT_FAMILY}; padding:4px 0;"
        )
        ml.addWidget(reg_note)

        # ── Ошибка ──
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color:#ff2020; font-size:12px; font-weight:bold;")
        self.error_label.setWordWrap(True)
        ml.addWidget(self.error_label)

        BTN_STYLE = f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(60,10,10,230), stop:1 rgba(25,3,3,220));
                color: #ff4040;
                border: 2px solid #cc2020;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: {FONT_FAMILY_DISPLAY};
            }}
            QPushButton:hover {{
                background: rgba(80,15,15,240);
                border-color: #ff4040;
                color: #ff6060;
            }}
            QPushButton:disabled {{
                color:#664444; border-color:#442222;
            }}
        """

        self.btn_submit = QPushButton("⚡ ВОЙТИ")
        self.btn_submit.setStyleSheet(BTN_STYLE)
        self.btn_submit.clicked.connect(self._try_submit)
        ml.addWidget(self.btn_submit)

        ml.addStretch()

    # ── Логика ───────────────────────────────────────────────
    def _hide_referral_if_used(self, config: dict | None = None):
        """Скрыть поле реферала если код уже был введён ранее."""
        if config and config.get("used_referral_code"):
            self._ref_label.setVisible(False)
            self.referral_input.setVisible(False)
        else:
            self._ref_label.setVisible(True)
            self.referral_input.setVisible(True)

    def _try_submit(self):
        self._try_auth()

    def _try_auth(self):
        if not self._cloud or not self._cloud.available:
            self._show_error(
                "Облако не настроено.\n"
                "Задайте INFERNO_SUPABASE_URL и INFERNO_SUPABASE_KEY."
            )
            self._shake()
            return

        fio_text = self.fio_input.text().strip()
        if not fio_text:
            self._show_error("Введите ФИО!")
            return

        if self._local_snapshot_fn is None:
            self._show_error("Внутренняя ошибка: нет снимка локальных данных.")
            return

        snap = self._local_snapshot_fn()
        ref = self.referral_input.text().strip()

        self.btn_submit.setEnabled(False)
        self.error_label.setText("Проверка в облаке…")

        self._worker = LoginWorker(
            fio_text,
            self._cloud,
            snap,
            referral_code=ref,
        )
        self._worker.finished_ok.connect(self._on_login_ok)
        self._worker.finished_err.connect(self._on_login_err)
        self._worker.finished.connect(self._on_worker_done)
        self._worker.start()

    def _on_worker_done(self):
        self.btn_submit.setEnabled(True)

    def _on_login_ok(self, prof: dict, created_new: bool):
        self.error_label.setText("")
        fio = prof.get("fio") or self.fio_input.text().strip()
        nick = prof.get("nickname") or "???"

        # Сигнал успеха (created_new всегда False для login-only)
        self.auth_success.emit(fio, nick, prof, False)
        self.hide()

    def _on_login_err(self, msg: str):
        self._show_error(msg)
        self._shake()

    def show(self):
        super().show()
        scr = QApplication.primaryScreen()
        if scr:
            sg = scr.availableGeometry()
            x = (sg.width() - self.width()) // 2 + sg.x()
            y = (sg.height() - self.height()) // 2 + sg.y()
            self.move(x, y)

    def _show_error(self, msg: str):
        self.error_label.setText(f"❌ {msg}")

    def _shake(self):
        self._shake_step = 0
        self._orig_pos = self.pos()
        self._shake_timer = QTimer(self)
        self._shake_timer.timeout.connect(self._shake_tick)
        self._shake_timer.start(30)

    def _shake_tick(self):
        self._shake_step += 1
        if self._shake_step > 10:
            self._shake_timer.stop()
            self.move(self._orig_pos)
            return
        import random
        dx = random.randint(-8, 8)
        self.move(self._orig_pos.x() + dx, self._orig_pos.y())

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if hasattr(self, "_drag_pos") and self._drag_pos:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
