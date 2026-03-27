"""
Daily quests + daily gold bonus per two.

Базовая идея:
- Раз в сутки пользователь выбирает один квест.
- После выполнения квеста активируется баф: +gold_per_two к каждому засчитанному "двоечному" событию (detect "двойка").
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from typing import Callable


@dataclass(frozen=True)
class QuestDef:
    id: str
    icon: str
    title: str
    goal_type: str  # "twos" | "mercy"
    goal_count: int
    reward_gold_per_two: int
    desc: str = ""


QUESTS: list[QuestDef] = [
    QuestDef(
        id="q_twos_5",
        icon="✋",
        title="Пять двоек",
        goal_type="twos",
        goal_count=5,
        reward_gold_per_two=15,
        desc="Поставь 5 двоек за сегодня.",
    ),
    QuestDef(
        id="q_twos_8",
        icon="🕳️",
        title="Воронка двоек",
        goal_type="twos",
        goal_count=8,
        reward_gold_per_two=15,
        desc="Поставь 8 двоек за сегодня.",
    ),
    QuestDef(
        id="q_mercy_3",
        icon="🕊️",
        title="Милость 3×",
        goal_type="mercy",
        goal_count=3,
        reward_gold_per_two=15,
        desc="Сделай 3 помилования за сегодня.",
    ),
    QuestDef(
        id="q_mercy_5",
        icon="💚",
        title="Милость 5×",
        goal_type="mercy",
        goal_count=5,
        reward_gold_per_two=15,
        desc="Сделай 5 помилований за сегодня.",
    ),
]


def _today_str() -> str:
    return date.today().isoformat()


class DailyQuestManager:
    def __init__(self, config: dict, stats, save_fn: Callable[[dict], None]):
        self.config = config
        self.stats = stats
        self.save_fn = save_fn
        self._ensure_keys()

    def _ensure_keys(self):
        self.config.setdefault("daily_quest_date", "")
        self.config.setdefault("daily_quest_id", "")
        self.config.setdefault("daily_quest_completed_date", "")
        self.config.setdefault("daily_bonus_date", "")
        self.config.setdefault("daily_bonus_gold_per_two", 0)

    def _save(self):
        self.save_fn(self.config)

    def _quest_by_id(self, quest_id: str) -> QuestDef | None:
        for q in QUESTS:
            if q.id == quest_id:
                return q
        return None

    def _seed_for_today(self) -> int:
        # deterministic daily options
        s = _today_str().replace("-", "")
        try:
            return int(s)
        except Exception:
            return 0

    def get_today_options(self, k: int = 3) -> list[QuestDef]:
        r = random.Random(self._seed_for_today())
        pool = list(QUESTS)
        # stable pick of k quests
        k = min(k, len(pool))
        r.shuffle(pool)
        return pool[:k]

    def get_selected_quest(self) -> QuestDef | None:
        if self.config.get("daily_quest_date") != _today_str():
            return None
        quest_id = self.config.get("daily_quest_id", "")
        if not quest_id:
            return None
        return self._quest_by_id(quest_id)

    def can_select_quest_today(self) -> bool:
        if self.config.get("daily_quest_date") != _today_str():
            return True
        return not bool(self.config.get("daily_quest_id"))

    def select_quest_today(self, quest_id: str) -> bool:
        q = self._quest_by_id(quest_id)
        if not q:
            return False
        if not self.can_select_quest_today():
            return False

        self.config["daily_quest_date"] = _today_str()
        self.config["daily_quest_id"] = quest_id
        # сбрасываем completion/bonus для "нового выбора" (если вдруг)
        self.config["daily_quest_completed_date"] = ""
        self.config["daily_bonus_date"] = ""
        self.config["daily_bonus_gold_per_two"] = 0
        self._save()
        return True

    def _get_progress_for_quest(self, quest: QuestDef) -> int:
        if quest.goal_type == "twos":
            return int(self.stats.get_today_count())
        if quest.goal_type == "mercy":
            return int(self.stats.mercy_today)
        return 0

    def get_progress(self) -> tuple[QuestDef | None, int, int]:
        quest = self.get_selected_quest()
        if not quest:
            return None, 0, 0
        cur = self._get_progress_for_quest(quest)
        return quest, cur, quest.goal_count

    def is_quest_completed_today(self) -> bool:
        return self.config.get("daily_quest_completed_date") == _today_str()

    def check_and_activate_bonus_if_completed(self) -> bool:
        """
        Проверяет выполнение квеста и, если выполнено впервые сегодня —
        активирует баф (+gold_per_two к каждой двойке).
        """
        quest, cur, goal = self.get_progress()
        if not quest:
            return False
        if cur < goal:
            return False

        today = _today_str()
        if self.config.get("daily_quest_completed_date") == today:
            return False

        self.config["daily_quest_completed_date"] = today
        self.config["daily_bonus_date"] = today
        self.config["daily_bonus_gold_per_two"] = int(quest.reward_gold_per_two)
        self._save()
        return True

    def is_bonus_active(self) -> bool:
        return self.config.get("daily_bonus_date") == _today_str() and int(self.config.get("daily_bonus_gold_per_two", 0)) > 0

    def gold_per_two(self) -> int:
        if not self.is_bonus_active():
            return 0
        return int(self.config.get("daily_bonus_gold_per_two", 0))

