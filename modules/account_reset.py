"""
Очистка локального прогресса в config (ачивки/коды/квесты/валюта), без ФИО и без настроек детекции.
"""
from __future__ import annotations

from modules.shop_manager import DEFAULT_GOLD, DEFAULT_KEYS

# Явный список префиксов/ключей прогресса в config
_EXTRA_PROGRESS_KEYS = frozenset(
    {
        "_code_fail",
        "_ominous_eyes",
        "_bottomless_star_clicked",
        "_sunset_days",
        "_villain_laser_streak",
        "_gacha_spins",
        "_themes_bought",
        "_bought_over_1000",
        "_bought_5000",
        "_sticker_count",
    }
)


def clear_config_account_progress(config: dict) -> None:
    """Удаляет ключи прогресса; золото/ключи — к дефолтам магазина; квест дня сбрасывается."""
    kill = [k for k in list(config.keys()) if k.startswith("_code_")]
    for k in kill:
        del config[k]
    for k in _EXTRA_PROGRESS_KEYS:
        config.pop(k, None)

    config["used_codes"] = []
    config["gacha_won_unique"] = []

    config["shop_gold"] = DEFAULT_GOLD
    config["shop_keys"] = DEFAULT_KEYS
    config["shop_pool"] = []
    config["shop_pool_timestamp"] = 0.0
    config["shop_last_free_gold"] = 0.0
    config["shop_last_free_key"] = 0.0
    config["streak_gold_date"] = ""

    config["daily_quest_date"] = ""
    config["daily_quest_id"] = ""
    config["daily_quest_completed_date"] = ""
    config["daily_bonus_date"] = ""
    config["daily_bonus_gold_per_two"] = 0
