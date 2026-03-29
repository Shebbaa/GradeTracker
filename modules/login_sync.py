"""
Handshake после логина: сравнение локального золота/двоек с облаком, pull/push, анти-чит.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from modules.cloud_profile import (
    CloudProfileService,
    normalize_fio_key,
    SEEDED_ADMIN_FIO,
    SEEDED_ADMIN_NICKNAME,
    CHEATER_PUNISHMENT_MINUTES,
    REFERRAL_VETERAN_KEYS_BONUS,
)

# За одну «сессию» нельзя честно уйти дальше облака на такие величины (подстройте под баланс)
MAX_EXCESS_TWOS_VS_CLOUD = 45
MAX_EXCESS_GOLD_VS_CLOUD = 30000


def _config_looks_tampered(
    config: dict[str, Any],
    local_total_twos: int,
    cloud_twos: int,
    local_gold: int,
    cloud_gold: int,
) -> bool:
    """
    Грубая эвристика правки config.json: много золота/валюты при «замороженных» двойках относительно облака.
    """
    cg = int(config.get("shop_gold", 0))
    if cg > cloud_gold + MAX_EXCESS_GOLD_VS_CLOUD and local_total_twos <= cloud_twos + 2:
        return True
    if local_gold > cloud_gold + MAX_EXCESS_GOLD_VS_CLOUD and local_total_twos <= cloud_twos + 2:
        return True
    if config.get("_inferno_config_tamper"):
        return True
    return False


def _cheat_local_snapshot(
    config: dict[str, Any], local_total_twos: int, local_gold: int, local_keys: int
) -> dict[str, Any]:
    return {
        "total_twos": int(local_total_twos),
        "gold": int(local_gold),
        "keys": int(local_keys),
        "shop_gold_config": int(config.get("shop_gold", 0)),
        "shop_keys_config": int(config.get("shop_keys", 0)),
        "theme_id": config.get("theme_id"),
        "purchased_themes": list(config.get("shop_purchased_themes", [])),
    }


def _legit_cloud_snapshot(cloud_twos: int, cloud_gold: int, cloud_keys: int, title: str) -> dict[str, Any]:
    return {
        "total_fives": int(cloud_twos),
        "gold": int(cloud_gold),
        "keys": int(cloud_keys),
        "title": str(title),
    }


@dataclass
class LoginSyncResult:
    profile: dict[str, Any]
    cheater_triggered: bool
    pulled_from_cloud: bool
    message: str


def _parse_until(val: Any) -> datetime | None:
    if not val:
        return None
    if isinstance(val, datetime):
        dt = val
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    s = str(val).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def cheater_period_active(profile: dict[str, Any], now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    if not profile.get("is_cheater") and not profile.get("cheater_until"):
        return False
    until = _parse_until(profile.get("cheater_until"))
    if until and now < until:
        return True
    return bool(profile.get("is_cheater")) and until is None


def cheater_seconds_remaining(profile: dict[str, Any], now: datetime | None = None) -> int | None:
    """Сколько секунд осталось до конца наказания; None если таймер не по until."""
    now = now or datetime.now(timezone.utc)
    until = _parse_until(profile.get("cheater_until"))
    if until is None or now >= until:
        return None
    return max(0, int((until - now).total_seconds()))


def login_or_create_profile(
    svc: CloudProfileService,
    fio_input: str,
    *,
    local_total_twos: int,
    local_gold: int,
    local_keys: int,
    local_title: str,
    register_mode: bool = False,
    nickname: str = "",
    referral_code: str = "",
) -> tuple[dict[str, Any], bool]:
    """
    Находит профиль или создаёт для SEEDED_ADMIN_FIO при первом запуске,
    либо регистрирует нового преподавателя (register_mode).
    Возвращает (profile, created_new).
    """
    row = svc.fetch_by_fio(fio_input) or svc.fetch_by_fio_relaxed(fio_input)
    if row:
        return row, False

    if normalize_fio_key(fio_input) == normalize_fio_key(SEEDED_ADMIN_FIO):
        row = svc.insert_profile(
            SEEDED_ADMIN_FIO,
            SEEDED_ADMIN_NICKNAME,
            local_gold,
            local_keys,
            local_total_twos,
            local_title,
        )
        return row, True

    if register_mode:
        nick = (nickname or "").strip()
        if len(nick) < 2:
            raise ValueError("Введите никнейм (минимум 2 символа).")
        ref = (referral_code or "").strip()
        row = svc.register_new_user(
            fio_input,
            nick,
            local_gold,
            local_keys,
            local_total_twos,
            local_title,
            referral_code_input=ref if ref else None,
        )
        return row, True

    raise PermissionError(
        "Преподаватель не найден в базе. Воспользуйтесь «Регистрация» или обратитесь к администратору."
    )


def perform_handshake(
    svc: CloudProfileService,
    profile: dict[str, Any],
    *,
    config: dict[str, Any],
    local_total_twos: int,
    local_gold: int,
    local_keys: int,
    stats_title_fn: Callable[[], str],
    save_config_fn: Callable[[], None],
    stats_manager: Any,
    skip_anticheat: bool,
    created_new: bool = False,
) -> LoginSyncResult:
    """
    Сравнивает прогресс; при подозрении на накрутку — mark_cheater и откат локали к облаку.
    """
    pid = profile["id"]
    fresh = svc.fetch_by_id(pid) or profile
    cloud_twos = int(fresh.get("total_fives", 0))
    cloud_gold = int(fresh.get("gold", 0))
    cloud_keys = int(fresh.get("keys", 0))

    excess_twos = local_total_twos - cloud_twos
    excess_gold = local_gold - cloud_gold

    cheater = False
    if not skip_anticheat and excess_twos > MAX_EXCESS_TWOS_VS_CLOUD:
        cheater = True
    if not skip_anticheat and excess_gold > MAX_EXCESS_GOLD_VS_CLOUD:
        cheater = True
    if not skip_anticheat and _config_looks_tampered(
        config, local_total_twos, cloud_twos, local_gold, cloud_gold
    ):
        cheater = True

    if cheater:
        cloud_title = str(fresh.get("title") or stats_title_fn())
        legit = _legit_cloud_snapshot(cloud_twos, cloud_gold, cloud_keys, cloud_title)
        local_snap = _cheat_local_snapshot(config, local_total_twos, local_gold, local_keys)
        svc.mark_cheater_punishment(
            pid,
            local_snapshot=local_snap,
            cloud_legit_snapshot=legit,
        )
        prof = svc.fetch_by_id(pid) or fresh
        stats_manager.apply_cloud_counters(cloud_twos)
        config["shop_gold"] = cloud_gold
        config["shop_keys"] = cloud_keys
        config.pop("_inferno_config_tamper", None)
        save_config_fn()
        return LoginSyncResult(
            profile=prof,
            cheater_triggered=True,
            pulled_from_cloud=True,
            message=(
                f"Обнаружена накрутка или правка прогресса. Режим наказания на {CHEATER_PUNISHMENT_MINUTES} минут. "
                "Локальные счётчики приведены к данным Supabase."
            ),
        )

    pulled = False
    profile = fresh
    # Новый профиль в обладе (регистрация / сид): подтянуть кошелёк с сервера, иначе локаль перезапишет бонусы.
    if created_new:
        config["shop_gold"] = cloud_gold
        config["shop_keys"] = cloud_keys
        save_config_fn()
        local_gold = cloud_gold
        local_keys = cloud_keys

    # Бонус реферера (+ключ в облаке): подтянуть, не перетирая локаль при большой разнице
    # (если на сервере ровно на REFERRAL_VETERAN_KEYS_BONUS ключей больше — это типичный реферал).
    if (
        not created_new
        and cloud_keys > local_keys
        and (cloud_keys - local_keys) == REFERRAL_VETERAN_KEYS_BONUS
    ):
        config["shop_keys"] = cloud_keys
        save_config_fn()
        local_keys = cloud_keys

    # Только суммарные двойки подтягиваем из облака (восстановление прогресса).
    # Золото и инвентарь ключей НЕ перезаписываем с сервера при cloud > local — иначе
    # после траты ключей локально до 0 при следующем входе снова подставлялось значение из Supabase.
    if cloud_twos > local_total_twos:
        stats_manager.apply_cloud_counters(cloud_twos)
        save_config_fn()
        pulled = True

    title = stats_title_fn()
    svc.update_progress(
        pid,
        gold=int(config.get("shop_gold", 0)),
        keys=int(config.get("shop_keys", 0)),
        total_fives=stats_manager.total,
        title=title,
    )
    fresh = svc.fetch_by_id(pid) or profile
    return LoginSyncResult(
        profile=fresh,
        cheater_triggered=False,
        pulled_from_cloud=pulled,
        message="Синхронизация завершена.",
    )
