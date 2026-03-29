#!/usr/bin/env python3
"""
Inferno Grade Tracker — Pre-build Asset Encryptor

Рекурсивно шифрует все медиа-файлы в /assets XOR-ключом,
меняет расширение на .enc, удаляет оригиналы.

Запуск ПЕРЕД сборкой Nuitka:
    python encrypt_assets.py          — зашифровать
    python encrypt_assets.py --decrypt — расшифровать обратно (для разработки)

После шифрования в /assets останутся только .enc файлы.
Даже при распаковке Nuitka --onefile они нечитаемы без ключа.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Используем тот же ключ, что и приложение
sys.path.insert(0, str(Path(__file__).resolve().parent))
from modules.secure_storage import encrypt_bytes, decrypt_bytes

ASSETS_DIR = Path(__file__).resolve().parent / "assets"

# Расширения медиа-файлов, которые шифруем
MEDIA_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp",  # Изображения
    ".mp3", ".wav", ".ogg",                              # Звуки
    ".mp4", ".avi", ".mkv", ".webm",                     # Видео
    ".ico",                                               # Иконки
}


def encrypt_assets(assets_dir: Path) -> int:
    """Зашифровать все медиа-файлы, удалить оригиналы. Возвращает число обработанных."""
    count = 0
    for f in sorted(assets_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
        # Уже зашифрован?
        enc_path = f.with_suffix(f.suffix + ".enc")
        if enc_path.exists():
            print(f"  [SKIP] {f.relative_to(assets_dir)} (уже есть .enc)")
            continue

        data = f.read_bytes()
        encrypted = encrypt_bytes(data)
        enc_path.write_bytes(encrypted)
        f.unlink()  # удаляем оригинал
        count += 1
        print(f"  [ENC]  {f.relative_to(assets_dir)} -> {enc_path.name}")
    return count


def decrypt_assets(assets_dir: Path) -> int:
    """Расшифровать .enc файлы обратно в оригиналы, удалить .enc. Для разработки."""
    count = 0
    for f in sorted(assets_dir.rglob("*.enc")):
        if not f.is_file():
            continue
        # Восстанавливаем оригинальное расширение: file.png.enc -> file.png
        original_path = f.with_suffix("")  # убираем .enc
        if original_path.suffix.lower() not in MEDIA_EXTENSIONS:
            print(f"  [SKIP] {f.relative_to(assets_dir)} (неизвестный формат)")
            continue
        if original_path.exists():
            print(f"  [SKIP] {f.relative_to(assets_dir)} (оригинал уже есть)")
            continue

        data = f.read_bytes()
        decrypted = decrypt_bytes(data)
        original_path.write_bytes(decrypted)
        f.unlink()
        count += 1
        print(f"  [DEC]  {f.relative_to(assets_dir)} -> {original_path.name}")
    return count


def main():
    parser = argparse.ArgumentParser(description="Encrypt/decrypt Inferno assets")
    parser.add_argument("--decrypt", action="store_true", help="Decrypt .enc back to originals")
    parser.add_argument("--dir", type=str, default=None, help="Custom assets directory")
    args = parser.parse_args()

    target = Path(args.dir) if args.dir else ASSETS_DIR
    if not target.is_dir():
        print(f"[ERROR] Directory not found: {target}")
        sys.exit(1)

    print(f"Assets directory: {target}")
    if args.decrypt:
        print("Mode: DECRYPT (.enc -> originals)\n")
        n = decrypt_assets(target)
        print(f"\nDecrypted: {n} files")
    else:
        print("Mode: ENCRYPT (originals -> .enc)\n")
        n = encrypt_assets(target)
        print(f"\nEncrypted: {n} files")
        if n > 0:
            print("\nОригиналы удалены. Для восстановления: python encrypt_assets.py --decrypt")


if __name__ == "__main__":
    main()
