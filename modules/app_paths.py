"""
Пути данных приложения: %LOCALAPPDATA%/InfernoTracker/ (Windows) или XDG-подобный каталог.
Ассеты (bundled с Nuitka) остаются рядом с .exe; сюда переносятся только пользовательские данные.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def inferno_app_data_dir() -> Path:
    """Каталог пользовательских данных Inferno (создаётся при ensure)."""
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local) / "InfernoTracker"
    return Path.home() / ".local" / "share" / "InfernoTracker"


def ensure_inferno_dirs(app_data: Path | None = None) -> Path:
    d = app_data or inferno_app_data_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "screenshots").mkdir(parents=True, exist_ok=True)
    return d


def migrate_legacy_to_appdata(
    legacy_root: Path,
    app_data: Path,
) -> None:
    """
    Одноразовое копирование config.json, stats.json, inferno.db, users.json из старого корня
    (рядом с проектом / .exe), если в AppData ещё нет соответствующих файлов.
    """
    ensure_inferno_dirs(app_data)
    pairs = [
        ("config.json", app_data / "config.json"),
        ("users.json", app_data / "users.json"),
        ("stats.json", None),  # обрабатывается отдельно — будет .enc
        ("inferno.db", app_data / "inferno.db"),
        ("inferno.db.enc", app_data / "inferno.db.enc"),
    ]
    for name, dest in pairs:
        src = legacy_root / name
        if dest is None:
            continue
        if src.exists() and not dest.exists():
            try:
                shutil.copy2(src, dest)
                print(f"[MIGRATE] {src.name} -> {dest}")
            except OSError as e:
                print(f"[MIGRATE] skip {name}: {e}")

    # stats legacy: если есть plain stats.json, а зашифрованного кэша ещё нет
    from modules.secure_storage import SecureStorage

    legacy_stats = legacy_root / "stats.json"
    enc_stats = app_data / "stats.enc"
    if legacy_stats.exists() and not enc_stats.exists():
        try:
            import json

            with open(legacy_stats, "r", encoding="utf-8") as f:
                data = json.load(f)
            SecureStorage.save_json_encrypted(enc_stats, data)
            print(f"[MIGRATE] stats.json -> stats.enc")
        except Exception as e:
            print(f"[MIGRATE] stats encrypt: {e}")

    # скриншоты из старой папки (опционально)
    old_shots = legacy_root / "screenshots"
    new_shots = app_data / "screenshots"
    if old_shots.is_dir() and not any(new_shots.iterdir()):
        try:
            for src in old_shots.iterdir():
                if src.is_file():
                    shutil.copy2(src, new_shots / src.name)
            print(f"[MIGRATE] screenshots copied")
        except OSError as e:
            print(f"[MIGRATE] screenshots: {e}")


BASE_DIR = _base_dir()
APP_DATA_DIR = ensure_inferno_dirs(inferno_app_data_dir())
# Миграция при импорте (идемпотентна: не перезаписывает существующее в AppData)
migrate_legacy_to_appdata(BASE_DIR, APP_DATA_DIR)
