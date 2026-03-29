"""
Inferno Grade Tracker — Sound Manager
Воспроизведение звуковых эффектов (демонический смех, взрывы, фразы).
Поддерживает как обычные аудио, так и зашифрованные .enc файлы.
"""

import random
from pathlib import Path
from PyQt6.QtCore import QUrl

try:
    from PyQt6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput
    _HAS_MULTIMEDIA = True
except ImportError:
    _HAS_MULTIMEDIA = False

from modules.config import SOUNDS_DIR
from modules.asset_loader import load_audio_buffer

SUPPORTED_AUDIO = {".wav", ".mp3", ".ogg"}
SUPPORTED_AUDIO_ENC = {ext + ".enc" for ext in SUPPORTED_AUDIO}
ALL_AUDIO = SUPPORTED_AUDIO | SUPPORTED_AUDIO_ENC


def _is_audio_file(f: Path) -> bool:
    name = f.name.lower()
    for ext in ALL_AUDIO:
        if name.endswith(ext):
            return True
    return False


def _stem_for_category(f: Path) -> str:
    """Получить имя файла без расширений (.enc и аудио)."""
    name = f.stem  # убирает последнее расширение
    if f.suffix.lower() == ".enc":
        name = Path(name).stem  # убираем ещё одно (.mp3)
    return name.lower()


class SoundManager:
    """Менеджер звуков."""

    def __init__(self):
        self._enabled = True
        self._sounds = {}
        self._all_files = []
        self._sounds_root = SOUNDS_DIR
        self._player = None
        self._audio_output = None
        self._current_buffer = None  # ссылка на QBuffer чтобы GC не убил
        self._scan_sounds()
        self._init_player()

    def set_sounds_root(self, root: Path | None = None):
        """Каталог звуков (режим клоуна — assets/cheater_mod/sounds). None — штатный SOUNDS_DIR."""
        self._sounds_root = root if root is not None else SOUNDS_DIR
        self._sounds.clear()
        self._scan_sounds()

    def _scan_sounds(self):
        """Сканирует папку sounds."""
        if not self._sounds_root.exists():
            return
        self._all_files = [
            f for f in self._sounds_root.iterdir()
            if f.is_file() and _is_audio_file(f)
        ]
        for f in self._all_files:
            name = _stem_for_category(f)
            if "laugh" in name or "смех" in name:
                self._sounds.setdefault("laugh", []).append(str(f))
            elif "explosion" in name or "взрыв" in name or "boom" in name:
                self._sounds.setdefault("explosion", []).append(str(f))
            elif "phrase" in name or "фраз" in name or "voice" in name:
                self._sounds.setdefault("phrase", []).append(str(f))
            elif "combo" in name or "комбо" in name:
                self._sounds.setdefault("combo", []).append(str(f))
            elif "alarm" in name or "сирен" in name:
                self._sounds.setdefault("alarm", []).append(str(f))
            else:
                self._sounds.setdefault("misc", []).append(str(f))

    def _init_player(self):
        if _HAS_MULTIMEDIA:
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)
            self._audio_output.setVolume(0.8)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, val: bool):
        self._enabled = val

    def play_random(self, category: str = None):
        """Играет случайный звук (опционально из категории)."""
        if not self._enabled:
            return
        if category and category in self._sounds:
            pool = self._sounds[category]
        else:
            pool = [str(f) for f in self._all_files]
        if not pool:
            return
        self._play_file(random.choice(pool))

    def play_for_level(self, level: int):
        """Играет звук, подходящий уровню реакции."""
        if not self._enabled:
            return
        if level >= 2:
            self.play_random("alarm") or self.play_random("explosion")
        elif level >= 1:
            self.play_random("combo") or self.play_random("explosion")
        else:
            self.play_random("laugh") or self.play_random("misc")

    def _play_file(self, path: str):
        if not _HAS_MULTIMEDIA or self._player is None:
            return
        try:
            p = Path(path)
            if p.suffix.lower() == ".enc":
                # Зашифрованный файл — расшифровываем в память
                buf = load_audio_buffer(p)
                if buf:
                    self._current_buffer = buf  # prevent GC
                    self._player.setSourceDevice(buf)
                    self._player.play()
            else:
                # Обычный файл
                self._current_buffer = None
                self._player.setSource(QUrl.fromLocalFile(path))
                self._player.play()
        except Exception:
            pass

    def stop(self):
        """Остановить воспроизведение."""
        if self._player:
            try:
                self._player.stop()
            except Exception:
                pass

    @property
    def sound_count(self) -> int:
        return len(self._all_files)

    @property
    def categories(self) -> list:
        return list(self._sounds.keys())
