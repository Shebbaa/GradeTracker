from __future__ import annotations

"""
Inferno Grade Tracker — Meme Manager
Загружает мемы/фотожабы из /assets/memes и /assets/custom_teacher.
Поддерживает PNG, JPG, GIF.
"""

import random
from pathlib import Path
from modules.config import MEMES_DIR, CUSTOM_DIR

SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


class MemeManager:
    """Менеджер мемов и фотожаб."""

    def __init__(self):
        self._memes_dir = MEMES_DIR
        self._custom_dir = CUSTOM_DIR
        self._memes = []
        self._custom = []
        self.reload()

    def set_asset_roots(self, memes_dir: Path | None = None, custom_dir: Path | None = None):
        """Переопределение каталогов (например assets/cheater_mod/...). None = стандарт из config."""
        self._memes_dir = memes_dir if memes_dir is not None else MEMES_DIR
        self._custom_dir = custom_dir if custom_dir is not None else CUSTOM_DIR
        self.reload()

    def reload(self):
        """Перезагрузить списки мемов из папок."""
        self._memes = self._scan_dir(self._memes_dir)
        self._custom = self._scan_dir(self._custom_dir)

    def _scan_dir(self, path: Path) -> list:
        if not path.exists():
            return []
        return [
            str(f) for f in path.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXT
        ]

    @property
    def all_memes(self) -> list:
        return self._memes + self._custom

    def get_random(self) -> str | None:
        """Случайный мем из обоих каталогов."""
        pool = self.all_memes
        if not pool:
            return None
        return random.choice(pool)

    def get_random_custom(self) -> str | None:
        """Случайная фотожаба из custom_teacher."""
        if not self._custom:
            return self.get_random()
        return random.choice(self._custom)

    @property
    def meme_count(self) -> int:
        return len(self.all_memes)

    @property
    def custom_count(self) -> int:
        return len(self._custom)
