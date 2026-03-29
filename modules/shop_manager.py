"""
Inferno Grade Tracker — Shop Manager
Pure Python logic for the in-app shop: Theme Store, Gacha Roulette, Currency Exchange.
"""

import time
import random
import datetime

# ═══════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════

POOL_REFRESH_SECONDS = 2 * 60 * 60          # 2 hours
FREE_GOLD_COOLDOWN   = 15 * 60              # 15 minutes
FREE_KEY_COOLDOWN    = 24 * 60 * 60         # 24 hours

DEFAULT_GOLD = 0
DEFAULT_KEYS = 0

# All classic themes EXCEPT classic_candy (15 total)
CLASSIC_CANDIDATES = [
    "classic_ice", "classic_sakura", "classic_lemon", "classic_royal",
    "classic_ember", "classic_mint", "classic_blood", "classic_ocean",
    "classic_lime", "classic_lavender", "classic_copper", "classic_snow",
    "classic_coral", "classic_forest", "classic_steel", "classic_steel",
]
# De-duplicate just in case (classic_steel listed once)
CLASSIC_CANDIDATES = list(dict.fromkeys(CLASSIC_CANDIDATES))

# Only these elementals appear in the shop pool
ELEMENTAL_CANDIDATES = ["sunset", "retro", "villain", "fractal"]

# Neon themes that can appear as expensive cards in the pool
NEON_CANDIDATES = [
    "inferno_classic", "golden_emperor", "shadow_lord",
    "toxic_green", "inferno_blue", "void_purple", "hysteria",
]

# Fixed elemental prices
ELEMENTAL_PRICES = {
    "sunset":  2000,
    "retro":   2000,
    "villain": 3500,
    "fractal": 3500,
}

GOLDEN_EMPEROR_PRICE = 5000
GOLDEN_EMPEROR_CHANCE = 0.15  # 15 %

EXCHANGE_GOLD_PER_KEY = 250
# Сколько золота списать за 1 ключ (обратный обмен)
EXCHANGE_GOLD_FOR_ONE_KEY = 500

# One-time gacha prizes — can only be won once, then replaced with 150 gold
GACHA_UNIQUE_PRIZES = {"classic_candy", "ominous", "bottomless", "charged", "gold_1000"}

# Base gacha reward table  (type, value, weight)
# Weights sum to ~100 for clarity
_GACHA_TABLE_BASE = [
    ("theme",   "classic_candy", 8),
    ("gold",    100,            16),
    ("gold",    200,            10),
    ("gold",    250,             8),
    ("nothing", 0,              28),
    ("gold",    1000,            4),
    ("gold",    150,            14),
    ("sticker", None,           10),
    # Rare elemental themes (~0.67% each ≈ 2% total)
    ("theme",   "charged",       0.67),
    ("theme",   "bottomless",    0.67),
    ("theme",   "ominous",       0.66),
]

# Sticker IDs for gacha sticker prize
GACHA_STICKER_IDS = [
    "sticker_star", "sticker_fire", "sticker_skull",
    "sticker_crown", "sticker_diamond",
]


# ═══════════════════════════════════════════════════════════
#  ShopManager
# ═══════════════════════════════════════════════════════════

class ShopManager:
    """Manages shop state: currencies, theme pool, gacha, exchange."""

    def __init__(self, config: dict, save_fn):
        """
        Parameters
        ----------
        config : dict
            The application's loaded config dictionary (mutated in-place).
        save_fn : callable
            Function to persist the config (e.g. save_config).
        """
        self.config = config
        self.save_fn = save_fn
        self._ensure_defaults()

    # ── defaults ──────────────────────────────────────────

    def _ensure_defaults(self):
        defaults = {
            "shop_gold": DEFAULT_GOLD,
            "shop_keys": DEFAULT_KEYS,
            "shop_purchased_themes": [],
            "shop_pool": [],
            "shop_pool_timestamp": 0.0,
            "shop_last_free_gold": 0.0,
            "shop_last_free_key": 0.0,
            "gacha_won_unique": [],
            "streak_gold_date": "",
        }
        changed = False
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
                changed = True
        if changed:
            self._save()

    # ── persistence ───────────────────────────────────────

    def _save(self):
        """Persist current config to disk."""
        self.save_fn(self.config)

    # ── currencies ────────────────────────────────────────

    def get_gold(self) -> int:
        return self.config.get("shop_gold", DEFAULT_GOLD)

    def get_keys(self) -> int:
        return self.config.get("shop_keys", DEFAULT_KEYS)

    def add_gold(self, amount: int):
        self.config["shop_gold"] = self.get_gold() + amount
        self._save()

    def add_keys(self, amount: int):
        self.config["shop_keys"] = self.get_keys() + amount
        self._save()

    def spend_gold(self, amount: int) -> bool:
        """Deduct gold. Returns False if insufficient funds."""
        if self.get_gold() < amount:
            return False
        self.config["shop_gold"] = self.get_gold() - amount
        self._save()
        return True

    def spend_keys(self, amount: int) -> bool:
        """Deduct keys. Returns False if insufficient."""
        if self.get_keys() < amount:
            return False
        self.config["shop_keys"] = self.get_keys() - amount
        self._save()
        return True

    # ── purchased themes ──────────────────────────────────

    def get_purchased_themes(self) -> list[str]:
        return self.config.get("shop_purchased_themes", [])

    def is_theme_purchased(self, theme_id: str) -> bool:
        return theme_id in self.get_purchased_themes()

    def purchase_theme(self, theme_id: str, cost: int) -> bool:
        """Spend gold to purchase a theme. Returns True on success."""
        if self.is_theme_purchased(theme_id):
            return False
        if not self.spend_gold(cost):
            return False
        self.config.setdefault("shop_purchased_themes", []).append(theme_id)
        self._save()
        return True

    # ── theme pool ────────────────────────────────────────

    def get_theme_pool(self) -> list[str]:
        """Return the current store pool, refreshing if 2+ hours have passed."""
        ts = self.config.get("shop_pool_timestamp", 0.0)
        pool = self.config.get("shop_pool", [])
        if not pool or (time.time() - ts) >= POOL_REFRESH_SECONDS:
            self._refresh_pool()
        return self.config.get("shop_pool", [])

    def _refresh_pool(self):
        """Generate a new random pool — up to 3 classic cards, 20% chance one is expensive."""
        purchased = set(self.get_purchased_themes())
        TARGET = 3

        available_classics = [t for t in CLASSIC_CANDIDATES if t not in purchased]

        classic_count = min(TARGET, len(available_classics))
        pool = random.sample(available_classics, classic_count) if available_classics else []

        # 20% chance: replace one classic card with an elemental or neon theme
        if pool and random.random() < 0.20:
            available_expensive = (
                [t for t in ELEMENTAL_CANDIDATES if t not in purchased]
                + [t for t in NEON_CANDIDATES if t not in purchased]
            )
            if available_expensive:
                expensive_pick = random.choice(available_expensive)
                pool[-1] = expensive_pick

        random.shuffle(pool)

        self.config["shop_pool"] = pool
        self.config["shop_pool_timestamp"] = time.time()
        self._save()

    def get_theme_price(self, theme_id: str) -> int:
        """
        Pricing rules
        -------------
        Classic themes : 200 + 25 * (number of already-purchased classic themes)
        Elementals     : fixed per-theme price
        golden_emperor : 5000
        """
        if theme_id in ELEMENTAL_PRICES:
            return ELEMENTAL_PRICES[theme_id]
        if theme_id == "golden_emperor":
            return GOLDEN_EMPEROR_PRICE
        # Classic theme — price scales with how many classics you already own
        owned_classics = sum(
            1 for t in self.get_purchased_themes() if t in CLASSIC_CANDIDATES
        )
        return 200 + 25 * owned_classics

    def pool_time_remaining(self) -> int:
        """Seconds until the next pool refresh (0 if refresh is due)."""
        ts = self.config.get("shop_pool_timestamp", 0.0)
        elapsed = time.time() - ts
        remaining = POOL_REFRESH_SECONDS - elapsed
        return max(0, int(remaining))

    # ── gacha roulette ────────────────────────────────────

    def _get_gacha_table(self) -> list[tuple]:
        """
        Dynamically build the gacha table based on already-won unique prizes.
        One-time prizes that have been won are replaced with ("gold", 150, weight).
        """
        won = set(self.config.get("gacha_won_unique", []))
        table = []
        for rtype, rvalue, weight in _GACHA_TABLE_BASE:
            # Check if this entry is a one-time prize that was already won
            unique_key = None
            if rtype == "theme" and rvalue in GACHA_UNIQUE_PRIZES:
                unique_key = rvalue
            elif rtype == "gold" and rvalue == 1000 and "gold_1000" not in won:
                # gold_1000 not yet won — keep it
                table.append((rtype, rvalue, weight))
                continue
            elif rtype == "gold" and rvalue == 1000 and "gold_1000" in won:
                # gold_1000 already won — replace with 150 gold
                table.append(("gold", 150, weight))
                continue

            if unique_key and unique_key in won:
                # Already won this unique prize — replace with 150 gold
                table.append(("gold", 150, weight))
            else:
                table.append((rtype, rvalue, weight))
        return table

    def spin_gacha(self) -> dict:
        """
        Costs 1 key. Returns a dict describing the reward:
            {"type": "theme"|"gold"|"nothing"|"sticker", "value": <theme_id or int or 0>,
             "sticker_id": <str or None>}
        """
        if not self.spend_keys(1):
            return {"type": "nothing", "value": 0}

        gacha_table = self._get_gacha_table()

        # Weighted random pick
        total = sum(w for _, _, w in gacha_table)
        roll = random.uniform(0, total)
        cumulative = 0
        chosen_type, chosen_value = "nothing", 0
        for rtype, rvalue, weight in gacha_table:
            cumulative += weight
            if roll <= cumulative:
                chosen_type, chosen_value = rtype, rvalue
                break

        result = {"type": chosen_type, "value": chosen_value}

        # Apply reward
        if chosen_type == "gold":
            self.add_gold(chosen_value)
            # Track gold_1000 as unique win
            if chosen_value == 1000:
                won = self.config.get("gacha_won_unique", [])
                if "gold_1000" not in won:
                    won.append("gold_1000")
                    self.config["gacha_won_unique"] = won
                    self._save()
        elif chosen_type == "theme":
            if not self.is_theme_purchased(chosen_value):
                self.config.setdefault("shop_purchased_themes", []).append(chosen_value)
                # Track unique theme wins
                if chosen_value in GACHA_UNIQUE_PRIZES:
                    won = self.config.get("gacha_won_unique", [])
                    if chosen_value not in won:
                        won.append(chosen_value)
                        self.config["gacha_won_unique"] = won
                self._save()
            else:
                # Already own the theme — convert to gold consolation
                result["type"] = "gold"
                result["value"] = 300
                self.add_gold(300)
        elif chosen_type == "sticker":
            sticker_id = random.choice(GACHA_STICKER_IDS)
            result = {"type": "sticker", "sticker_id": sticker_id}

        return result

    # ── streak gold reward ────────────────────────────────

    def claim_streak_gold(self, streak_days: int) -> int:
        """
        If streak >= 2 days, awards 10 gold (once per calendar day).
        Returns the gold amount awarded (10) or 0 if not eligible.
        """
        if streak_days < 2:
            return 0

        today = datetime.date.today().isoformat()
        last_claim = self.config.get("streak_gold_date", "")
        if last_claim == today:
            return 0

        amount = 10
        self.add_gold(amount)
        self.config["streak_gold_date"] = today
        self._save()
        return amount

    # ── currency exchange ─────────────────────────────────

    def exchange_key_to_gold(self) -> bool:
        """Convert 1 key into 250 gold. Returns True on success."""
        if not self.spend_keys(1):
            return False
        self.add_gold(EXCHANGE_GOLD_PER_KEY)
        return True

    def exchange_gold_to_key(self) -> bool:
        """Spend gold to get 1 key. Returns False if not enough gold."""
        if self.get_gold() < EXCHANGE_GOLD_FOR_ONE_KEY:
            return False
        self.spend_gold(EXCHANGE_GOLD_FOR_ONE_KEY)
        self.add_keys(1)
        return True

    # ── free gold (every 15 minutes) ─────────────────────

    def can_claim_free_gold(self) -> bool:
        last = self.config.get("shop_last_free_gold", 0.0)
        return (time.time() - last) >= FREE_GOLD_COOLDOWN

    def claim_free_gold(self) -> int:
        """Claim 10-40 random gold. Returns the amount (0 if on cooldown)."""
        if not self.can_claim_free_gold():
            return 0
        amount = random.randint(10, 40)
        self.add_gold(amount)
        self.config["shop_last_free_gold"] = time.time()
        self._save()
        return amount

    def free_gold_seconds_remaining(self) -> int:
        last = self.config.get("shop_last_free_gold", 0.0)
        remaining = FREE_GOLD_COOLDOWN - (time.time() - last)
        return max(0, int(remaining))

    # ── free daily key (every 24 hours) ───────────────────

    def can_claim_free_key(self) -> bool:
        last = self.config.get("shop_last_free_key", 0.0)
        return (time.time() - last) >= FREE_KEY_COOLDOWN

    def claim_free_key(self) -> bool:
        """Claim 1 free key. Returns True on success, False if on cooldown."""
        if not self.can_claim_free_key():
            return False
        self.add_keys(1)
        self.config["shop_last_free_key"] = time.time()
        self._save()
        return True

    def free_key_seconds_remaining(self) -> int:
        last = self.config.get("shop_last_free_key", 0.0)
        remaining = FREE_KEY_COOLDOWN - (time.time() - last)
        return max(0, int(remaining))
