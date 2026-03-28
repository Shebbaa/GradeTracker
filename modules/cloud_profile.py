"""
Supabase: таблица profiles и операции для логина, лидерборда и метки читера.

Ожидаемые переменные окружения (или задайте константы ниже для сборки):
  INFERNO_SUPABASE_URL
  INFERNO_SUPABASE_KEY  — anon или service (см. SUPABASE_SETUP.md)
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

# ─── Подставьте свои значения при необходимости (env имеют приоритет) ───
_DEFAULT_URL = ""
_DEFAULT_KEY = ""


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def get_supabase_client():  # lazy import
    from supabase import create_client

    url = _env("INFERNO_SUPABASE_URL", _DEFAULT_URL)
    key = _env("INFERNO_SUPABASE_KEY", _DEFAULT_KEY)
    if not url or not key:
        return None
    return create_client(url, key)


def normalize_fio(s: str) -> str:
    return " ".join(s.strip().split())


def normalize_fio_key(s: str) -> str:
    return normalize_fio(s).lower()


# Первичная миграция «главного» преподавателя: если в облаке нет строки, создаём из локальных данных
SEEDED_ADMIN_FIO = "Аферов Андрей Алексеевич"
SEEDED_ADMIN_NICKNAME = "Аферова"


class CloudProfileService:
    """Обёртка над PostgREST Supabase для profiles."""

    def __init__(self, client):  # create_client(...) или None
        self._client = client

    @property
    def available(self) -> bool:
        return self._client is not None

    def fetch_by_fio(self, fio: str) -> dict[str, Any] | None:
        key = normalize_fio_key(fio)
        # Точное совпадение по каноническому fio в БД (при ручном вводе те же пробелы)
        rows = (
            self._client.table("profiles")
            .select("*")
            .eq("fio_key", key)
            .limit(1)
            .execute()
        )
        data = getattr(rows, "data", None) or []
        return data[0] if data else None

    def fetch_by_fio_relaxed(self, fio: str) -> dict[str, Any] | None:
        """Если fio_key не использовали — fallback на ilike по колонке fio."""
        nf = normalize_fio(fio)
        rows = (
            self._client.table("profiles")
            .select("*")
            .ilike("fio", nf)
            .limit(1)
            .execute()
        )
        data = getattr(rows, "data", None) or []
        return data[0] if data else None

    def insert_profile(
        self,
        fio: str,
        nickname: str,
        gold: int,
        keys: int,
        total_fives: int,
        title: str,
    ) -> dict[str, Any]:
        payload = {
            "id": str(uuid.uuid4()),
            "fio": normalize_fio(fio),
            "fio_key": normalize_fio_key(fio),
            "nickname": nickname.strip(),
            "gold": int(gold),
            "keys": int(keys),
            "total_fives": int(total_fives),
            "title": title,
            "is_cheater": False,
            "cheater_until": None,
        }
        self._client.table("profiles").insert(payload).execute()
        return payload

    def update_progress(
        self,
        profile_id: str,
        *,
        gold: int | None = None,
        keys: int | None = None,
        total_fives: int | None = None,
        title: str | None = None,
        is_cheater: bool | None = None,
        cheater_until: str | None = None,
    ) -> None:
        patch: dict[str, Any] = {}
        if gold is not None:
            patch["gold"] = int(gold)
        if keys is not None:
            patch["keys"] = int(keys)
        if total_fives is not None:
            patch["total_fives"] = int(total_fives)
        if title is not None:
            patch["title"] = title
        if is_cheater is not None:
            patch["is_cheater"] = bool(is_cheater)
        if cheater_until is not None:
            patch["cheater_until"] = cheater_until
        if not patch:
            return
        self._client.table("profiles").update(patch).eq("id", profile_id).execute()

    def mark_cheater_five_minutes(self, profile_id: str) -> dict[str, Any]:
        until = datetime.now(timezone.utc) + timedelta(minutes=5)
        iso = until.isoformat()
        self.update_progress(
            profile_id, is_cheater=True, cheater_until=iso
        )
        row = self.fetch_by_id(profile_id)
        return row or {"id": profile_id, "is_cheater": True, "cheater_until": iso}

    def fetch_by_id(self, profile_id: str) -> dict[str, Any] | None:
        rows = (
            self._client.table("profiles")
            .select("*")
            .eq("id", profile_id)
            .limit(1)
            .execute()
        )
        data = getattr(rows, "data", None) or []
        return data[0] if data else None

    def fetch_leaderboard(self, limit: int = 50) -> list[dict[str, Any]]:
        q = (
            self._client.table("profiles")
            .select("nickname,fio,total_fives,title")
            .order("total_fives", desc=True)
            .limit(limit)
        )
        rows = q.execute()
        return getattr(rows, "data", None) or []

    def reset_profile_progress_on_server(
        self,
        profile_id: str,
        *,
        gold: int,
        keys: int,
        title: str,
    ) -> None:
        """
        Обнуляет прогресс в облаке. Поля fio, fio_key, nickname, id не меняются.
        cheater_until сбрасывается в NULL через JSON.
        """
        patch = {
            "gold": int(gold),
            "keys": int(keys),
            "total_fives": 0,
            "title": title,
            "is_cheater": False,
            "cheater_until": None,
        }
        self._client.table("profiles").update(patch).eq("id", profile_id).execute()
