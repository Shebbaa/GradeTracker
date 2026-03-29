"""
Supabase: таблица profiles и операции для логина, лидерборда и метки читера.

Ожидаемые переменные окружения (или задайте константы ниже для сборки):
  INFERNO_SUPABASE_URL
  INFERNO_SUPABASE_KEY  — anon или service (см. SUPABASE_SETUP.md)
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from modules.secure_storage import get_supabase_url, get_supabase_key

# Реферальная система «Вербовщик Палачей»
REFERRAL_NEWBIE_GOLD_BONUS = 250
REFERRAL_NEWBIE_KEYS_BONUS = 1
REFERRAL_VETERAN_KEYS_BONUS = 1
REFERRAL_CODE_PREFIX = "INFERNO-"


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


def normalize_referral_code(s: str) -> str:
    return "".join(s.strip().upper().split())


def generate_referral_code() -> str:
    return f"{REFERRAL_CODE_PREFIX}{random.randint(100, 999)}"


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

    def fetch_by_referral_code(self, code: str) -> dict[str, Any] | None:
        key = normalize_referral_code(code)
        if not key:
            return None
        rows = (
            self._client.table("profiles")
            .select("*")
            .eq("referral_code", key)
            .limit(1)
            .execute()
        )
        data = getattr(rows, "data", None) or []
        return data[0] if data else None

    def count_successful_referrals(self, profile_id: str) -> int:
        """Сколько преподавателей пришло по коду этого профиля."""
        try:
            rows = (
                self._client.table("profiles")
                .select("id")
                .eq("referred_by", profile_id)
                .execute()
            )
            return len(getattr(rows, "data", None) or [])
        except Exception:
            return 0

    def ensure_referral_code(self, profile_id: str) -> str | None:
        """Гарантирует уникальный referral_code в облаке (для старых строк без кода)."""
        row = self.fetch_by_id(profile_id)
        if not row:
            return None
        existing = row.get("referral_code")
        if existing:
            return str(existing)
        for _ in range(40):
            code = generate_referral_code()
            try:
                self._client.table("profiles").update({"referral_code": code}).eq("id", profile_id).execute()
                return code
            except Exception:
                continue
        return None

    def insert_profile(
        self,
        fio: str,
        nickname: str,
        gold: int,
        keys: int,
        total_fives: int,
        title: str,
    ) -> dict[str, Any]:
        for _ in range(30):
            ref_code = generate_referral_code()
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
                "referral_code": ref_code,
                "referred_by": None,
            }
            try:
                self._client.table("profiles").insert(payload).execute()
                return payload
            except Exception:
                continue
        raise RuntimeError("Не удалось создать уникальный реферальный код профиля.")

    def register_new_user(
        self,
        fio: str,
        nickname: str,
        gold: int,
        keys: int,
        total_fives: int,
        title: str,
        referral_code_input: str | None = None,
    ) -> dict[str, Any]:
        """
        Новый преподаватель в базе. Опционально — бонусы за верный код коллеги.
        Новичок: +золото и +ключ; пригласивший: +ключ в облаке.
        """
        if self.fetch_by_fio(fio) or self.fetch_by_fio_relaxed(fio):
            raise ValueError("Профиль с таким ФИО уже зарегистрирован. Войдите.")

        inviter_id: str | None = None
        if referral_code_input and referral_code_input.strip():
            inv = self.fetch_by_referral_code(referral_code_input)
            if not inv:
                raise ValueError("Реферальный код не найден. Проверьте написание или оставьте поле пустым.")
            inviter_id = str(inv["id"])

        g, k = int(gold), int(keys)
        if inviter_id:
            g += REFERRAL_NEWBIE_GOLD_BONUS
            k += REFERRAL_NEWBIE_KEYS_BONUS

        payload: dict[str, Any] | None = None
        for _ in range(30):
            ref_code = generate_referral_code()
            payload = {
                "id": str(uuid.uuid4()),
                "fio": normalize_fio(fio),
                "fio_key": normalize_fio_key(fio),
                "nickname": nickname.strip(),
                "gold": g,
                "keys": k,
                "total_fives": int(total_fives),
                "title": title,
                "is_cheater": False,
                "cheater_until": None,
                "is_admin": False,
                "referral_code": ref_code,
                "referred_by": inviter_id,
            }
            try:
                self._client.table("profiles").insert(payload).execute()
                break
            except Exception:
                continue
        if payload is None:
            raise RuntimeError("Не удалось зарегистрировать профиль (код).")

        if inviter_id:
            inv = self.fetch_by_id(inviter_id)
            if inv:
                new_keys = int(inv.get("keys", 0)) + REFERRAL_VETERAN_KEYS_BONUS
                self.update_progress(inviter_id, keys=new_keys)

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
