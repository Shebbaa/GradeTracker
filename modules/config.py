"""
Inferno Grade Tracker — Config (v5)
Ачивки с категориями, прогрессом. Ранги. Реакции. Фразы.
"""
import os, sys, json
from pathlib import Path
from datetime import datetime

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = BASE_DIR / "assets"
MEMES_DIR = ASSETS_DIR / "memes"
SOUNDS_DIR = ASSETS_DIR / "sounds"
CUSTOM_DIR = ASSETS_DIR / "custom_teacher"
DB_PATH = BASE_DIR / "inferno.db"
STATS_JSON = BASE_DIR / "stats.json"
CONFIG_JSON = BASE_DIR / "config.json"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
for d in [MEMES_DIR, SOUNDS_DIR, CUSTOM_DIR, SCREENSHOTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

COMBO_WINDOW_SEC = 300
MASS_COMBO_WINDOW_SEC = 600

# ─── Ранги ───────────────────────────────────────────────────────────
RANKS = [
    (0,    "Новичок-диктатор",               "🔰"),
    (10,   "Суровый преподаватель",           "⚔️"),
    (25,   "Мелкий тиран",                   "🪓"),
    (35,   "Жестокий правитель",              "👑"),
    (50,   "Инквизитор оценок",              "🔥"),
    (75,   "Каратель зачёток",               "🗡️"),
    (100,  "Ангел Смерти",                   "🩸"),
    (125,  "Макиавелли ведомости",           "🏴"),
    (200,  "Тиран стипендий",                "💀"),
    (300,  "Тракторист ведомости",           "🚜"),
    (350,  "Чёрный канцлер",                 "🦇"),
    (400,  "Отряд 731",                      "🧪"),
    (500,  "Верховный каратель",             "☠️"),
    (666,  "Люцифер зачёток",               "😈"),
    (767,  "Шестьсот шестьдесят семь проблем","🤡"),
    (888,  "Большой Брат",                   "👁️"),
    (1000, "Абсолютный Диктатор Академии",   "👁️"),
    (1488, "Фюрер ведомостей",               "卐"),
    (2000, "Бог этого ада",                  "🌑"),
]

def get_rank(total):
    rank = RANKS[0]
    for t, n, e in RANKS:
        if total >= t: rank = (n, e)
    return rank

def get_rank_progress(total):
    ci = 0
    for i, (t, n, e) in enumerate(RANKS):
        if total >= t: ci = i
    if ci >= len(RANKS) - 1:
        return (RANKS[-1][1], 100, "МАКСИМУМ")
    ct, nt = RANKS[ci][0], RANKS[ci + 1][0]
    p = int((total - ct) / (nt - ct) * 100)
    return (RANKS[ci][1], min(p, 100), RANKS[ci + 1][1])

# ─── Ачивки с категориями ────────────────────────────────────────────
# category: "bestiary" | "combo" | "streak" | "mercy"
# progress_key + progress_target → для прогресс-бара
# tier: "legendary" → особый стиль, "secret" → полностью скрытый текст
ACHIEVEMENTS = [
    # ══ БЕСТИАРИЙ ЖЕРТВ (bestiary) ══
    {"id": "first_blood", "name": "Первый раз всегда больно", "desc": "Поставь первую двойку. Студент уже понял, что это не Tinder",
     "icon": "🩸", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 1,
     "condition": lambda s: s["total"] >= 1},
    {"id": "ten_victims", "name": "Сталинский список №10", "desc": "10 двоек суммарно. Первая чистка завершена",
     "icon": "🪦", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 10,
     "condition": lambda s: s["total"] >= 10},
    {"id": "thirteen", "name": "Чёртова дюжина", "desc": "13 двоек суммарно. Не к добру, студент",
     "icon": "👿", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 13,
     "condition": lambda s: s["total"] >= 13},
    {"id": "twenty_graves", "name": "Гулаг на 20 коек", "desc": "20 двоек суммарно. Места уже заняты",
     "icon": "⚰️", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 20,
     "condition": lambda s: s["total"] >= 20},
    {"id": "thirty_tears", "name": "Тридцать лет Колымы", "desc": "30 двоек суммарно. Студенты уже пишут жалобы в ЦК",
     "icon": "😭", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 30,
     "condition": lambda s: s["total"] >= 30},
    {"id": "forty_lashes", "name": "Сорок ударов плетью", "desc": "40 двоек суммарно. Студенты уже красные",
     "icon": "🪢", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 40,
     "condition": lambda s: s["total"] >= 40},
    {"id": "fifty_skulls", "name": "Чикатило ведомости", "desc": "56 двоек суммарно.",
     "icon": "💀", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 56,
     "condition": lambda s: s["total"] >= 56},
    {"id": "sixty_nine", "name": "69 — классика", "desc": "69 двоек суммарно. Nice.",
     "icon": "🍑", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 69,
     "condition": lambda s: s["total"] >= 69},
    {"id": "hundred_souls", "name": "Коллекционер душ", "desc": "100 двоек суммарно.",
     "icon": "👻", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 100,
     "condition": lambda s: s["total"] >= 100},
    {"id": "one_fifty", "name": "Полторы сотни жертв", "desc": "150 двоек суммарно. Теперь ты официально хуже 1937-го",
     "icon": "🦴", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 150,
     "condition": lambda s: s["total"] >= 150},
    {"id": "two_hundred", "name": "Я твой отец… и двойка", "desc": "200 двоек суммарно. Дарту Вейдеру и не снилось",
     "icon": "🌑", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 200,
     "condition": lambda s: s["total"] >= 200},
    {"id": "two_fifty", "name": "Четверть миллиона репрессий", "desc": "250 двоек суммарно. Студенты уже зовут тебя «Папочка 2.0»",
     "icon": "🏚️", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 250,
     "condition": lambda s: s["total"] >= 250},
    {"id": "three_hundred", "name": "Ты теперь тракторист ведомости", "desc": "300 двоек суммарно.",
     "icon": "🛡️", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 300,
     "condition": lambda s: s["total"] >= 300},
    {"id": "four_hundred", "name": "400 — Ангел Смерти", "desc": "400 двоек суммарно. Менгеле бы сказал: «идеально»",
     "icon": "🎬", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 400,
     "condition": lambda s: s["total"] >= 400},
    {"id": "five_hundred", "name": "Ким Чен Ын оценок", "desc": "500 двоек суммарно. Теперь ты финальный босс",
     "icon": "👑", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 500,
     "condition": lambda s: s["total"] >= 500},
    {"id": "six_hundred", "name": "600 — ты делаешь холокост студентов", "desc": "600 двоек суммарно. Дальше только тьма",
     "icon": "🕳️", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 600,
     "condition": lambda s: s["total"] >= 600},
    {"id": "six_six_six", "name": "Мейнстрим", "desc": "666 двоек — теперь только продавать душу за помилование",
     "icon": "😈", "category": "bestiary", "hidden": False, "tier": "legendary",
     "progress_key": "total", "progress_target": 666,
     "condition": lambda s: s["total"] >= 666},

    # ── Новые исторические цифры (10–1000, вместо лишних 700+) ──

    {"id": "seven_hundred_thirty_one", "name": "Отряд 731", "desc": "731 двойка суммарно. Японский эксперимент в ведомости завершён",
     "icon": "🧪", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 731,
     "condition": lambda s: s["total"] >= 731},
    {"id": "nine_hundred_eighty_four", "name": "984 — Солнцеликий уровень", "desc": "984 двойки суммарно. Аферов бы сказал: «молодец, сынок»",
     "icon": "☀️", "category": "bestiary", "hidden": False,
     "progress_key": "total", "progress_target": 984,
     "condition": lambda s: s["total"] >= 984},
    {"id": "stepan_syndrome", "name": "Синдром Степана", "desc": "1488 двоек суммарно",
     "icon": "🫠", "category": "bestiary", "hidden": False, "tier": "secret",
     "progress_key": "total", "progress_target": 1488,
     "condition": lambda s: s["total"] >= 1488},
    

    # ══ КОМБО (combo) ══
    {"id": "combo_2", "name": "Двойной выстрел в затылок", "desc": "2 двойки за 1 комбо. Сталинский стиль",
     "icon": "🩴", "category": "combo", "hidden": False,
     "progress_key": "max_combo", "progress_target": 2,
     "condition": lambda s: s["max_combo"] >= 2},
    {"id": "combo_3", "name": "Тройка МММ", "desc": "3 двойки за 1 комбо. Это не то, о чём ты подумал",
     "icon": "🫲", "category": "combo", "hidden": False,
     "progress_key": "max_combo", "progress_target": 3,
     "condition": lambda s: s["max_combo"] >= 3},
    {"id": "combo_5", "name": "Пятёрка в МММ", "desc": "5 двоек за 1 комбо. Главное — вовремя уйти из ?",
     "icon": "🖐️", "category": "combo", "hidden": False,
     "progress_key": "max_combo", "progress_target": 5,
     "condition": lambda s: s["max_combo"] >= 5},
    {"id": "combo_10", "name": "Расстрел по-сталински", "desc": "10 двоек за 1 комбо. Теперь это уже война",
     "icon": "🔟", "category": "combo", "hidden": False,
     "progress_key": "max_combo", "progress_target": 10,
     "condition": lambda s: s["max_combo"] >= 10},
    {"id": "combo_15", "name": "Хиросима ведомости", "desc": "15 двоек за 1 комбо. Конец света в одной ведомости",
     "icon": "☄️", "category": "combo", "hidden": False, "tier": "legendary",
     "progress_key": "max_combo", "progress_target": 15,
     "condition": lambda s: s["max_combo"] >= 15},

    # daily combo
    {"id": "daily_5", "name": "Пять лет лагерей за день", "desc": "5 двоек за сутки. Ты уже в ритме",
     "icon": "✋", "category": "combo", "hidden": False,
     "progress_key": "today", "progress_target": 5,
     "condition": lambda s: s["today"] >= 5},
    {"id": "daily_10", "name": "Мясник из 37-го", "desc": "10 двоек за сутки. Фартук в крови",
     "icon": "🪓", "category": "combo", "hidden": False,
     "progress_key": "today", "progress_target": 10,
     "condition": lambda s: s["today"] >= 10},
    {"id": "daily_20", "name": "Бойня в НКВД", "desc": "20 двоек за сутки. Сегодня мясо по акции",
     "icon": "🩸", "category": "combo", "hidden": False,
     "progress_key": "today", "progress_target": 20,
     "condition": lambda s: s["today"] >= 20},
    {"id": "daily_30", "name": "Кровавое воскресенье 2.0", "desc": "30 двоек за сутки. Выходные были слишком добрыми",
     "icon": "📅", "category": "combo", "hidden": False,
     "progress_key": "today", "progress_target": 30,
     "condition": lambda s: s["today"] >= 30},
    {"id": "daily_0", "name": "Синдром Марка", 
     "desc": "Ничего не сделать за день",
     "icon": "🥺", "category": "combo", "hidden": False, "tier": "secret",
     "progress_key": "today", "progress_target": 1,
     "condition": lambda s: (
         datetime.now().weekday() < 5 and   
         datetime.now().hour >= 18 and     
         s.get("today", 1) == 0             
     )},

    # ══ СТРИК (streak) ══
    {"id": "streak_2", "name": "Два дня Большого террора", "desc": "Стрик 2 дня. Ты уже не можешь остановиться",
     "icon": "✌️", "category": "streak", "hidden": False,
     "progress_key": "streak", "progress_target": 2,
     "condition": lambda s: s["streak"] >= 2},
    {"id": "streak_3", "name": "Трёхдневный террор", "desc": "Стрик 3 дня. Студенты чувствуют запах страха",
     "icon": "🔱", "category": "streak", "hidden": False,
     "progress_key": "streak", "progress_target": 3,
     "condition": lambda s: s["streak"] >= 3},
    {"id": "streak_5", "name": "Пятилетка в два дня", "desc": "Стрик 5 дней. Пятница стала красной",
     "icon": "📆", "category": "streak", "hidden": False,
     "progress_key": "streak", "progress_target": 5,
     "condition": lambda s: s["streak"] >= 5},
    {"id": "streak_7", "name": "Лазеры из глаз", "desc": "Стрик 7 дней. Ты теперь как Хоумлендер",
     "icon": "👁️‍🗨️", "category": "streak", "hidden": False,
     "progress_key": "streak", "progress_target": 7,
     "condition": lambda s: s["streak"] >= 7},
    {"id": "streak_10", "name": "Добби в ГУЛАГе", "desc": "Стрик 10 дней. Добби никогда не выберет",
     "icon": "🍄", "category": "streak", "hidden": False,
     "progress_key": "streak", "progress_target": 10,
     "condition": lambda s: s["streak"] >= 10},
    {"id": "streak_14", "name": "Две недели коллективизации", "desc": "Стрик 14 дней. Чума двоек распространяется",
     "icon": "⚡", "category": "streak", "hidden": False,
     "progress_key": "streak", "progress_target": 14,
     "condition": lambda s: s["streak"] >= 14},
    {"id": "streak_21", "name": "Три недели Большого скачка", "desc": "Стрик 21 день. Солнце больше не восходит",
     "icon": "🌘", "category": "streak", "hidden": False,
     "progress_key": "streak", "progress_target": 21,
     "condition": lambda s: s["streak"] >= 21},
    {"id": "streak_30", "name": "Ты бы мог стать Солнцеликим", "desc": "Стрик 30 дней",
     "icon": "☀️", "category": "streak", "hidden": False,
     "progress_key": "streak", "progress_target": 30,
     "condition": lambda s: s["streak"] >= 30},
    {"id": "streak_45", "name": "Полтора месяца культа личности", "desc": "Стрик 45 дней. Студенты уже пишут петицию в ООН",
     "icon": "🔥", "category": "streak", "hidden": False,
     "progress_key": "streak", "progress_target": 45,
     "condition": lambda s: s["streak"] >= 45},
    {"id": "streak_60", "name": "60 дней — и ты страшнее Мао", "desc": "Стрик 60 дней. Дедлайн перед сессией нервно курит",
     "icon": "💀", "category": "streak", "hidden": False,
     "progress_key": "streak", "progress_target": 60,
     "condition": lambda s: s["streak"] >= 60},
    {"id": "streak_365", "name": "Ярость Самсона", "desc": "Стрик 365 дней — «И нашёл он свежую ослиную челюсть…» Год без пощады",
     "icon": "⚔️", "category": "streak", "hidden": False, "tier": "legendary",
     "progress_key": "streak", "progress_target": 365,
     "condition": lambda s: s["streak"] >= 365},

    # ══ ПОМИЛОВАНИЕ (mercy) ══
    {"id": "soft_heart", "name": "Мягкое сердце", "desc": "Первое помилование. Студент вздохнул… на 15 секунд",
     "icon": "🕊️", "category": "mercy", "hidden": False,
     "progress_key": "mercy_count", "progress_target": 1,
     "condition": lambda s: s["mercy_count"] >= 1},
    {"id": "mercy_5", "name": "Рука дающего… и сразу забирающего", "desc": "5 помилований. Ты почти святой… почти",
     "icon": "🤲", "category": "mercy", "hidden": False,
     "progress_key": "mercy_count", "progress_target": 5,
     "condition": lambda s: s["mercy_count"] >= 5},
    {"id": "mercy_addict", "name": "Зависимость от милости", "desc": "10 помилований. Ты уже подсел на эту хрень",
     "icon": "💚", "category": "mercy", "hidden": False,
     "progress_key": "mercy_count", "progress_target": 10,
     "condition": lambda s: s["mercy_count"] >= 10},
    {"id": "mercy_15", "name": "Хрущёвская оттепель", "desc": "15 помилований. Сегодня милую, завтра опять заморозки",
     "icon": "😇", "category": "mercy", "hidden": False,
     "progress_key": "mercy_count", "progress_target": 15,
     "condition": lambda s: s["mercy_count"] >= 15},
    {"id": "mercy_50", "name": "Мать Тереза, которая потом всех расстреляла", "desc": "50 помилований. Канонизация отменяется",
     "icon": "🙏", "category": "mercy", "hidden": False,
     "progress_key": "mercy_count", "progress_target": 50,
     "condition": lambda s: s["mercy_count"] >= 50},
    {"id": "false_hope", "name": "Ложная надежда (вставил — вынул — и снова вставил)", "desc": "Помилование → двойка за 1 мин. Классика жанра",
     "icon": "😈", "category": "mercy", "hidden": False,
     "progress_key": None, "progress_target": 1,
     "condition": lambda s: s.get("mercy_then_two", False)},
    {"id": "no_mercy", "name": "Без пощады", "desc": "50 двоек, 0 помилований. Холодный ублюдок",
     "icon": "🖤", "category": "mercy", "hidden": False,
     "progress_key": "total", "progress_target": 50,
     "condition": lambda s: s["total"] >= 50 and s["mercy_count"] == 0},
    {"id": "bipolar", "name": "Биполярный диктатор", "desc": "5 помилов + 20 двоек/день. Сегодня оттепель, завтра — 37-й",
     "icon": "🎭", "category": "mercy", "hidden": False,
     "progress_key": "today", "progress_target": 20,
     "condition": lambda s: s.get("mercy_today", 0) >= 5 and s["today"] >= 20},

    # ══ СЕКРЕТНЫЕ (secret) ══
    {"id": "code_666", "name": "Число зверя", "desc": "Введи код 666. Люцифер одобряет",
     "icon": "😈", "category": "secret", "hidden": True,
     "condition": lambda s: s.get("_code_666", False)},
    {"id": "code_windows", "name": "Ностальгия", "desc": "Введи код windows. BSOD в душе",
     "icon": "🖥️", "category": "secret", "hidden": True,
     "condition": lambda s: s.get("_code_windows", False)},
    {"id": "code_key", "name": "Халява!", "desc": "Введи код key",
     "icon": "🔑", "category": "secret", "hidden": True,
     "condition": lambda s: s.get("_code_key", False)},
    {"id": "code_fail", "name": "Хакер-неудачник", "desc": "Ввести неправильный код. Даже 2 не поставил",
     "icon": "🤡", "category": "secret", "hidden": True,
     "condition": lambda s: s.get("_code_fail", False)},
    {"id": "like_67_but_22", "name": "Как 67 но 22", "desc": "Набери 22 двойки. Мем года",
     "icon": "✌️", "category": "secret", "hidden": True,
     "progress_key": "total", "progress_target": 22,
     "condition": lambda s: s["total"] >= 22},
    {"id": "error_404", "name": "Ошибка! Слишком мало двоек", "desc": "Набери 404 двойки. Студент не найден",
     "icon": "🚫", "category": "secret", "hidden": True,
     "progress_key": "total", "progress_target": 404,
     "condition": lambda s: s["total"] >= 404},
    {"id": "42_bro", "name": "42 братуха!", "desc": "42 двойки за неделю.",
     "icon": "🤙", "category": "secret", "hidden": True,
     "condition": lambda s: s.get("week_count", 0) >= 42},
    {"id": "chikatilo_52", "name": "Чикатило level", "desc": "Набери 52 двойки суммарно. Ростовский потрошитель нервно курит",
     "icon": "🔪", "category": "secret", "hidden": True,
     "progress_key": "total", "progress_target": 52,
     "condition": lambda s: s["total"] >= 52},
         {"id": "ominous_6eyes", "name": "Вездесущий", "desc": "Развей зловещую до 6 глаз",
     "icon": "👁️", "category": "themes", "hidden": False,
     "condition": lambda s: s.get("_ominous_eyes", 0) >= 6},
    {"id": "bottomless_star", "name": "Я не красный, культурно получилось", "desc": "Нажми на звезду в бездонной теме",
     "icon": "⭐", "category": "themes", "hidden": False,
     "condition": lambda s: s.get("_bottomless_star_clicked", False)},
    {"id": "sunset_3days", "name": "Солнцеликий", "desc": "Не меняй солнечную тему 3 дня",
     "icon": "☀️", "category": "themes", "hidden": False,
     "condition": lambda s: s.get("_sunset_days", 0) >= 3},
    {"id": "villain_5lasers", "name": "Бинго!", "desc": "Дождись 5 тиков лазера подряд в злодейской",
     "icon": "🎯", "category": "themes", "hidden": False,
     "condition": lambda s: s.get("_villain_laser_streak", 0) >= 5},

    # ══ МАГАЗИННЫЕ (shop) ══
    {"id": "gacha_1", "name": "Первый прокрут", "desc": "Прокрути рулетку 1 раз",
     "icon": "🎰", "category": "shop", "hidden": False,
     "condition": lambda s: s.get("_gacha_spins", 0) >= 1},
    {"id": "gacha_5", "name": "Азартный", "desc": "Прокрути рулетку 5 раз",
     "icon": "🎲", "category": "shop", "hidden": False,
     "progress_key": "_gacha_spins", "progress_target": 5,
     "condition": lambda s: s.get("_gacha_spins", 0) >= 5},
    {"id": "gacha_10", "name": "Лудоман", "desc": "Прокрути рулетку 10 раз",
     "icon": "💸", "category": "shop", "hidden": False,
     "progress_key": "_gacha_spins", "progress_target": 10,
     "condition": lambda s: s.get("_gacha_spins", 0) >= 10},
    {"id": "buy_first", "name": "Первая покупка", "desc": "Купи первую тему",
     "icon": "🛒", "category": "shop", "hidden": False,
     "condition": lambda s: s.get("_themes_bought", 0) >= 1},
    {"id": "buy_5", "name": "Шопоголик", "desc": "Купи 5 любых тем",
     "icon": "🛍️", "category": "shop", "hidden": False,
     "progress_key": "_themes_bought", "progress_target": 5,
     "condition": lambda s: s.get("_themes_bought", 0) >= 5},
    {"id": "buy_expensive", "name": "Транжира", "desc": "Купи тему дороже 1000 золота",
     "icon": "💰", "category": "shop", "hidden": False,
     "condition": lambda s: s.get("_bought_over_1000", False)},
    {"id": "buy_most_expensive", "name": "Олигарх", "desc": "Купи самую дорогую тему",
     "icon": "💎", "category": "shop", "hidden": False,
     "condition": lambda s: s.get("_bought_5000", False)},
]

CATEGORY_NAMES = {
    "bestiary": ("🦷 Бестиарий жертв", "Коллекция поверженных"),
    "combo":    ("💥 Комбо", "Массовые расправы"),
    "streak":   ("🔥 Стрик", "Непрерывное правление"),
    "mercy":    ("🕊️ Помилование", "Игры с милостью"),
    "secret":   ("🔐 Секретные", "Тайны, открытые единицам"),
    "themes":   ("🎨 Темки темщика", "Глубокое погружение"),
    "shop":     ("🛒 Магазинные", "Прокрутки и покупки"),
}

REACTIONS_SINGLE = [
    "🐸 Двоечка! Крякнула!",
    "🦆 Кря-кря, двойка в полёт!",
    "🧹 Подметено. Двойка на месте.",
    "🪣 Двойка упала в ведро судьбы!",
    "🐌 Медленно, но двоечно.",
    "🧲 Двойка притянута магнитом кармы!",
    "🎪 Цирк продолжается! Двойка!",
    "🪤 Мышеловка сработала — двойка!",
    "🦷 Вырвано с корнем! Двойка!",
    "🧻 Протокол зафиксирован!",
    "🪵 Как дрова в топку — двойка!",
    "🪠 Пробит! Двойка засчитана!",
    "🫕 В котёл! Двойка варится!",
    "🧊 Холодный расчёт — двойка!",
    "🦔 Колючий приговор!",
    "🔥 Двойка! Солнцеликий гордится тобой!",
    "💀 Ещё одна душа в коллекцию. Люцифер бы поставил тебе 5 за старание!",
    "🩸 Первая кровь сегодня? Студент уже в шоке!",
    "👑 Двойка принята в партию диктатора!",
    "☀️ Солнцеликий смотрит и улыбается!",
    "🪓 Топор занесён — и ты не промахнулся!",
    "🧪 Отряд 731 одобряет этот эксперимент!",
    "😈 Люцифер зачёток ставит галочку!",
    "📸 Эпштейном с Трампом: «Красавчик!»",
    "🌑 Дарту Вейдеру и не снилось столько силы!",
    "🛡️ Тракторист ведомости в деле!",
    "🔪 Чикатило level: +1 жертва!",
    "🧪 Эксперимент удался. Двойка зафиксирована!",
    "👁️ Большой Брат всё видит!",
    "🍑 69-й уровень двоек приближается...",
]
REACTIONS_COMBO = [
    "🦆🦆 ДВОЙНОЙ КРЯК!",
    "🧦🧦 ДВА НОСКА В ЛИЦО!",
    "🪓🪓 ДВОЙНОЙ РУБЕЖ!",
    "🐸🐸 ЖАБЫ НАПАДАЮТ!",
    "🫁🫁 ДВОЙНОЙ ВДОХ БОЛИ!",
    "🧲🧲 МАГНИТНАЯ БУРЯ ДВОЕК!",
    "🦴🦴 ДВА УДАРА ПО ЗАЧЁТКЕ!",
    "🪣🪣 ДВА ВЕДРА ПРАВОСУДИЯ!",
    "🔥🔥 ДВОЙНОЙ ОГОНЬ! Ты просто машина!",
    "💀💀 ДВА ЧЕРЕПА ЗА РАЗ — ты не шутишь!",
    "🪓🪓 ДВОЙНОЙ РАССТРЕЛ! Ты в своём репертуаре!",
    "👑👑 ДВА НОВЫХ СОЛДАТА В ТВОЮ АРМИЮ!",
    "🧪🧪 ДВОЙНОЙ ЭКСПЕРИМЕНТ УДАЛСЯ!",
    "🌑🌑 ДВА УДАРА С ТЁМНОЙ СТОРОНЫ — мощно!",
    "😈😈 ДВА ПОДПИСАНИЯ ОТ ЛЮЦИФЕРА ЗАЧЁТОК!",
    "☀️☀️ Ты светишь так ярко, что студенты слепнут!",
    "😈😈 ПОЧТИ КАК 67!",
]
REACTIONS_MASS = [
    "🦆🐸🧹 ТРОЙНАЯ КАРА!",
    "🪤🪤🪤 ТРОЙНАЯ ЛОВУШКА!",
    "🧊🔥💀 СТИХИЯ ДВОЕК!",
    "🫕🫕🫕 КОТЁЛ ПЕРЕПОЛНЕН!",
    "🦷🦷🦷 ЗУБОДРОБИТЕЛЬНОЕ КОМБО!",
    "🪵🪵🪵 ВСЁ В ТОПКУ!",
    "🪠🪠🪠 ТРОЙНОЙ ПРОБОЙ!",
    "🔥🔥🔥 ТРОЙНАЯ КАРА! СТАЛИН АПЛОДИРУЕТ!",
    "💀💀💀 ТРИ ЧЕРЕПА — ЧИКАТИЛО ОТДЫХАЕТ!",
    "🧪🧪🧪 ЯПОНИЯ В ШОКЕ ОТ МАССОВОГО ЭКСПЕРИМЕНТА!",
    "🪓🪓🪓 ТРОЙНОЙ ТОПОР — ты не знаешь слова «пощада»!",
    "👑👑👑 ТРИ СОЛДАТА В АРМИЮ ДИКТАТОРА!",
    "☀️☀️☀️ Солнцеликий: «Это мой лучший ученик!»",
    "🌑🌑🌑 ТРОЙНОЙ УДАР ТЁМНОЙ СТОРОНЫ!",
    "😈😈😈 ЛЮЦИФЕР ЗАЧЁТОК УСТРАИВАЕТ АПЛОДИСМЕНТЫ!",
    "🪓🪓🪓 ТРОЙНОЙ РАССТРЕЛ В ВЕДОМОСТИ!",
    "🔥🔥🔥 ТРОЙНАЯ КАРА! Ты сегодня бог!",
]
MOTIVATIONAL_QUOTES = [
    "Каждая двойка — шаг к власти!",
    "Ты в ударе, диктатор!",
    "Двойки — твои солдаты.",
    "Стрик не остановить!",
    "Ведомость горит!",
    "Рекорды ждут!",
    "Трон крепнет!",
    "Сегодня ведомость, завтра — мир.",
    "Двойка не спрашивает разрешения.",
    "Кто ставит двойки — тот правит миром.",
    "Стрик растёт, студенты плачут.",
    "Каждый комбо — маленькая победа.",
    "Ведомость помнит всё.",
    "Ни дня без двойки — закон диктатора.",
    "67... всего лишь 67... почему 67? Зачем 67? Куда ведёт 67?",
    "Если в жизни всё плохо — поставь двойку. Кому-то ещё хуже.",
    "--   ---   .--.   .-   ---   ...-   ---   .   .--.   ..-   --..   ---",
    "СТАВЬ! СТАВЬ! СТАВЬ! ДВА! Ты - машина",
    "Солнцеликий смотрит на тебя. Ставь дальше!",
    "Ты не просто ставишь 2. Ты пишешь историю ведомости!",
    "Сталин бы сказал: «Вот это я понимаю — настоящий диктатор!»",
    "Двойка тупогуб, тупогубенькая двойка, у двойки была губа тупа",
    "Двойки — это твои солдаты.",
    "Ты - машина",
    "Каждое комбо делает тебя сильнее. Продолжай!",
    "Студенты плачут, а ты — улыбаешься. Так и надо!",
    "Стрик растёт? Солнцеликий уже готовит тебе пятёрку!",
    "Ведомость горит — и ты греешь руки у этого огня!",
    "Ты не преподаватель. Ты — верховный каратель оценок!",
    "Каждое комбо приближает тебя к званию лучшего",
    "Студенты плачут, ты - лучший. Продолжай!",
    "Трон крепнет, а Солнцеликий уже ставит тебе зачёт!",
    "Двойка не спрашивает разрешения… как и ты.",
    "Сегодня двойки, завтра — весь мир знает, кто тут главный.",
    "Если в жизни всё плохо — поставь двойку.",
    "Число зверя уже близко… готовь шампанское, диктатор!",
    "С каждой двойкой ты становишься всё ближе к абсолюту!",
    "Ты в ритме. Ты в огне. Ты — это сила!",
    "Только двойки",
    "🔑 «Ключ» к успеху — в правильном слове...",
    "💻 Какая операционка лучше? Окна решают!",
    "🔥 Три шестёрки — не просто число...",
    "🕳 Пустота зовёт тех, кто не боится void...",
    "🥐 Круассаны — валюта мудрых.",
    "📅 1874 — год великих открытий.",
]

DEFAULT_CONFIG = {
    "hotkey": "ctrl+shift+f2",
    "color_tolerance": 35,
    "detection_interval_ms": 1500,
    "zone": None,
    "target_color_hsv": None,
    "sound_enabled": True,
    "overlay_enabled": True,
    "mercy_duration_sec": 15,
    "bg_opacity": 85,        # % прозрачность фона панели
    "widget_opacity": 95,    # % прозрачность виджетов
    "pixel_threshold": 0.3,  # % порог срабатывания
}

def load_config():
    if CONFIG_JSON.exists():
        try:
            with open(CONFIG_JSON, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception: pass
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    with open(CONFIG_JSON, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
