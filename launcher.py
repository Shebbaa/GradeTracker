#!/usr/bin/env python3
"""
INFERNO GRADE TRACKER — Launcher v2
Окно загрузки: проверка обновлений (GitHub), Supabase, ассеты, хранилище.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

# ── High-DPI fix (до QApplication) ──────────────────────────────────
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
os.environ.setdefault("QT_SCALE_FACTOR", "1.0")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QLinearGradient,
    QBrush,
    QPen,
    QFont,
    QPixmap,
)

# ════════════════════════════════════════════════════════════════════
#  Константы
# ════════════════════════════════════════════════════════════════════
VERSION = "0.0.1"

# ── Замените на свои реквизиты GitHub ───────────────────────────────
GITHUB_OWNER = "Shebbaa"
GITHUB_REPO  = "InfernoGradeTracker"
GITHUB_API   = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# Таймауты запросов (сек)
REQUESTS_TIMEOUT_CHECK    = 8
REQUESTS_TIMEOUT_DOWNLOAD = 120

# Имя основного исполняемого файла рядом с лаунчером
APP_EXE_NAME = "InfernoGradeTracker.exe" if sys.platform == "win32" else "InfernoGradeTracker"

BASE_DIR      = Path(__file__).resolve().parent
ASSETS_DIR    = BASE_DIR / "assets"
LOGO_PATH     = ASSETS_DIR / "inferno_logo.png"
LOGO_ENC_PATH = ASSETS_DIR / "inferno_logo.png.enc"
APP_EXE_PATH  = BASE_DIR / APP_EXE_NAME
APP_NEW_PATH  = BASE_DIR / (APP_EXE_NAME + ".new")
APP_BAK_PATH  = BASE_DIR / (APP_EXE_NAME + ".bak")

WIN_W, WIN_H = 520, 400
FONT_FAMILY  = "'Segoe UI', 'Inter', 'Arial', sans-serif"
FONT_DISPLAY = "'Impact', 'Arial Black', 'Segoe UI Black', sans-serif"


# ════════════════════════════════════════════════════════════════════
#  Утилиты
# ════════════════════════════════════════════════════════════════════
def _parse_version(tag: str) -> tuple[int, ...]:
    """'v1.2.3' -> (1, 2, 3). Нечисловые части -> 0."""
    tag = tag.lstrip("vV").strip()
    parts = []
    for p in tag.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _is_newer(remote_tag: str, local: str = VERSION) -> bool:
    return _parse_version(remote_tag) > _parse_version(local)


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _kill_process_by_name(name: str) -> int:
    """Убивает все процессы с именем `name`. Возвращает кол-во убитых."""
    killed = 0

    # Попытка через psutil (самый надёжный способ)
    try:
        import psutil
        for proc in psutil.process_iter(["name", "pid"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() == name.lower():
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return killed
    except ImportError:
        pass

    # Фолбэк: системные команды
    if sys.platform == "win32":
        ret = os.system(f'taskkill /F /IM "{name}" >nul 2>&1')
        return 1 if ret == 0 else 0
    else:
        ret = os.system(f'pkill -f "{name}" 2>/dev/null')
        return 1 if ret == 0 else 0


# ════════════════════════════════════════════════════════════════════
#  Кастомный прогресс-бар
# ════════════════════════════════════════════════════════════════════
class InfernoProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(20)
        self._value       = 0
        self._phase       = 0.0
        self._downloading = False   # синий режим скачивания
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(45)

    def set_value(self, v: int):
        self._value = max(0, min(100, int(v)))
        self.update()

    def set_download_mode(self, on: bool):
        self._downloading = on
        self.update()

    def _tick(self):
        self._phase = (self._phase + 0.15) % 6.2832
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Фон
        p.setBrush(QColor(12, 3, 3, 220))
        p.setPen(QPen(QColor(80, 20, 20, 180), 1))
        p.drawRoundedRect(0, 0, w, h, 6, 6)

        fill_w = int(w * self._value / 100)
        if fill_w > 4:
            if self._downloading:
                # Синеватый градиент — режим скачивания
                grad = QLinearGradient(0, 0, fill_w, 0)
                grad.setColorAt(0.0, QColor(0,   60, 180, 210))
                grad.setColorAt(0.4, QColor(0,  120, 240, 235))
                grad.setColorAt(0.7, QColor(20, 180, 255, 255))
                grad.setColorAt(1.0, QColor(80, 220, 255, 255))
            else:
                # Огненный градиент — обычный режим
                grad = QLinearGradient(0, 0, fill_w, 0)
                grad.setColorAt(0.0,  QColor(180,  20,  0, 220))
                grad.setColorAt(0.35, QColor(220,  60,  0, 240))
                grad.setColorAt(0.65, QColor(255, 100, 10, 255))
                grad.setColorAt(1.0,  QColor(255, 160, 30, 255))

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(1, 1, fill_w - 2, h - 2, 5, 5)

            # Искры на переднем крае
            fx = fill_w - 3
            spark = QColor(120, 220, 255) if self._downloading else QColor(255, 200, 80)
            for i in range(7):
                ang = self._phase + i * 0.9
                fy  = (h / 2) + math.sin(ang) * (h / 2 - 2)
                a   = int(110 + 90 * abs(math.sin(ang * 1.5)))
                spark.setAlpha(a)
                p.setBrush(spark)
                p.drawEllipse(fx - 1, int(fy) - 1, 4, 4)

        # Рамка поверх
        p.setPen(QPen(QColor(180, 40, 0, 130), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(0, 0, w, h, 6, 6)
        p.end()


# ════════════════════════════════════════════════════════════════════
#  UpdateInfo — данные о найденном обновлении
# ════════════════════════════════════════════════════════════════════
class UpdateInfo:
    def __init__(
        self,
        available:    bool,
        tag:          str   = "",
        download_url: str   = "",
        size_bytes:   int   = 0,
        sha256:       str   = "",
        release_name: str   = "",
        error:        str   = "",
    ):
        self.available    = available
        self.tag          = tag
        self.download_url = download_url
        self.size_bytes   = size_bytes
        self.sha256       = sha256
        self.release_name = release_name
        self.error        = error


# ════════════════════════════════════════════════════════════════════
#  CheckWorker — все этапы запуска в одном фоновом потоке
# ════════════════════════════════════════════════════════════════════
class CheckWorker(QThread):
    """
    Сигналы
    -------
    step_update(pct, msg)              — текущий этап
    update_found(UpdateInfo)           — найдено обновление (ждём решения)
    download_progress(pct, kbs, eta)   — прогресс скачивания
    check_ok()                         — всё хорошо, запускаем апп
    check_fail(msg)                    — критическая ошибка
    """
    step_update       = pyqtSignal(int, str)
    update_found      = pyqtSignal(object)           # UpdateInfo
    download_progress = pyqtSignal(int, float, int)  # pct, KB/s, eta_sec
    check_ok          = pyqtSignal()
    check_fail        = pyqtSignal(str)

    def __init__(self, skip_update: bool = False):
        super().__init__()
        self._skip_update       = skip_update
        self._update_confirmed  = False
        self._update_skipped    = False

    # Вызываются из GUI-потока ─────────────────────────────────
    def confirm_update(self):
        self._update_confirmed = True

    def skip_update(self):
        self._update_skipped = True

    # Основной поток ─────────────────────────────────────────
    def run(self):
        try:
            self._run_all()
        except Exception as e:
            self.check_fail.emit(f"Критическая ошибка: {e}")

    def _run_all(self):
        # ── Этап 1: Проверка обновлений (GitHub) ─────────────
        if not self._skip_update:
            self.step_update.emit(3, "🔍 Проверка обновлений...")
            info = self._check_for_updates()

            if info.error:
                # Сеть недоступна / GitHub лежит — не критично, идём дальше
                self.step_update.emit(15, f"⚠ Обновления: {info.error} — пропущено")
                time.sleep(1.0)

            elif info.available:
                self.step_update.emit(15, f"🔔 Доступна версия {info.tag}!")
                self.update_found.emit(info)

                # Ждём решения пользователя (макс 30 с, потом пропускаем)
                deadline = time.time() + 30
                while not self._update_confirmed and not self._update_skipped:
                    if time.time() > deadline:
                        self._update_skipped = True
                    time.sleep(0.05)

                if self._update_confirmed:
                    ok = self._perform_update(info)
                    if not ok:
                        self.step_update.emit(22, "⚠ Обновление не удалось — запуск старой версии")
                        time.sleep(1.0)
                else:
                    self.step_update.emit(20, "Обновление пропущено")
                    time.sleep(0.3)

            else:
                self.step_update.emit(15, f"✔ Версия актуальна ({VERSION})")
                time.sleep(0.3)
        else:
            self.step_update.emit(15, "Проверка обновлений пропущена")
            time.sleep(0.2)

        # ── Этап 2: Supabase ─────────────────────────────────
        self.step_update.emit(25, "Связь с Supabase...")
        time.sleep(0.2)
        try:
            from modules.cloud_profile import get_supabase_client
            client = get_supabase_client()
            if client is None:
                self.check_fail.emit(
                    "Supabase не настроен.\n"
                    "Задайте INFERNO_SUPABASE_URL и INFERNO_SUPABASE_KEY."
                )
                return
            # Лёгкий ping
            client.table("profiles").select("id").limit(0).execute()
        except Exception as e:
            err = str(e)
            net_kw = ("StreamReset", "ConnectError", "ConnectionError",
                      "TimeoutError", "RemoteProtocolError", "NetworkError")
            if any(k in err for k in net_kw):
                self.check_fail.emit(
                    "Ошибка связи с преисподней.\n"
                    "Проверьте VPN / Интернет-соединение."
                )
            else:
                self.check_fail.emit(f"Supabase: {err}")
            return
        self.step_update.emit(50, "Supabase подключён ✔")
        time.sleep(0.2)

        # ── Этап 3: Ассеты ───────────────────────────────────
        self.step_update.emit(55, "Проверка ассетов...")
        time.sleep(0.1)
        if not ASSETS_DIR.exists():
            self.check_fail.emit(
                f"Папка ассетов не найдена:\n{ASSETS_DIR}\n\n"
                "Запускайте лаунчер из корневой папки проекта."
            )
            return
        self.step_update.emit(65, "Ассеты в порядке ✔")
        time.sleep(0.1)

        # ── Этап 4: SecureStorage / AppData ──────────────────
        self.step_update.emit(70, "Инициализация хранилища...")
        time.sleep(0.1)
        try:
            from modules.secure_storage import _get_key
            _get_key()
            from modules.app_paths import APP_DATA_DIR
            _ = APP_DATA_DIR
        except Exception as e:
            self.check_fail.emit(f"Хранилище: {e}")
            return
        self.step_update.emit(80, "Хранилище готово ✔")
        time.sleep(0.1)

        # ── Этап 5: Конфиг ───────────────────────────────────
        self.step_update.emit(85, "Авторизация преподавателя...")
        time.sleep(0.1)
        try:
            from modules.app_paths import APP_DATA_DIR as _apd
            cfg = _apd / "config.json"
            if cfg.exists():
                with open(cfg, "r", encoding="utf-8") as f:
                    json.load(f)
        except Exception:
            pass   # повреждённый конфиг — main.py создаст новый

        self.step_update.emit(95, "Готово к запуску ✔")
        time.sleep(0.25)

        self.step_update.emit(100, "🔥 Запуск Inferno...")
        time.sleep(0.4)
        self.check_ok.emit()

    # ── GitHub: проверка версии ──────────────────────────────
    def _check_for_updates(self) -> UpdateInfo:
        try:
            import requests
        except ImportError:
            return UpdateInfo(False, error="requests не установлен")

        try:
            resp = requests.get(
                GITHUB_API,
                timeout=REQUESTS_TIMEOUT_CHECK,
                headers={
                    "Accept":     "application/vnd.github+json",
                    "User-Agent": f"InfernoGradeTracker/{VERSION}",
                },
            )
        except Exception as e:
            return UpdateInfo(False, error=str(e)[:60])

        if resp.status_code == 404:
            return UpdateInfo(False, error="репозиторий не найден")
        if resp.status_code != 200:
            return UpdateInfo(False, error=f"HTTP {resp.status_code}")

        try:
            data = resp.json()
        except Exception:
            return UpdateInfo(False, error="плохой JSON от GitHub")

        tag  = data.get("tag_name", "")
        name = data.get("name", tag)

        if not _is_newer(tag):
            return UpdateInfo(False, tag=tag)

        # Ищем .exe в ассетах релиза
        assets  = data.get("assets", [])
        dl_url  = ""
        dl_size = 0

        # Точное совпадение имени
        for asset in assets:
            if asset.get("name", "").lower() == APP_EXE_NAME.lower():
                dl_url  = asset.get("browser_download_url", "")
                dl_size = asset.get("size", 0)
                break
        # Любой .exe
        if not dl_url:
            for asset in assets:
                if asset.get("name", "").lower().endswith(".exe"):
                    dl_url  = asset.get("browser_download_url", "")
                    dl_size = asset.get("size", 0)
                    break

        if not dl_url:
            return UpdateInfo(False, error="нет .exe в релизе")

        # SHA256 из тела релиза (строка вида "sha256: <hex64>")
        dl_sha = ""
        body   = data.get("body", "")
        for line in body.splitlines():
            if "sha256" in line.lower():
                parts = line.split()
                if parts and len(parts[-1]) == 64:
                    dl_sha = parts[-1]
                    break

        return UpdateInfo(
            available=True,
            tag=tag,
            download_url=dl_url,
            size_bytes=dl_size,
            sha256=dl_sha,
            release_name=name,
        )

    # ── Скачивание + горячая замена ─────────────────────────
    def _perform_update(self, info: UpdateInfo) -> bool:
        """Скачивает, проверяет хеш, заменяет exe. True = успех."""
        try:
            import requests
        except ImportError:
            self.step_update.emit(20, "❌ requests не установлен — пропуск")
            return False

        self.step_update.emit(20, f"⬇ Скачивание {info.tag}...")
        self.download_progress.emit(0, 0.0, 0)

        # Временный файл в той же папке (важно для cross-device rename)
        fd, tmp_str = tempfile.mkstemp(suffix=".tmp", prefix="inferno_upd_",
                                       dir=str(BASE_DIR))
        tmp_path = Path(tmp_str)
        os.close(fd)

        try:
            resp = requests.get(
                info.download_url,
                stream=True,
                timeout=REQUESTS_TIMEOUT_DOWNLOAD,
                headers={"User-Agent": f"InfernoGradeTracker/{VERSION}"},
            )
            resp.raise_for_status()

            total      = int(resp.headers.get("content-length", info.size_bytes or 0))
            downloaded = 0
            t_start    = time.time()
            CHUNK      = 64 * 1024   # 64 KB

            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=CHUNK):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)

                    elapsed   = max(0.001, time.time() - t_start)
                    speed_kbs = downloaded / elapsed / 1024
                    pct       = int(downloaded * 100 / total) if total else 0
                    eta       = int((total - downloaded) / (downloaded / elapsed)) \
                                if downloaded > 0 and total > 0 else 0
                    self.download_progress.emit(pct, speed_kbs, eta)

        except Exception as e:
            tmp_path.unlink(missing_ok=True)
            self.step_update.emit(20, f"❌ Ошибка скачивания: {str(e)[:55]}")
            time.sleep(1.5)
            return False

        # ── Проверка SHA-256 (если выложен в релизе) ─────────
        if info.sha256:
            self.step_update.emit(20, "🔒 Проверка целостности...")
            actual = _sha256(tmp_path)
            if actual.lower() != info.sha256.lower():
                tmp_path.unlink(missing_ok=True)
                self.step_update.emit(20, "❌ Хеш не совпал — файл повреждён")
                time.sleep(1.5)
                return False

        # ── Перемещаем во временный .new ─────────────────────
        try:
            APP_NEW_PATH.unlink(missing_ok=True)
            shutil.move(str(tmp_path), str(APP_NEW_PATH))
        except Exception as e:
            tmp_path.unlink(missing_ok=True)
            self.step_update.emit(20, f"❌ Сохранение не удалось: {str(e)[:50]}")
            time.sleep(1.0)
            return False

        # ── Горячая замена ────────────────────────────────────
        self.step_update.emit(20, "🔄 Замена файлов...")
        time.sleep(0.2)

        # Завершаем старый процесс
        _kill_process_by_name(APP_EXE_NAME)
        time.sleep(0.5)

        try:
            if APP_EXE_PATH.exists():
                APP_BAK_PATH.unlink(missing_ok=True)
                APP_EXE_PATH.rename(APP_BAK_PATH)
            APP_NEW_PATH.rename(APP_EXE_PATH)
        except Exception as e:
            # Откат: вернуть .bak если exe пропал
            if APP_BAK_PATH.exists() and not APP_EXE_PATH.exists():
                try:
                    APP_BAK_PATH.rename(APP_EXE_PATH)
                except Exception:
                    pass
            APP_NEW_PATH.unlink(missing_ok=True)
            self.step_update.emit(20, f"❌ Замена не удалась: {str(e)[:55]}")
            time.sleep(1.5)
            return False

        # Права исполнения (Linux/macOS)
        if sys.platform != "win32":
            try:
                APP_EXE_PATH.chmod(APP_EXE_PATH.stat().st_mode | 0o111)
            except Exception:
                pass

        self.step_update.emit(22, f"✔ Обновлено до {info.tag}!")
        time.sleep(0.6)
        return True


# ════════════════════════════════════════════════════════════════════
#  Главное окно лаунчера
# ════════════════════════════════════════════════════════════════════
class LauncherWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("INFERNO — Запуск")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(WIN_W, WIN_H)

        self._drag_pos   = None
        self._phase      = 0.0
        self._error_mode = False
        self._upd_info: Optional[UpdateInfo] = None
        self._worker: Optional[CheckWorker]  = None

        self._bg_timer = QTimer(self)
        self._bg_timer.timeout.connect(self._bg_tick)
        self._bg_timer.start(50)

        self._build_ui()
        self._center_on_screen()
        QTimer.singleShot(350, self._start_checks)

    # ── UI ───────────────────────────────────────────────────
    def _build_ui(self):
        ml = QVBoxLayout(self)
        ml.setContentsMargins(28, 18, 28, 18)
        ml.setSpacing(0)

        # Логотип
        self._logo_label = QLabel()
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_logo()
        ml.addWidget(self._logo_label)

        ml.addSpacing(6)

        # Заголовок
        title = QLabel("🔥  INFERNO GRADE TRACKER  🔥")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color:#ff3020; font-size:22px; font-weight:bold; "
            f"font-family:{FONT_DISPLAY}; letter-spacing:2px; background:transparent;"
        )
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(255, 50, 0, 200))
        glow.setBlurRadius(28)
        glow.setOffset(0, 0)
        title.setGraphicsEffect(glow)
        ml.addWidget(title)

        ml.addSpacing(2)

        # Версия
        self._ver_label = QLabel(f"v{VERSION}  •  Academic Dictator Edition")
        self._ver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ver_label.setStyleSheet(
            f"color:#552222; font-size:11px; letter-spacing:3px; "
            f"font-family:{FONT_FAMILY}; background:transparent;"
        )
        ml.addWidget(self._ver_label)

        ml.addSpacing(14)

        # Статус
        self._status_label = QLabel("Инициализация...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        self._status_label.setFixedHeight(48)
        self._status_label.setStyleSheet(
            f"color:#cc8844; font-size:13px; font-weight:bold; "
            f"font-family:{FONT_FAMILY}; background:transparent;"
        )
        ml.addWidget(self._status_label)

        ml.addSpacing(6)

        # Прогресс-бар
        self._progress = InfernoProgressBar()
        ml.addWidget(self._progress)

        ml.addSpacing(4)

        # Детали (процент + скорость)
        det_row = QHBoxLayout()
        self._pct_label = QLabel("0%")
        self._pct_label.setStyleSheet(
            f"color:#884422; font-size:11px; font-family:{FONT_FAMILY}; background:transparent;"
        )
        det_row.addWidget(self._pct_label)
        det_row.addStretch()
        self._speed_label = QLabel("")
        self._speed_label.setStyleSheet(
            f"color:#664422; font-size:10px; font-family:{FONT_FAMILY}; background:transparent;"
        )
        det_row.addWidget(self._speed_label)
        ml.addLayout(det_row)

        ml.addStretch(1)

        # Кнопки обновления (скрыты до нужного момента)
        self._upd_row = QHBoxLayout()
        self._upd_row.setSpacing(10)

        self._btn_update = QPushButton("⬇  Обновить сейчас")
        self._btn_update.setVisible(False)
        self._btn_update.setFixedHeight(40)
        self._btn_update.setStyleSheet(self._btn_style("#22aacc", "#1188aa"))
        self._btn_update.clicked.connect(self._on_confirm_update)
        self._upd_row.addWidget(self._btn_update)

        self._btn_skip_upd = QPushButton("→  Пропустить")
        self._btn_skip_upd.setVisible(False)
        self._btn_skip_upd.setFixedHeight(40)
        self._btn_skip_upd.setStyleSheet(self._btn_style("#886622", "#664400"))
        self._btn_skip_upd.clicked.connect(self._on_skip_update)
        self._upd_row.addWidget(self._btn_skip_upd)

        ml.addLayout(self._upd_row)

        # Кнопки ошибки (скрыты по умолчанию)
        self._err_row = QHBoxLayout()
        self._err_row.setSpacing(10)

        self._btn_retry = QPushButton("⟳  Повторить")
        self._btn_retry.setVisible(False)
        self._btn_retry.setFixedHeight(38)
        self._btn_retry.setStyleSheet(self._btn_style("#cc6622", "#882200"))
        self._btn_retry.clicked.connect(self._retry)
        self._err_row.addWidget(self._btn_retry)

        self._btn_exit = QPushButton("✖  Выход")
        self._btn_exit.setVisible(False)
        self._btn_exit.setFixedHeight(38)
        self._btn_exit.setStyleSheet(self._btn_style("#aa2222", "#660000"))
        self._btn_exit.clicked.connect(QApplication.quit)
        self._err_row.addWidget(self._btn_exit)

        ml.addLayout(self._err_row)

        ml.addSpacing(8)

        # Футер
        footer = QLabel(f"© Inferno Grade Tracker  •  Степан & Марк  •  v{VERSION}")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(
            f"color:#2a0a0a; font-size:9px; font-family:{FONT_FAMILY}; background:transparent;"
        )
        ml.addWidget(footer)

    @staticmethod
    def _btn_style(border: str, hover: str) -> str:
        return (
            f"QPushButton {{color:{border}; border:2px solid {border};"
            f"border-radius:7px; background:rgba(18,5,5,210);"
            f"font-size:13px; font-weight:bold; font-family:{FONT_FAMILY}; padding:6px 16px;}}"
            f"QPushButton:hover {{background:rgba(35,8,8,240); "
            f"border-color:{hover}; color:{hover};}}"
        )

    def _load_logo(self):
        pm = None
        if LOGO_ENC_PATH.exists():
            try:
                from modules.asset_loader import load_pixmap
                pm = load_pixmap(str(LOGO_ENC_PATH))
            except Exception:
                pm = None
        elif LOGO_PATH.exists():
            pm = QPixmap(str(LOGO_PATH))

        if pm and not pm.isNull():
            pm = pm.scaled(110, 72, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
            self._logo_label.setPixmap(pm)
            self._logo_label.setFixedHeight(78)
        else:
            self._logo_label.setText("🔥")
            self._logo_label.setFont(QFont("Segoe UI Emoji", 42))
            self._logo_label.setFixedHeight(64)

    # ── Фон ──────────────────────────────────────────────────
    def _bg_tick(self):
        self._phase = (self._phase + 0.06) % 6.2832
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(18,  3, 3, 252))
        grad.setColorAt(0.5, QColor(10,  0, 0, 255))
        grad.setColorAt(1.0, QColor(22,  5, 2, 252))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(1, 1, w - 2, h - 2, 14, 14)

        # Пульсирующая рамка
        ph    = self._phase
        pulse = 0.5 + 0.5 * math.sin(ph * 0.8)
        ba    = int(100 + 80 * pulse)

        if self._error_mode:
            bc = QColor(200, 0, 0, ba)
        elif self._upd_info and self._upd_info.available and not self._upd_info.error:
            bc = QColor(20, 120, 255, ba)     # синяя при обновлении
        else:
            bc = QColor(180, 40, 0, ba)       # огненная по умолчанию

        p.setPen(QPen(bc, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(1, 1, w - 2, h - 2, 14, 14)

        # Искры по нижнему краю
        if not self._error_mode:
            for i in range(18):
                ang = ph * 1.2 + i * 0.35
                fx  = int(30 + (w - 60) * i / 17 + math.sin(ang * 1.8) * 6)
                fa  = int(45 + 45 * math.sin(ang))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(255, random.randint(55, 135), 10, fa))
                p.drawEllipse(fx, h - 9, 3, 3)

        p.end()

    # ── Drag ─────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and (e.buttons() & Qt.MouseButton.LeftButton):
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None

    def _center_on_screen(self):
        scr = QApplication.primaryScreen()
        if scr:
            sg = scr.availableGeometry()
            self.move(
                (sg.width()  - self.width())  // 2 + sg.x(),
                (sg.height() - self.height()) // 2 + sg.y(),
            )

    # ── Запуск проверок ──────────────────────────────────────
    def _start_checks(self, skip_update: bool = False):
        self._error_mode = False
        self._upd_info   = None
        self._set_buttons(update=False, error=False)
        self._progress.set_value(0)
        self._progress.set_download_mode(False)
        self._pct_label.setText("0%")
        self._speed_label.setText("")
        self._set_status("Инициализация...", "#cc8844")

        self._worker = CheckWorker(skip_update=skip_update)
        self._worker.step_update.connect(self._on_step)
        self._worker.update_found.connect(self._on_update_found)
        self._worker.download_progress.connect(self._on_dl_progress)
        self._worker.check_ok.connect(self._on_ok)
        self._worker.check_fail.connect(self._on_fail)
        self._worker.start()

    def _set_status(self, text: str, color: str = "#cc8844"):
        self._status_label.setStyleSheet(
            f"color:{color}; font-size:13px; font-weight:bold; "
            f"font-family:{FONT_FAMILY}; background:transparent;"
        )
        self._status_label.setText(text)

    def _set_buttons(self, *, update: bool, error: bool):
        self._btn_update.setVisible(update)
        self._btn_skip_upd.setVisible(update)
        self._btn_retry.setVisible(error)
        self._btn_exit.setVisible(error)

    # ── Слоты воркера ────────────────────────────────────────
    def _on_step(self, pct: int, msg: str):
        self._progress.set_value(pct)
        self._pct_label.setText(f"{pct}%")
        # Если шагнули дальше скачивания — сбросить синий режим
        if pct > 23:
            self._progress.set_download_mode(False)
            self._speed_label.setText("")
        self._set_status(msg)

    def _on_update_found(self, info: UpdateInfo):
        """Найдено обновление — показываем кнопки выбора."""
        self._upd_info = info
        sz = info.size_bytes
        sz_str = f"  ({sz / 1024 / 1024:.1f} МБ)" if sz > 0 else ""
        self._set_status(
            f"🔔 Доступна версия {info.tag}{sz_str}\n{info.release_name}",
            color="#44aaff",
        )
        self._set_buttons(update=True, error=False)
        self.update()

    def _on_dl_progress(self, pct: int, kbs: float, eta: int):
        self._progress.set_download_mode(True)
        self._progress.set_value(pct)
        self._pct_label.setText(f"{pct}%")
        speed_str = f"{kbs / 1024:.1f} МБ/с" if kbs > 1024 else f"{kbs:.0f} КБ/с"
        eta_str   = f"  ~{eta}с" if eta > 0 else ""
        self._speed_label.setText(f"{speed_str}{eta_str}")

    def _on_ok(self):
        self._progress.set_value(100)
        self._pct_label.setText("100%")
        self._set_status("✔ Добро пожаловать в Ад", "#44ff88")
        QTimer.singleShot(600, self._launch_main)

    def _on_fail(self, msg: str):
        self._error_mode = True
        self._set_status(f"⚠️  {msg}", "#ff4040")
        self._set_buttons(update=False, error=True)
        self.update()

    # ── Обновление: действия пользователя ────────────────────
    def _on_confirm_update(self):
        self._set_buttons(update=False, error=False)
        self._set_status("⬇ Скачивание обновления...", "#44aaff")
        self._progress.set_download_mode(True)
        if self._worker:
            self._worker.confirm_update()

    def _on_skip_update(self):
        self._set_buttons(update=False, error=False)
        self._set_status("Обновление пропущено", "#886644")
        if self._worker:
            self._worker.skip_update()

    # ── Повтор / запуск ──────────────────────────────────────
    def _retry(self):
        if self._worker and self._worker.isRunning():
            return
        self._start_checks()

    def _launch_main(self):
        self.hide()

        if getattr(sys, "frozen", False):
            # Nuitka/PyInstaller: рядом лежит InfernoGradeTracker.exe
            target = APP_EXE_PATH
            flags  = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            if target.exists() and target.resolve() != Path(sys.executable).resolve():
                subprocess.Popen([str(target), "--launched-by-launcher"],
                                 creationflags=flags)
            else:
                # Лаунчер == основное приложение в одном exe
                subprocess.Popen([sys.executable, "--launched-by-launcher"],
                                 creationflags=flags)
        else:
            # Режим разработки — запускаем main.py напрямую
            main_py = BASE_DIR / "main.py"
            subprocess.Popen(
                [sys.executable, str(main_py), "--launched-by-launcher"],
                cwd=str(BASE_DIR),
            )

        QTimer.singleShot(400, QApplication.quit)


# ════════════════════════════════════════════════════════════════════
#  Entry point
# ════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Inferno Launcher")
    app.setQuitOnLastWindowClosed(True)

    win = LauncherWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
