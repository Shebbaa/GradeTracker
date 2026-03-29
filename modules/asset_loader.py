"""
Inferno Grade Tracker — Encrypted Asset Loader

Расшифровывает .enc ассеты в оперативную память (без записи на диск).
Предоставляет PyQt6-объекты: QPixmap, QMovie, QBuffer для аудио.
"""
from __future__ import annotations

from pathlib import Path
from PyQt6.QtCore import QBuffer, QByteArray, QIODevice
from PyQt6.QtGui import QPixmap, QImage, QMovie

from modules.secure_storage import decrypt_bytes


# ─── Расширения, которые считаем зашифрованными ──────────────────────
IMAGE_EXT_ENC = {".png.enc", ".jpg.enc", ".jpeg.enc", ".bmp.enc", ".webp.enc"}
GIF_EXT_ENC = {".gif.enc"}
AUDIO_EXT_ENC = {".mp3.enc", ".wav.enc", ".ogg.enc"}


def _is_encrypted(path: Path) -> bool:
    return path.suffix.lower() == ".enc"


def _original_suffix(path: Path) -> str:
    """file.png.enc -> .png"""
    return Path(path.stem).suffix.lower()


def load_pixmap(path: str | Path) -> QPixmap:
    """
    Загрузить изображение: если .enc — расшифровать в память,
    иначе — обычная загрузка с диска (для режима разработки).
    Автоматически пробует .enc версию если оригинал не найден.
    """
    p = Path(path)
    if _is_encrypted(p):
        if not p.exists():
            return QPixmap()
        raw = decrypt_bytes(p.read_bytes())
        pm = QPixmap()
        pm.loadFromData(QByteArray(raw))
        return pm
    # Если обычный файл не существует — попробовать .enc
    if not p.exists():
        enc = p.with_suffix(p.suffix + ".enc")
        if enc.exists():
            raw = decrypt_bytes(enc.read_bytes())
            pm = QPixmap()
            pm.loadFromData(QByteArray(raw))
            return pm
    return QPixmap(str(p))


def load_movie(path: str | Path) -> QMovie | None:
    """
    Загрузить GIF-анимацию из .enc файла в память.
    QMovie требует QBuffer (QIODevice), который живёт пока живёт QMovie.
    """
    p = Path(path)
    if _is_encrypted(p):
        raw = decrypt_bytes(p.read_bytes())
        ba = QByteArray(raw)
        buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.ReadOnly)
        movie = QMovie()
        movie.setDevice(buf)
        movie.setFormat(b"GIF")
        # ВАЖНО: QBuffer должен жить пока живёт QMovie.
        # Привязываем буфер как атрибут, чтобы GC не собрал.
        movie._inferno_buffer = buf
        movie._inferno_data = ba
        if movie.isValid():
            return movie
        return None
    # Если обычный файл не существует — попробовать .enc
    if not p.exists():
        enc = p.with_suffix(p.suffix + ".enc")
        if enc.exists():
            return load_movie(enc)
    # Обычный файл (режим разработки)
    movie = QMovie(str(p))
    return movie if movie.isValid() else None


def load_audio_buffer(path: str | Path) -> QBuffer | None:
    """
    Расшифровать аудиофайл в QBuffer для QMediaPlayer.
    QMediaPlayer.setSourceDevice(buffer) — воспроизведение из RAM.

    Возвращает открытый QBuffer. Вызывающий код должен хранить ссылку на него.
    """
    p = Path(path)
    if _is_encrypted(p):
        raw = decrypt_bytes(p.read_bytes())
        ba = QByteArray(raw)
        buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.ReadOnly)
        # Привязываем данные чтобы GC не убил
        buf._inferno_data = ba
        return buf
    return None  # для незашифрованных файлов вызывающий использует fromLocalFile


def is_gif(path: str | Path) -> bool:
    """Проверить, является ли файл GIF (учитывая .enc)."""
    p = Path(path)
    if _is_encrypted(p):
        return _original_suffix(p) == ".gif"
    return p.suffix.lower() == ".gif"


def is_image(path: str | Path) -> bool:
    """Проверить, является ли файл изображением (не GIF)."""
    p = Path(path)
    if _is_encrypted(p):
        orig = _original_suffix(p)
        return orig in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    return p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def is_audio(path: str | Path) -> bool:
    """Проверить, является ли файл аудио."""
    p = Path(path)
    if _is_encrypted(p):
        return _original_suffix(p) in {".mp3", ".wav", ".ogg"}
    return p.suffix.lower() in {".mp3", ".wav", ".ogg"}
