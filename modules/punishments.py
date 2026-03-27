"""
Inferno Grade Tracker — Micro-Event Punishments
Наказания за чрезмерную мягкость и другие «грехи».
"""
import random
import time

# ═══════════════════════════════════════════════════════════════
#  Правила наказаний
# ═══════════════════════════════════════════════════════════════
# 1) mercy_spam — слишком много помилований подряд (3+ за 3 минуты)
#    → «ПОСТАВЬ ДВОЙКУ ЗА 30 СЕКУНД!»
#    → если не ставишь: -1 двойка из сегодняшнего счёта
# 2) mercy_addict — 5+ помилований за день при <3 двоек
#    → «СЛАБАК! Лишаешься комбо-прогресса!»
#    → сброс combo-таймеров
# 3) idle_shame — 10+ минут детекция активна, но ни одной двойки
#    → «Ты что уснул? Двоек нет! Позор!»
#    → мотивационный «тычок» (просто сообщение)


PUNISHMENT_TYPES = {
    "mercy_spam": {
        "title": "\u26a0\ufe0f ВОЗДЕРЖАНИЕ - ГРЕХ!",
        "desc": "Слишком много помилований! Поставь двойку за {time}с\nили потеряешь -1 из сегодняшнего счёта!",
        "timeout_sec": 30,
        "penalty_desc": "\U0001f4a2 Штраф: -1 двойка сегодня!",
    },
    "mercy_addict": {
        "title": "\U0001f49a ЗАВИСИМОСТЬ ОТ МИЛОСТИ!",
        "desc": "Ты помиловал {mercy_today}× за день при {today} двойках.\nКомбо-прогресс обнулён!",
        "timeout_sec": 0,
        "penalty_desc": "\U0001f4a2 Комбо сброшено!",
    },
    "idle_shame": {
        "title": "\U0001f634 ПОЗОР ДИКТАТОРА!",
        "desc": "Детекция активна {minutes} мин — и ни одной двойки?\nГде твоя ярость?!",
        "timeout_sec": 0,
        "penalty_desc": "",
    },
}


class PunishmentEngine:
    """Движок наказаний. Проверяет условия и выдаёт события."""

    def __init__(self):
        self._mercy_timestamps = []  # время каждого помилования
        self._detection_start_ts = None
        self._last_two_ts = None
        self._last_punishment_ts = 0
        self._active_challenge = None  # текущий вызов (mercy_spam)
        self._challenge_deadline = 0

    def on_mercy(self, mercy_today: int, today_twos: int) -> dict | None:
        """Вызывается при каждом помиловании. Возвращает наказание или None."""
        now = time.time()
        self._mercy_timestamps.append(now)
        # Очищаем старые (>3 мин)
        self._mercy_timestamps = [t for t in self._mercy_timestamps if now - t < 180]

        # Защита от спама: не чаще 1 наказания в 60с
        if now - self._last_punishment_ts < 60:
            return None

        # mercy_spam: 3+ помилования за 3 минуты
        if len(self._mercy_timestamps) >= 3:
            self._last_punishment_ts = now
            self._active_challenge = "mercy_spam"
            self._challenge_deadline = now + PUNISHMENT_TYPES["mercy_spam"]["timeout_sec"]
            return {
                "type": "mercy_spam",
                "title": PUNISHMENT_TYPES["mercy_spam"]["title"],
                "desc": PUNISHMENT_TYPES["mercy_spam"]["desc"].format(
                    time=PUNISHMENT_TYPES["mercy_spam"]["timeout_sec"]
                ),
                "timeout_sec": PUNISHMENT_TYPES["mercy_spam"]["timeout_sec"],
            }

        # mercy_addict: 5+ помилований за день при <3 двоек
        if mercy_today >= 5 and today_twos < 3:
            self._last_punishment_ts = now
            return {
                "type": "mercy_addict",
                "title": PUNISHMENT_TYPES["mercy_addict"]["title"],
                "desc": PUNISHMENT_TYPES["mercy_addict"]["desc"].format(
                    mercy_today=mercy_today, today=today_twos
                ),
                "timeout_sec": 0,
            }
        return None

    def on_two_detected(self) -> bool:
        """Вызывается при двойке. Возвращает True если challenge выполнен."""
        now = time.time()
        self._last_two_ts = now
        # Даём 2с grace-период после дедлайна (на случай задержки детекции)
        if self._active_challenge == "mercy_spam" and now <= self._challenge_deadline + 2:
            self._active_challenge = None
            return True  # Спасён!
        return False

    def check_challenge_expired(self) -> dict | None:
        """Проверяет, истёк ли вызов. Вызывать раз в секунду."""
        if self._active_challenge != "mercy_spam":
            return None
        now = time.time()
        # Даём 2с grace-период после дедлайна для on_two_detected
        if now > self._challenge_deadline + 2:
            self._active_challenge = None
            return {
                "type": "mercy_spam_failed",
                "title": "\U0001f4a2 ПРОВАЛ!",
                "desc": PUNISHMENT_TYPES["mercy_spam"]["penalty_desc"],
            }
        # Возвращаем оставшееся время
        remaining = int(self._challenge_deadline - now)
        return {
            "type": "mercy_spam_countdown",
            "remaining": remaining,
        }

    def on_detection_start(self):
        self._detection_start_ts = time.time()

    def on_detection_stop(self):
        self._detection_start_ts = None

    def check_idle(self, detection_active: bool) -> dict | None:
        """Проверяет idle shame. Вызывать раз в минуту."""
        if not detection_active or self._detection_start_ts is None:
            return None
        now = time.time()
        elapsed_min = int((now - self._detection_start_ts) / 60)
        if elapsed_min >= 10:
            last = self._last_two_ts or self._detection_start_ts
            if now - last > 600:  # 10+ мин без двоек
                if now - self._last_punishment_ts > 300:  # не чаще 5 мин
                    self._last_punishment_ts = now
                    return {
                        "type": "idle_shame",
                        "title": PUNISHMENT_TYPES["idle_shame"]["title"],
                        "desc": PUNISHMENT_TYPES["idle_shame"]["desc"].format(
                            minutes=elapsed_min
                        ),
                        "timeout_sec": 0,
                    }
        return None

    @property
    def has_active_challenge(self) -> bool:
        return self._active_challenge is not None

    @property
    def challenge_type(self) -> str | None:
        return self._active_challenge
