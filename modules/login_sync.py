"""
Handshake после логина: сравнение локального золота/двоек с облаком, pull/push, анти-чит.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from modules.cloud_profile import CloudProfileService, normalize_fio_key, SEEDED_ADMIN_FIO, SEEDED_ADMIN_NICKNAME

# За одну «сессию» нельзя честно уйти дальше облака на такие величины (подстройте под баланс)
MAX_EXCESS_TWOS_VS_CLOUD = 45
MAX_EXCESS_GOLD_VS_CLOUD = 30000


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


def login_or_create_profile(
    svc: CloudProfileService,
    fio_input: str,
    *,
    local_total_twos: int,
    local_gold: int,
    local_keys: int,
    local_title: str,
) -> tuple[dict[str, Any], bool]:
    """
    Находит профиль или создаёт для SEEDED_ADMIN_FIO при первом запуске.
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

    raise PermissionError(
        "Преподаватель не найден в базе. Обратитесь к администратору для добавления профиля."
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
) -> LoginSyncResult:
    """
    Сравнивает прогресс; при подозрении на накрутку — mark_cheater и откат локали к облаку.
    """
    pid = profile["id"]
    cloud_twos = int(profile.get("total_fives", 0))
    cloud_gold = int(profile.get("gold", 0))
    cloud_keys = int(profile.get("keys", 0))

    excess_twos = local_total_twos - cloud_twos
    excess_gold = local_gold - cloud_gold

    cheater = False
    if not skip_anticheat and excess_twos > MAX_EXCESS_TWOS_VS_CLOUD:
        cheater = True
    if not skip_anticheat and excess_gold > MAX_EXCESS_GOLD_VS_CLOUD:
        cheater = True

    if cheater:
        svc.mark_cheater_five_minutes(pid)
        prof = svc.fetch_by_id(pid) or profile
        stats_manager.apply_cloud_counters(cloud_twos)
        config["shop_gold"] = cloud_gold
        config["shop_keys"] = cloud_keys
        save_config_fn()
        return LoginSyncResult(
            profile=prof,
            cheater_triggered=True,
            pulled_from_cloud=True,
            message="Обнаружен несоразмерный прирост прогресса. Активирован режим «клоуна» на 5 минут.",
        )

    pulled = False
    if cloud_twos > local_total_twos or cloud_gold > local_gold or cloud_keys > local_keys:
        stats_manager.apply_cloud_counters(cloud_twos)
        if cloud_gold > local_gold:
            config["shop_gold"] = cloud_gold
        if cloud_keys > local_keys:
            config["shop_keys"] = cloud_keys
        save_config_fn()
        pulled = True
        local_total_twos = cloud_twos
        local_gold = max(local_gold, cloud_gold)
        local_keys = max(local_keys, cloud_keys)

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
