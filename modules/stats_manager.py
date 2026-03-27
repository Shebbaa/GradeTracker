"""
Inferno Grade Tracker — Stats Manager (v3)
SQLite + JSON, стрики, комбо, рекорды, помилования.
"""

import sqlite3
import json
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from modules.config import (
    DB_PATH, STATS_JSON, ACHIEVEMENTS, get_rank,
    COMBO_WINDOW_SEC, MASS_COMBO_WINDOW_SEC,
)


class StatsManager:
    def __init__(self):
        self._db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._create_tables()
        self._load_cache()

    def _create_tables(self):
        c = self._db.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS twos_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL, date TEXT NOT NULL,
            screenshot_path TEXT, memo TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS achievements (
            id TEXT PRIMARY KEY, unlocked_ts REAL NOT NULL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS daily_summary (
            date TEXT PRIMARY KEY, count INTEGER DEFAULT 0,
            max_combo INTEGER DEFAULT 0, mercy_count INTEGER DEFAULT 0
        )""")
        # Миграция: добавляем mercy_count если нет
        try:
            c.execute("ALTER TABLE daily_summary ADD COLUMN mercy_count INTEGER DEFAULT 0")
        except Exception:
            pass
        self._db.commit()

    def _load_cache(self):
        if STATS_JSON.exists():
            try:
                with open(STATS_JSON, "r") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = self._default_cache()
        else:
            self._cache = self._default_cache()

        # Доп. защита от "админ-демо": если открытых ачивок в БД нет,
        # а в кэше очень большие значения — сбрасываем к реальным.
        try:
            ach_count = self._db.execute("SELECT COUNT(*) FROM achievements").fetchone()[0]
        except Exception:
            ach_count = 0
        if ach_count == 0 and int(self._cache.get("total", 0)) >= 1000:
            self._cache = self._default_cache()

        # Ensure all keys
        for k, v in self._default_cache().items():
            self._cache.setdefault(k, v)

    def _default_cache(self) -> dict:
        # Реальные значения по умолчанию (без "админ-режима").
        return {
            "total": 0,
            "streak": 0,
            "last_active_date": None,
            "max_combo": 0,
            "session_combos": 0,
            "recent_timestamps": [],
            "mercy_total": 0,
            "mercy_today": 0,
            "mercy_today_date": None,
            "last_mercy_ts": 0,
        }

    def _save_cache(self):
        with open(STATS_JSON, "w") as f:
            json.dump(self._cache, f, indent=2)

    # ═══ Запись двойки ═══════════════════════════════════════════════════
    def record_two(self, screenshot_path: str = None, memo: str = None) -> dict:
        now = time.time()
        today_str = date.today().isoformat()

        self._db.execute(
            "INSERT INTO twos_log (ts, date, screenshot_path, memo) VALUES (?,?,?,?)",
            (now, today_str, screenshot_path, memo)
        )

        row = self._db.execute(
            "SELECT count, max_combo FROM daily_summary WHERE date=?", (today_str,)
        ).fetchone()
        if row:
            new_count = row[0] + 1
            self._db.execute("UPDATE daily_summary SET count=? WHERE date=?", (new_count, today_str))
        else:
            new_count = 1
            self._db.execute("INSERT INTO daily_summary (date, count) VALUES (?,?)", (today_str, 1))
        self._db.commit()

        self._cache["total"] += 1
        self._cache["recent_timestamps"].append(now)
        cutoff = now - MASS_COMBO_WINDOW_SEC
        self._cache["recent_timestamps"] = [t for t in self._cache["recent_timestamps"] if t > cutoff]

        self._update_streak(today_str)

        combo_type = self._calc_combo(now)
        if combo_type == "mass":
            self._cache["session_combos"] = self._cache.get("session_combos", 0) + 1

        recent_count = len(self._cache["recent_timestamps"])
        if recent_count > self._cache["max_combo"]:
            self._cache["max_combo"] = recent_count
            self._db.execute("UPDATE daily_summary SET max_combo=? WHERE date=?", (recent_count, today_str))
            self._db.commit()

        # Проверка mercy_then_two: двойка в течение 60с после помилования
        mercy_then_two = False
        if self._cache.get("last_mercy_ts", 0) > 0:
            if now - self._cache["last_mercy_ts"] < 60:
                mercy_then_two = True

        self._save_cache()
        new_achs = self._check_achievements(mercy_then_two=mercy_then_two)

        reaction_level = {"single": 0, "double": 1, "mass": 2}.get(combo_type, 0)
        if self._cache["streak"] >= 15:
            reaction_level = max(reaction_level, 3)

        rank_name, rank_emoji = get_rank(self._cache["total"])

        return {
            "combo_type": combo_type,
            "total": self._cache["total"],
            "today": new_count,
            "streak": self._cache["streak"],
            "rank": rank_name,
            "rank_emoji": rank_emoji,
            "new_achievements": new_achs,
            "reaction_level": reaction_level,
            "max_combo": self._cache["max_combo"],
        }

    # ═══ Помилование ═════════════════════════════════════════════════════
    def record_mercy(self):
        """Записывает использование помилования."""
        today_str = date.today().isoformat()
        self._cache["mercy_total"] = self._cache.get("mercy_total", 0) + 1
        self._cache["last_mercy_ts"] = time.time()

        # Сброс mercy_today если другой день
        if self._cache.get("mercy_today_date") != today_str:
            self._cache["mercy_today"] = 0
            self._cache["mercy_today_date"] = today_str
        self._cache["mercy_today"] = self._cache.get("mercy_today", 0) + 1

        # В daily_summary
        row = self._db.execute(
            "SELECT mercy_count FROM daily_summary WHERE date=?", (today_str,)
        ).fetchone()
        if row:
            self._db.execute(
                "UPDATE daily_summary SET mercy_count=? WHERE date=?",
                (row[0] + 1, today_str)
            )
        else:
            self._db.execute(
                "INSERT INTO daily_summary (date, count, mercy_count) VALUES (?,0,1)",
                (today_str,)
            )
        self._db.commit()
        self._save_cache()

    @property
    def mercy_total(self) -> int:
        return self._cache.get("mercy_total", 0)

    @property
    def mercy_today(self) -> int:
        today_str = date.today().isoformat()
        if self._cache.get("mercy_today_date") != today_str:
            return 0
        return self._cache.get("mercy_today", 0)

    # ═══ Стрик (пропускает сб/вс) ═══════════════════════════════════════
    def _update_streak(self, today_str: str):
        last = self._cache.get("last_active_date")
        if last is None:
            self._cache["streak"] = 1
        else:
            last_date = date.fromisoformat(last)
            today_date = date.fromisoformat(today_str)
            delta = (today_date - last_date).days
            if delta == 0:
                pass
            elif delta == 1:
                self._cache["streak"] += 1
            elif delta <= 3 and last_date.weekday() == 4:
                self._cache["streak"] += 1
            else:
                self._cache["streak"] = 1
        self._cache["last_active_date"] = today_str

    def _calc_combo(self, now: float) -> str:
        recent = self._cache["recent_timestamps"]
        five = [t for t in recent if t > now - COMBO_WINDOW_SEC]
        ten = [t for t in recent if t > now - MASS_COMBO_WINDOW_SEC]
        if len(ten) >= 3:
            return "mass"
        if len(five) >= 2:
            return "double"
        return "single"

    # ═══ Ачивки ══════════════════════════════════════════════════════════
    def _check_achievements(self, mercy_then_two: bool = False) -> list:
        unlocked = set(r[0] for r in self._db.execute("SELECT id FROM achievements").fetchall())
        today_str = date.today().isoformat()
        stats = {
            "total": self._cache["total"],
            "today": self.get_today_count(),
            "streak": self._cache["streak"],
            "combos_today": self._cache.get("session_combos", 0),
            "max_combo": self._cache["max_combo"],
            "month": self.get_month_count(),
            "mercy_count": self._cache.get("mercy_total", 0),
            "mercy_today": self._cache.get("mercy_today", 0) if self._cache.get("mercy_today_date") == today_str else 0,
            "mercy_then_two": mercy_then_two,
        }
        new = []
        for ach in ACHIEVEMENTS:
            if ach["id"] not in unlocked:
                try:
                    if ach["condition"](stats):
                        self._db.execute(
                            "INSERT INTO achievements (id, unlocked_ts) VALUES (?,?)",
                            (ach["id"], time.time())
                        )
                        new.append(ach)
                except Exception:
                    pass
        if new:
            self._db.commit()
        return new

    def get_unlocked_achievements(self) -> list:
        unlocked_ids = set(r[0] for r in self._db.execute("SELECT id FROM achievements").fetchall())
        return [
            {**ach, "unlocked": (ach["id"] in unlocked_ids)}
            for ach in ACHIEVEMENTS
        ]

    # ═══ Статистика ══════════════════════════════════════════════════════
    def get_today_count(self) -> int:
        row = self._db.execute("SELECT count FROM daily_summary WHERE date=?", (date.today().isoformat(),)).fetchone()
        return row[0] if row else 0

    def get_week_count(self) -> int:
        d = (date.today() - timedelta(days=7)).isoformat()
        row = self._db.execute("SELECT COALESCE(SUM(count),0) FROM daily_summary WHERE date>=?", (d,)).fetchone()
        return row[0]

    def get_month_count(self) -> int:
        d = date.today().replace(day=1).isoformat()
        row = self._db.execute("SELECT COALESCE(SUM(count),0) FROM daily_summary WHERE date>=?", (d,)).fetchone()
        return row[0]

    def get_all_time_count(self) -> int:
        return self._cache.get("total", 0)

    def get_records(self) -> dict:
        max_day = self._db.execute("SELECT MAX(count) FROM daily_summary").fetchone()[0] or 0
        rows = self._db.execute("SELECT date, count FROM daily_summary ORDER BY date").fetchall()
        max_week = 0
        if rows:
            dc = [(date.fromisoformat(r[0]), r[1]) for r in rows]
            for i, (d, c) in enumerate(dc):
                ws = sum(cc for dd, cc in dc if 0 <= (d - dd).days < 7)
                max_week = max(max_week, ws)
        return {
            "max_day": max_day,
            "max_week": max_week,
            "max_combo": self._cache.get("max_combo", 0),
            "streak": self._cache.get("streak", 0),
            "total": self._cache["total"],
            "mercy_total": self._cache.get("mercy_total", 0),
        }

    def get_recent_log(self, limit: int = 50) -> list:
        rows = self._db.execute(
            "SELECT ts, date, memo FROM twos_log ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
        return [{"time": datetime.fromtimestamp(r[0]).strftime("%H:%M:%S"), "date": r[1], "memo": r[2] or ""} for r in rows]

    def deduct_one(self):
        """Штраф: вычитает 1 двойку из total, today и SQLite daily_summary."""
        if self._cache["total"] <= 0:
            return
        self._cache["total"] -= 1
        today_str = date.today().isoformat()
        row = self._db.execute(
            "SELECT count FROM daily_summary WHERE date=?", (today_str,)
        ).fetchone()
        if row and row[0] > 0:
            self._db.execute(
                "UPDATE daily_summary SET count=? WHERE date=?",
                (row[0] - 1, today_str)
            )
            self._db.commit()
        self._save_cache()

    @property
    def streak(self) -> int:
        return self._cache.get("streak", 0)

    @property
    def total(self) -> int:
        return self._cache.get("total", 0)

    def close(self):
        self._save_cache()
        self._db.close()
