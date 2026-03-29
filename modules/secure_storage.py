"""
Inferno Grade Tracker — Secure Storage v2

XOR-шифрование с рантайм-генерацией ключа.
Ключ НЕ хранится как строка — собирается из фрагментов при первом обращении.
Для ассетов (.enc) используется тот же алгоритм.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _assemble_key() -> bytes:
    """
    Собираем 31-байтный ключ XOR в рантайме из разрозненных фрагментов.
    Нигде в бинарнике нет одной строки с полным ключом.
    """
    # Фрагменты — маскировка от strings / .rodata
    _p0 = bytes([0x49, 0x6E, 0x66, 0x65])            # Infe
    _p1 = bytes([0x72, 0x6E, 0x6F, 0x47])            # rnoG
    _p2 = bytes([0x72, 0x61, 0x64, 0x65])            # rade
    _p3 = bytes([0x54, 0x72, 0x61, 0x63])            # Trac
    _p4 = bytes([0x6B, 0x65, 0x72])                   # ker

    # Вторая половина: "XorKey2026!!" через вычисления
    _p5 = bytes([0x58, 0x6F ^ 0x00, 0x72])           # Xor
    _p6 = bytes([0x4B, 0x65, 0x79])                   # Key
    # "2026" через арифметику
    _p7 = bytes([0x30 + 2, 0x30 + 0, 0x30 + 2, 0x30 + 6])  # 2026
    _p8 = bytes([0x21, 0x21])                          # !!

    return _p0 + _p1 + _p2 + _p3 + _p4 + _p5 + _p6 + _p7 + _p8


# Ленивый кэш — ключ вычисляется один раз
_KEY_CACHE: bytes | None = None


def _get_key() -> bytes:
    global _KEY_CACHE
    if _KEY_CACHE is None:
        _KEY_CACHE = _assemble_key()
    return _KEY_CACHE


def _xor_bytes(data: bytes, key: bytes | None = None) -> bytes:
    """XOR-шифрование/расшифрование (симметричное)."""
    if key is None:
        key = _get_key()
    kl = len(key)
    return bytes(data[i] ^ key[i % kl] for i in range(len(data)))


def decrypt_bytes(data: bytes) -> bytes:
    """Расшифровать байты (для ассетов, загружаемых в память)."""
    return _xor_bytes(data)


def encrypt_bytes(data: bytes) -> bytes:
    """Зашифровать байты."""
    return _xor_bytes(data)


class SecureStorage:
    """Обёртка: JSON → UTF-8 → XOR → файл; обратно для чтения."""

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
        dest_enc.parent.mkdir(parents=True, exist_ok=True)
        dest_enc.write_bytes(_xor_bytes(src_plain.read_bytes()))

    @staticmethod
    def decrypt_file_to(src_enc: Path, dest_plain: Path) -> None:
        dest_plain.parent.mkdir(parents=True, exist_ok=True)
        dest_plain.write_bytes(_xor_bytes(src_enc.read_bytes()))

    @staticmethod
    def xor_key() -> bytes:
        return _get_key()


# ─── Зашифрованные креденшиалы Supabase ───────────────────────────────
# Значения зашифрованы тем же XOR-ключом.
# Чтобы обновить: запусти _encrypt_credential("https://xxxxx.supabase.co")
# и вставь результат сюда как bytes-литерал.

# Placeholder — ЗАМЕНИ на реальные зашифрованные значения (см. инструкцию ниже)
_ENC_SUPABASE_URL: bytes = b'!\x1a\x12\x15\x01T@h\x1e\x17\x07\x176\x11\x15\x13\x13\x10\x17?\n\x1d!\x06\x17XJT\x18RT9\x0f\x04\x04\x01\x0bA$\x1dN'
_ENC_SUPABASE_KEY: bytes = b',\x17,\r\x10)\x0c.=\x08.,\x01\x08(R%\x0c;+&\x1c\x19P\x1aqy\x04\x7fJQ\x118%/K@\n>8\x11\x07V\x19\x1b.\n!\x1f\x16\x00-\x1a\x12\x08?Hja\x7fRh\'$\n?\x1b\'Y\x0e\x1f\x19V<g8\x08:X7\x05=\'$\'?KdFS[oT(\x00\x16\x08;\x07\x18.\x11\x0c]\x16\x0e!(U"\x084-\r@\x7f\x0c5qzBoyp !\x0c A \x15\x16@/ (g<%\x00\x18,\x1f\x0e[\x11\x08,O\x7fZs\x03le\x00\x16)1\x11^!tBO]#\x1874W)<\x010W8\x11\x01\x03^CScdG\x0c\x1d7\x16F\x1a<5=$\x01\'&6%\x0b</\x04\x1fB7'

def _encrypt_credential(plain: str) -> bytes:
    """Утилита: зашифровать строку для вставки в код. Вызывай из REPL."""
    return _xor_bytes(plain.encode("utf-8"))


def _decrypt_credential(enc: bytes) -> str:
    """Расшифровать креденшиал в рантайме."""
    if not enc:
        return ""
    return _xor_bytes(enc).decode("utf-8")


def get_supabase_url() -> str:
    """Получить URL Supabase (env имеет приоритет, иначе — зашитый)."""
    import os
    env = os.environ.get("INFERNO_SUPABASE_URL", "").strip()
    if env:
        return env
    return _decrypt_credential(_ENC_SUPABASE_URL)


def get_supabase_key() -> str:
    """Получить ключ Supabase (env имеет приоритет, иначе — зашитый)."""
    import os
    env = os.environ.get("INFERNO_SUPABASE_KEY", "").strip()
    if env:
        return env
    return _decrypt_credential(_ENC_SUPABASE_KEY)
