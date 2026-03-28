"""
Inferno Grade Tracker — Sound Manager
Воспроизведение звуковых эффектов (демонический смех, взрывы, фразы).
Использует QSoundEffect из PyQt6 или pygame.mixer как фоллбэк.
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

SUPPORTED_AUDIO = {".wav", ".mp3", ".ogg"}


class SoundManager:
    """Менеджер звуков."""

    def __init__(self):
        self._enabled = True
        self._sounds = {}
        self._all_files = []
        self._sounds_root = SOUNDS_DIR
        self._player = None
        self._audio_output = None
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
            if f.is_file() and f.suffix.lower() in SUPPORTED_AUDIO
        ]
        # Категоризация по имени файла
        for f in self._all_files:
            name = f.stem.lower()
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
