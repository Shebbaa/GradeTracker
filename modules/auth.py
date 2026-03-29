"""
Inferno Grade Tracker — Auth Screen
Вход по ФИО через Supabase (таблица profiles). Локальная миграция для первого запуска Аферова.
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


def find_user(fio_input: str) -> dict | None:
    users = load_users()
    normalized = " ".join(fio_input.strip().split()).lower()
    for u in users:
        if " ".join(u["fio"].strip().split()).lower() == normalized:
            return u
    return None


def register_user(fio: str, nickname: str) -> dict:
    users = load_users()
    user = {"fio": fio.strip(), "nickname": nickname.strip()}
    users.append(user)
    save_users(users)
    return user


class LoginWorker(QThread):
    """Сетевой логин (создание/поиск профиля) вне GUI-потока."""

    finished_ok = pyqtSignal(dict, bool)
    finished_err = pyqtSignal(str)

    def __init__(
        self,
        fio: str,
        svc: CloudProfileService,
        snapshot: dict,
        *,
        register_mode: bool = False,
        nickname: str = "",
        referral_code: str = "",
    ):
        super().__init__()
        self._fio = fio
        self._svc = svc
        self._snapshot = snapshot
        self._register_mode = register_mode
        self._nickname = nickname
        self._referral_code = referral_code

    def run(self):
        try:
            prof, created = login_or_create_profile(
                self._svc,
                self._fio,
                local_total_twos=int(self._snapshot["total_twos"]),
                local_gold=int(self._snapshot["gold"]),
                local_keys=int(self._snapshot["keys"]),
                local_title=str(self._snapshot["title"]),
                register_mode=self._register_mode,
                nickname=self._nickname,
                referral_code=self._referral_code,
            )
            self.finished_ok.emit(prof, created)
        except Exception as e:
            self.finished_err.emit(str(e))


class AuthScreen(QWidget):
    """Экран авторизации: ввод ФИО, проверка в Supabase."""

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
        self.setFixedSize(420, 600)
        self._error_msg = ""
        self._shake_offset = 0
        self._register_mode = False
        self._cloud = cloud_service
        self._local_snapshot_fn = local_snapshot_fn
        self._worker: LoginWorker | None = None
        self._build_ui()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        _, h = self.width(), self.height()
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

    def _build_ui(self):
        ml = QVBoxLayout(self)
        ml.setSpacing(10)
        ml.setContentsMargins(30, 25, 30, 25)

        title = QLabel("\U0001f525 INFERNO \U0001f525")
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

        ml.addSpacing(15)

        INPUT_STYLE = f"""
            QLineEdit {{
                background: rgba(15,3,3,200);
                color: #ff8888;
                border: 2px solid #662222;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 16px;
                font-weight: bold;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border-color: #ff4040;
                color: #ffaaaa;
            }}
        """

        self.fio_label = QLabel("Введите ФИО (как в базе кафедры):")
        self.fio_label.setStyleSheet(
            f"color:#aa6666; font-size:13px; font-weight:bold; font-family:{FONT_FAMILY};"
        )
        ml.addWidget(self.fio_label)

        self.fio_input = QLineEdit()
        self.fio_input.setPlaceholderText("Фамилия Имя Отчество")
        self.fio_input.setStyleSheet(INPUT_STYLE)
        self.fio_input.returnPressed.connect(self._try_submit)
        ml.addWidget(self.fio_input)

        self.nick_label = QLabel("Никнейм (короткое имя):")
        self.nick_label.setStyleSheet(
            f"color:#aa6666; font-size:13px; font-weight:bold; font-family:{FONT_FAMILY};"
        )
        self.nick_label.setVisible(False)
        ml.addWidget(self.nick_label)

        self.nick_input = QLineEdit()
        self.nick_input.setPlaceholderText("Например: ИвановИ")
        self.nick_input.setStyleSheet(INPUT_STYLE)
        self.nick_input.setVisible(False)
        self.nick_input.returnPressed.connect(self._try_submit)
        ml.addWidget(self.nick_input)

        self.referral_label = QLabel("Код коллеги (реферал, необязательно):")
        self.referral_label.setStyleSheet(
            f"color:#aa6666; font-size:13px; font-weight:bold; font-family:{FONT_FAMILY};"
        )
        ml.addWidget(self.referral_label)

        self.referral_input = QLineEdit()
        self.referral_input.setPlaceholderText("Например: INFERNO-742")
        self.referral_input.setStyleSheet(INPUT_STYLE)
        self.referral_input.returnPressed.connect(self._try_submit)
        ml.addWidget(self.referral_input)

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

        self.btn_submit = QPushButton("\u26a1 ВОЙТИ")
        self.btn_submit.setStyleSheet(BTN_STYLE)
        self.btn_submit.clicked.connect(self._try_submit)
        ml.addWidget(self.btn_submit)

        self.btn_toggle_mode = QPushButton("Нет аккаунта? Регистрация")
        self.btn_toggle_mode.setStyleSheet(
            f"QPushButton{{border:none; color:#664444; font-size:12px; "
            f"font-family:{FONT_FAMILY}; background:transparent; padding:6px;}}"
            f"QPushButton:hover{{color:#ff6060;}}"
        )
        self.btn_toggle_mode.clicked.connect(self._toggle_mode)
        self.btn_toggle_mode.setVisible(True)
        ml.addWidget(self.btn_toggle_mode)

        ml.addStretch()

    def _toggle_mode(self):
        self._register_mode = not self._register_mode
        self.error_label.setText("")
        if self._register_mode:
            self.fio_label.setText("ФИО нового преподавателя:")
            self.nick_label.setVisible(True)
            self.nick_input.setVisible(True)
            self.referral_label.setVisible(True)
            self.referral_input.setVisible(True)
            self.btn_submit.setText("\U0001f4dd РЕГИСТРАЦИЯ")
            self.btn_toggle_mode.setText("Уже есть аккаунт? Войти")
        else:
            self.fio_label.setText("Введите ФИО (как в базе):")
            self.nick_label.setVisible(False)
            self.nick_input.setVisible(False)
            self.referral_label.setVisible(True)
            self.referral_input.setVisible(True)
            self.btn_submit.setText("\u26a1 ВОЙТИ")
            self.btn_toggle_mode.setText("Нет аккаунта? Регистрация")

    def _try_submit(self):
        self._try_auth()

    def _try_auth(self):
        if not self._cloud or not self._cloud.available:
            self._show_error("Облако не настроено. Задайте INFERNO_SUPABASE_URL и INFERNO_SUPABASE_KEY.")
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
        self.btn_submit.setEnabled(False)
        self.error_label.setText("Проверка в облаке…")
        nick = self.nick_input.text().strip() if self._register_mode else ""
        ref = self.referral_input.text().strip()
        self._worker = LoginWorker(
            fio_text,
            self._cloud,
            snap,
            register_mode=self._register_mode,
            nickname=nick,
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
        self.auth_success.emit(fio, nick, prof, created_new)
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

    def _show_error(self, msg):
        self.error_label.setText(f"\u274c {msg}")

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
