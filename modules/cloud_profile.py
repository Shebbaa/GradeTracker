"""
Supabase: таблица profiles и операции для логина, лидерборда и метки читера.

Ожидаемые переменные окружения (или задайте константы ниже для сборки):
  INFERNO_SUPABASE_URL
  INFERNO_SUPABASE_KEY  — anon или service (см. SUPABASE_SETUP.md)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from modules.secure_storage import get_supabase_url, get_supabase_key


def get_supabase_client():  # lazy import
    from supabase import create_client

    url = get_supabase_url()
    key = get_supabase_key()
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

# Длительность режима наказания за накрутку (синхронизировать с login_sync / UI)
CHEATER_PUNISHMENT_MINUTES = 10


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
            "is_admin": False,
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
        cheat_local_snapshot: Any = None,
        legit_cloud_snapshot: Any = None,
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
        if cheat_local_snapshot is not None:
            patch["cheat_local_snapshot"] = cheat_local_snapshot
        if legit_cloud_snapshot is not None:
            patch["legit_cloud_snapshot"] = legit_cloud_snapshot
        if not patch:
            return
        self._client.table("profiles").update(patch).eq("id", profile_id).execute()

    def mark_cheater_punishment(
        self,
        profile_id: str,
        *,
        local_snapshot: dict[str, Any] | None = None,
        cloud_legit_snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        until = datetime.now(timezone.utc) + timedelta(minutes=CHEATER_PUNISHMENT_MINUTES)
        iso = until.isoformat()
        patch: dict[str, Any] = {"is_cheater": True, "cheater_until": iso}
        if local_snapshot is not None:
            patch["cheat_local_snapshot"] = local_snapshot
        if cloud_legit_snapshot is not None:
            patch["legit_cloud_snapshot"] = cloud_legit_snapshot
        self._client.table("profiles").update(patch).eq("id", profile_id).execute()
        row = self.fetch_by_id(profile_id)
        return row or {"id": profile_id, **patch}

    def finalize_cheater_punishment(self, profile_id: str) -> None:
        """После истечения таймера: снять флаги наказания в облаке."""
        self._client.table("profiles").update(
            {"is_cheater": False, "cheater_until": None}
        ).eq("id", profile_id).execute()

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
            .select("fio,total_fives,title")
            .eq("is_admin", False)
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
            "cheat_local_snapshot": None,
            "legit_cloud_snapshot": None,
        }
        self._client.table("profiles").update(patch).eq("id", profile_id).execute()
