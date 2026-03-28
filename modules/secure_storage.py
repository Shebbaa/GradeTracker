"""
Простое XOR-шифрование бинарных и JSON-файлов (ключ зашит в клиенте — защита от просмотра блокнотом, не от реверса).
Для прогресса и SQLite-базы используется общий ключ; config.json остаётся открытым текстом.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Длина кратна типичным блокам; для XOR достаточно любой ненулевой последовательности.
_XOR_KEY = b"InfernoGradeTrackerXorKey2026!!"


def _xor_bytes(data: bytes, key: bytes = _XOR_KEY) -> bytes:
    return bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))


class SecureStorage:
    """Обёртка: JSON в UTF-8 → XOR → файл; обратно для чтения."""

    @staticmethod
    def save_json_encrypted(path: Path, obj: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")
        path.write_bytes(_xor_bytes(raw))

    @staticmethod
    def load_json_encrypted(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            dec = _xor_bytes(path.read_bytes())
            return json.loads(dec.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            return None

    @staticmethod
    def encrypt_file_to(src_plain: Path, dest_enc: Path) -> None:
        """Читает весь plain-файл и пишет XOR-копию."""
        dest_enc.parent.mkdir(parents=True, exist_ok=True)
        data = src_plain.read_bytes()
        dest_enc.write_bytes(_xor_bytes(data))

    @staticmethod
    def decrypt_file_to(src_enc: Path, dest_plain: Path) -> None:
        """Восстанавливает plain-файл из XOR."""
        dest_plain.parent.mkdir(parents=True, exist_ok=True)
        data = _xor_bytes(src_enc.read_bytes())
        dest_plain.write_bytes(data)

    @staticmethod
    def xor_key() -> bytes:
        return _XOR_KEY
