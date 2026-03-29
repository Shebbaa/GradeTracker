"""
Inferno Grade Tracker — Themes (v3: Категории тем)
Темы сгруппированы по категориям.
Каждая тема может содержать: colors, font, animated, special_effect, bg_image.
"""

# ═══════════════════════════════════════════════════════════
#  Категории тем (порядок важен — так они отображаются в UI)
# ═══════════════════════════════════════════════════════════
THEME_CATEGORIES = [
    {
        "id": "canonical",
        "name": "Каноничные ⛪",
        "desc": "Темы, вдохновлённые кругами Ада и библейскими мотивами.",
    },
    {
        "id": "classic",
        "name": "Классические 🏛",
        "desc": "Строгие, проверенные временем цветовые схемы.",
    },
    {
        "id": "elemental",
        "name": "Стихийные 🌪",
        "desc": "Силы природы: лёд, яд, молния, пустота.",
    },
    {
        "id": "neon",
        "name": "Неоновые 💡",
        "desc": "Яркие, кислотные, сияющие схемы.",
    },
    {
        "id": "satirical",
        "name": "Сатирические 🤡",
        "desc": "Абсурд, хаос и чёрный юмор.",
    },
]

THEME_CATEGORY_ORDER = [c["id"] for c in THEME_CATEGORIES]


def get_category_info(cat_id: str) -> dict | None:
    for c in THEME_CATEGORIES:
        if c["id"] == cat_id:
            return c
    return None


# ═══════════════════════════════════════════════════════════
#  Все темы
# ═══════════════════════════════════════════════════════════
THEMES = [
    # ─── КАНОНИЧНЫЕ ───────────────────────────────────────
    # Постепенное погружение: от серости к огню
    {
        "id": "ultra_default",
        "category": "canonical",
        "name": "Ультра дефолтно дефолтная 😐",
        "desc": "Серая, однотонная, невзрачная. Начало пути.",
        "unlock": None,
        "theme_icon_text": ("0", "#999999"),
        "fire_scale": 0.3,
        "no_glow": True,
        "no_border": True,
        "flat_bg": True,
        "counter_font": "Arial",
        "colors": {
            "primary": "#999999",
            "secondary": "#777777",
            "accent": "#aaaaaa",
            "glow": "#666666",
            "bg_top": (30, 30, 30),
            "bg_mid": (30, 30, 30),
            "bg_bot": (30, 30, 30),
            "border": "#555555",
            "fire_core": (150, 120, 100),
            "fire_mid": (130, 130, 130),
            "fire_tip": (100, 100, 100),
            "ember_colors": [(140, 140, 140), (120, 120, 120), (100, 100, 100)],
        },
    },
    {
        "id": "not_ultra_default",
        "category": "canonical",
        "name": "Уже не ультра дефолтно дефолтная 😐",
        "desc": "Появился градиент бара и рамка. Ещё серая, но уже с характером.",
        "unlock": "total:10",
        "theme_icon_text": ("10", "#aa6655"),
        "fire_scale": 0.4,
        "no_glow": True,
        "counter_font": "Arial",
        "colors": {
            "primary": "#aaaaaa",
            "secondary": "#888888",
            "accent": "#bbbbbb",
            "glow": "#777777",
            "bg_top": (35, 32, 30),
            "bg_mid": (25, 23, 22),
            "bg_bot": (38, 35, 32),
            "border": "#666666",
            "fire_core": (170, 130, 100),
            "fire_mid": (150, 140, 130),
            "fire_tip": (120, 115, 110),
            "ember_colors": [(160, 140, 120), (140, 130, 120), (120, 110, 100)],
        },
    },
    {
        "id": "stylized",
        "category": "canonical",
        "name": "Стилизованная 🎭",
        "desc": "Урезанный Адский огонь. Без свечений, без понтов.",
        "desc_full": "Урезанный Адский огонь. Без свечений, без понтов.<br><br>• Особая цветовая гамма",
        "unlock": "total:20",
        "theme_icon_text": ("20", "#cd7f32"),
        "fire_scale": 0.7,
        "no_glow": True,
        "counter_font": "Arial",
        "colors": {
            "primary": "#cc4420",
            "secondary": "#aa3300",
            "accent": "#dd8844",
            "glow": "#aa3300",
            "bg_top": (18, 3, 3),
            "bg_mid": (8, 0, 0),
            "bg_bot": (22, 5, 2),
            "border": "#882200",
            "fire_core": (200, 50, 0),
            "fire_mid": (200, 100, 0),
            "fire_tip": (180, 140, 30),
            "ember_colors": [(200, 60, 0), (200, 120, 0), (200, 30, 30)],
        },
    },
    {
        "id": "blatnaya",
        "category": "canonical",
        "name": "Блатная 💎",
        "desc": "Золотые пылинки на тёмном фоне. Бар — жёлтый, амбиции — золотые.",
        "desc_full": "Золотые пылинки на тёмном фоне. Бар — жёлтый, амбиции — золотые.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "total:30",
        "theme_icon_text": ("30", "#ff6600"),
        "fire_scale": 0.75,
        "no_glow": True,
        "bg_particles": "gold_dust",
        "counter_font": "Arial",
        "bar_colors": {
            "chunk_start": (80, 60, 0),
            "chunk_mid": (200, 160, 0),
            "chunk_end": (255, 200, 0),
        },
        "colors": {
            "primary": "#cc4420",
            "secondary": "#aa3300",
            "accent": "#dd8844",
            "glow": "#aa3300",
            "bg_top": (18, 3, 3),
            "bg_mid": (8, 0, 0),
            "bg_bot": (22, 5, 2),
            "border": "#882200",
            "fire_core": (200, 50, 0),
            "fire_mid": (200, 100, 0),
            "fire_tip": (180, 140, 30),
            "ember_colors": [(200, 60, 0), (200, 120, 0), (200, 30, 30)],
        },
    },
    {
        "id": "almost_star",
        "category": "canonical",
        "name": "Почти звезда ⭐",
        "desc": "Оранжевый рассвет, звёзды и золотые пылинки. Ещё чуть-чуть...",
        "desc_full": "Оранжевый рассвет, звёзды и золотые пылинки. Ещё чуть-чуть...<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "total:50",
        "theme_icon_text": ("50", "#dd2222"),
        "fire_scale": 0.85,
        "no_glow": True,
        "bg_particles": "gold_dust",
        "bg_stars": True,
        "counter_font": "Arial",
        "colors": {
            "primary": "#cc4420",
            "secondary": "#aa3300",
            "accent": "#dd8844",
            "glow": "#aa3300",
            "bg_top": (40, 18, 4),
            "bg_mid": (8, 0, 0),
            "bg_bot": (22, 5, 2),
            "border": "#882200",
            "fire_core": (200, 50, 0),
            "fire_mid": (200, 100, 0),
            "fire_tip": (180, 140, 30),
            "ember_colors": [(200, 60, 0), (200, 120, 0), (200, 30, 30)],
        },
    },
    {
        "id": "cant_not_photo",
        "category": "canonical",
        "name": "Неее... ну это не сфоткать грех! 📸",
        "desc": "Голубые 67 на фоне, голубые пылинки. Полный огонь.",
        "desc_full": "Голубые 67 на фоне, голубые пылинки. Полный огонь.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "total:67",
        "theme_icon_text": ("67", "#3399ee"),
        "fire_scale": 1.0,
        "no_glow": True,
        "bg_particles": "blue_dust",
        "bg_images": ["ku.png", "kuu.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#3399ee",
            "secondary": "#2266bb",
            "accent": "#66bbff",
            "glow": "#2288dd",
            "bg_top": (4, 8, 22),
            "bg_mid": (0, 2, 10),
            "bg_bot": (2, 6, 20),
            "border": "#2266aa",
            "fire_core": (255, 60, 0),
            "fire_mid": (255, 130, 0),
            "fire_tip": (255, 180, 30),
            "ember_colors": [(255, 80, 0), (255, 160, 0), (255, 30, 30)],
        },
    },
    {
        "id": "local_herzog",
        "category": "canonical",
        "name": "Местный Ицхак Герцог ✡️",
        "desc": "Звезда Давида в центре, синее свечение по краям. 115% огня.",
        "desc_full": "Звезда Давида в центре, синее свечение по краям. 115% огня.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "total:150",
        "theme_icon_text": ("150", "#2266ff"),
        "fire_scale": 1.15,
        "no_glow": True,
        "bg_particles": "blue_dust",
        "bg_images": ["ku.png", "kuu.png"],
        "bg_center_image": "lol.png",
        "edge_glow": (30, 100, 255),
        "counter_font": "Arial",
        "colors": {
            "primary": "#2266ff",
            "secondary": "#1144cc",
            "accent": "#5599ff",
            "glow": "#1155ee",
            "bg_top": (2, 4, 18),
            "bg_mid": (0, 1, 8),
            "bg_bot": (1, 3, 16),
            "border": "#1144bb",
            "fire_core": (255, 60, 0),
            "fire_mid": (255, 130, 0),
            "fire_tip": (255, 180, 30),
            "ember_colors": [(255, 80, 0), (255, 160, 0), (255, 30, 30)],
        },
    },

    # ─── СТИХИЙНЫЕ ────────────────────────────────────────
    {
        "id": "villain",
        "icon": "evilcone.png",
        "category": "elemental",
        "name": "Злодейская 🗡",
        "desc": "Тёмно-зелёное полотно с багрянцем. Углы срезаны, колбы по бокам.",
        "desc_full": "Тёмно-зелёное полотно с багрянцем. Углы срезаны, колбы по бокам.<br><br>• Особая цветовая гамма<br>• Эффекты при обнаружении<br>• Особый шрифт<br><br>✦ <b>ПЕРСОНАЛЬНАЯ ОСОБЕННОСТЬ</b><br>Брутальная форма окна, боковые шкалы прогресса ранга.",
        "unlock": "hidden",
        "no_glow": True,
        "no_grid": True,        # без сетки
        "shape": "octagon",     # срезанные углы + боковые колбы
        "extra_width": 52,      # +52px для боковых колб (26 на сторону)
        "counter_font": "Georgia",
        "counter_font_scale": 1.2,  # крупнее цифра
        "colors": {
            "primary": "#b81c28",           # багряный — основной цвет текста/цифр
            "secondary": "#3b4a3b",         # тёмно-зелёный
            "accent": "#8a9a80",            # оливковый
            "glow": "#b81c28",
            "bg_top": (45, 55, 42),         # тёмно-зелёный фон (не чёрный!)
            "bg_mid": (35, 45, 35),
            "bg_bot": (55, 35, 40),         # переход в бордовый снизу
            "border": "#3b4a3b",
            "bar_bg": (30, 38, 30),         # фон бара
            "bar_fill": (180, 28, 40),      # заливка бара — багряный
            "fire_core": (180, 25, 35),     # багряный огонь
            "fire_mid": (120, 30, 30),
            "fire_tip": (65, 20, 30),       # тёмный марон
            "ember_colors": [(180,25,35), (120,135,110), (65,20,30), (55,70,55)],
        },
    },
    {
        "id": "sunset",
        "icon": "sunsecone.png",
        "category": "elemental",
        "name": "Закат 🌅",
        "desc": "Тёплые волны заката. Числа излучают солнечный свет.",
        "desc_full": "Тёплые волны заката. Числа излучают солнечный свет.<br><br>• Особая цветовая гамма<br>• Фоновые частицы<br>• Фоновая анимация<br>• Эффекты при обнаружении<br>• Особый шрифт",
        "unlock": "hidden",
        "fire_scale": 0.7,
        "no_grid": True,
        "bg_particles": "sun_rays",       # специальный тип — лучи из числа
        "edge_glow_pulse": True,           # пульсирующая рамка жёлтый↔оранжевый
        "counter_font": "Segoe Script",    # рукописный
        "counter_font_scale": 1.0,
        "counter_glow_boost": 6,           # множитель свечения — яркое солнце
        "wavy_bg": True,                   # волнистый асимметричный градиент
        "bar_colors": {
            "chunk_start": (178, 46, 55),
            "chunk_mid": (246, 131, 24),
            "chunk_end": (253, 192, 5),
        },
        "colors": {
            "primary": "#F68318",           # оранжевый — текст счётчика
            "secondary": "#B22E37",
            "accent": "#FDC005",            # жёлтый акцент
            "glow": "#FDD835",              # ярко-жёлтое свечение
            "bg_top": (49, 53, 117),       # #313575
            "bg_mid": (50, 25, 81),        # #321951
            "bg_bot": (99, 48, 144),       # #633090
            "border": "#633090",
            "fire_core": (253, 192, 5),
            "fire_mid": (246, 131, 24),
            "fire_tip": (178, 46, 55),
            "ember_colors": [(253,192,5), (246,131,24), (178,46,55), (99,48,144)],
        },
    },

    {
        "id": "retro",
        "icon": "retrocone.png",
        "category": "elemental",
        "name": "Ретро 🖥",
        "desc": "Зелёный терминал, полосы сканлайнов и двоичный дождь. :D",
        "desc_full": "Зелёный терминал, полосы сканлайнов и двоичный дождь. :D<br><br>• Особая цветовая гамма<br>• Фоновые частицы<br>• Фоновая анимация<br>• Эффекты при обнаружении<br>• Особый шрифт<br>• Динамичный счётчик",
        "unlock": "hidden",
        "no_glow": True,
        "no_grid": True,
        "sharp_corners": True,           # прямые углы окна
        "bg_particles": "binary_rain",   # 0 и 1 вместо пылинок
        "bg_scanlines": True,            # горизонтальные полосы
        "counter_smiley": True,          # :D / >:D на счётчике
        "counter_font": "Consolas",        # моноширинный, масштабируемый
        "counter_font_scale": 1.3,
        "bar_colors": {
            "chunk_start": (0, 60, 0),
            "chunk_mid": (0, 180, 0),
            "chunk_end": (0, 255, 0),
        },
        "colors": {
            "primary": "#00ff00",           # ярко-зелёный текст
            "secondary": "#00aa00",
            "accent": "#00dd00",
            "glow": "#00ff00",
            "bg_top": (6, 16, 6),           # тёмно-зелёный (+25%)
            "bg_mid": (4, 10, 4),
            "bg_bot": (6, 18, 6),
            "border": "#00aa00",
            "fire_core": (0, 200, 30),
            "fire_mid": (50, 255, 50),
            "fire_tip": (150, 255, 80),
            "ember_colors": [(0, 220, 40), (0, 180, 0), (80, 255, 0), (0, 140, 0)],
        },
    },

    {
        "id": "ominous",
        "icon": "horrocone.png",
        "category": "elemental",
        "name": "Зловещая 👁",
        "desc": "Чёрный дым, вращающиеся глаза. С каждой детекцией — хуже.",
        "desc_full": "Чёрный дым, вращающиеся глаза. С каждой детекцией — хуже.<br><br>• Особая цветовая гамма<br>• Фоновые частицы<br>• Фоновая анимация<br>• Эффекты при обнаружении<br>• Особый шрифт<br>• Фоновый рисунок<br>• Динамичный счётчик<br><br>✦ <b>ПЕРСОНАЛЬНАЯ ОСОБЕННОСТЬ</b><br>У счётчика есть глаза, их становится больше с каждой двойкой.",
        "unlock": "hidden",
        "no_glow": True,
        "no_grid": True,
        "bg_particles": "black_smoke",
        "bg_image_file": "sc.jpg",       # фоновая картинка
        "counter_font": "Impact",         # угловатый шрифт
        "counter_font_scale": 0.75,
        "counter_outline": True,          # белый текст + чёрный контур
        "counter_wobble": True,           # покачивание числа
        "orbiting_eyes": True,            # вращающиеся глаза
        "progressive_detections": True,   # доп. глаза с каждой детекцией
        "bar_colors": {
            "chunk_start": (20, 20, 20),
            "chunk_mid": (60, 60, 60),
            "chunk_end": (100, 100, 100),
        },
        "colors": {
            "primary": "#ffffff",          # белый счётчик
            "secondary": "#555555",
            "accent": "#999999",
            "glow": "#444444",
            "bg_top": (15, 15, 18),
            "bg_mid": (8, 8, 10),
            "bg_bot": (5, 5, 8),
            "border": "#333333",
            "fire_core": (30, 30, 35),     # чёрный дым вместо огня
            "fire_mid": (20, 20, 25),
            "fire_tip": (10, 10, 15),
            "ember_colors": [(25,25,30), (35,35,40), (15,15,20), (40,40,45)],
        },
    },

    {
        "id": "charged",
        "icon": "elecone.png",
        "category": "elemental",
        "name": "Заряженная ⚡",
        "desc": "Молнии, вспышки грозы, электрические зигзаги. Спящий шторм.",
        "desc_full": "Молнии, вспышки грозы, электрические зигзаги. Спящий шторм.<br><br>• Особая цветовая гамма<br>• Фоновая анимация<br>• Эффекты при обнаружении<br>• Особый шрифт<br>• Динамичный счётчик<br><br>✦ <b>ПЕРСОНАЛЬНАЯ ОСОБЕННОСТЬ</b><br>Почти статична, но стоит только включить детектор — сразу начнётся шторм. Включает в себя эффекты мыши.",
        "unlock": "hidden",
        "no_glow": True,
        "no_grid": True,
        # Молнии рисуются по краям окна стандартной ширины (480px)
        "counter_font": "Consolas",
        "counter_font_scale": 1.0,
        "counter_jitter": True,          # дёрганый счётчик
        "edge_lightning": True,          # постоянные зигзаги-рамки по краям
        "edge_glow": (30, 100, 255),     # синее свечение по краям как у Герцога
        "dormant_until_detection": True, # бледная до запуска детекции
        "detection_shake": True,         # тряска окна при детекции
        "bar_colors": {
            "chunk_start": (200, 220, 255),
            "chunk_mid": (150, 180, 240),
            "chunk_end": (100, 140, 220),
        },
        "colors": {
            "primary": "#ffffff",
            "secondary": "#eeeeff",
            "accent": "#ffffcc",
            "glow": "#aaccff",
            "bg_top": (4, 6, 22),
            "bg_mid": (2, 3, 14),
            "bg_bot": (1, 2, 10),
            "border": "#1144bb",
            "fire_core": (100, 150, 255),
            "fire_mid": (60, 100, 200),
            "fire_tip": (30, 60, 150),
            "ember_colors": [(180,200,255), (120,160,240), (200,220,255), (255,255,200)],
        },
    },

    {
        "id": "bottomless",
        "icon": "abicone.png",
        "category": "elemental",
        "name": "Бездонная 🌀",
        "desc": "Чёрно-красная спираль, затягивающая тьму. Курсор — триггер бездны.",
        "desc_full": "Чёрно-красная спираль, затягивающая тьму. Курсор — триггер бездны.<br><br>• Особая цветовая гамма<br>• Фоновая анимация<br>• Эффекты при обнаружении<br>• Особый шрифт<br><br>✦ <b>ПЕРСОНАЛЬНАЯ ОСОБЕННОСТЬ</b><br>Спираль вместо фона с динамичной скоростью. Прокликивание ядра вызовет коллапс. Схлопывание звезды приводит к смене цвета воронки.",
        "unlock": "hidden",
        "no_glow": True,
        "no_grid": True,
        "spiral_theme": True,          # крутящаяся спираль
        "counter_font": "Cinzel",
        "counter_font_scale": 0.9,
        "counter_color": "#ffffff",    # белый счётчик
        "counter_glow_boost": 3,      # сильное свечение счётчика
        "bar_colors": {
            "chunk_start": (40, 0, 0),
            "chunk_mid": (140, 10, 10),
            "chunk_end": (200, 20, 20),
        },
        "shape": "circle",            # идеальный круг
        "extra_width": 192,           # +40% от 480 для круга
        "colors": {
            "primary": "#ff4444",
            "secondary": "#aa1111",
            "accent": "#ff6666",
            "glow": "#ff2222",
            "bg_top": (0, 0, 0),
            "bg_mid": (0, 0, 0),
            "bg_bot": (0, 0, 0),
            "border": "#661111",
            "fire_core": (200, 15, 15),
            "fire_mid": (140, 0, 0),
            "fire_tip": (70, 0, 0),
            "ember_colors": [(160,10,10), (100,0,0), (50,0,0), (20,0,0)],
        },
    },

    {
        "id": "fractal",
        "icon": "fracone.png",
        "category": "elemental",
        "name": "Фрактальная 🔷",
        "desc": "Гексагональная сетка, приближающаяся из бесконечности и вращающаяся.",
        "desc_full": "Гексагональная сетка, приближающаяся из бесконечности и вращающаяся.<br><br>• Особая цветовая гамма<br>• Фоновые частицы<br>• Фоновая анимация<br>• Эффекты при обнаружении<br>• Особый шрифт<br><br>✦ <b>ПЕРСОНАЛЬНАЯ ОСОБЕННОСТЬ</b><br>Бесконечная генерация сетки фона.",
        "unlock": "hidden",
        "no_grid": True,            # стандартная сетка отключена — своя гексагональная
        "hex_grid": True,           # гексагональная анимированная сетка
        "bg_particles": "hex_dust", # шестиугольные/пятиугольные пылинки
        "fire_scale": 0.75,
        "counter_font": "Consolas",
        "counter_glow_color": "#ff0055",
        "bar_colors": {
            "chunk_start": (80, 0, 22),
            "chunk_mid": (200, 0, 55),
            "chunk_end": (255, 0, 85),
        },
        "colors": {
            "primary": "#aaff00",
            "secondary": "#88dd00",
            "accent": "#ccff33",
            "glow": "#aaff00",
            "bg_top": (18, 2, 8),
            "bg_mid": (8, 0, 3),
            "bg_bot": (22, 3, 10),
            "border": "#55aa00",
            "fire_core": (255, 0, 85),
            "fire_mid": (200, 0, 55),
            "fire_tip": (180, 40, 80),
            "ember_colors": [(255, 0, 85), (200, 0, 55), (180, 30, 70)],
        },
    },

    # ─── КЛАССИЧЕСКИЕ (16 цветовых вариаций) ────────────
   {
        "id": "classic_ice",
        "category": "classic",
        "name": "Ледяная тишина 🧊",
        "desc": "Тёмная бирюза, холод и спокойствие.",
        "desc_full": "Тёмная бирюза, холод и спокойствие.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "blue_dust",
        "bg_images": ["medal_11_1.png", "medal_11_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#00ccaa", "secondary": "#009988", "accent": "#33ddbb",
            "glow": "#00bbaa",
            "bg_top": (6, 18, 22), "bg_mid": (3, 10, 14), "bg_bot": (8, 20, 24),
            "border": "#006655",
            "fire_core": (0, 200, 160), "fire_mid": (0, 140, 120), "fire_tip": (0, 100, 80),
            "ember_colors": [(0, 200, 160), (0, 150, 120), (0, 100, 80)],
        },
    },
    {
        "id": "classic_sakura",
        "category": "classic",
        "name": "Сакура 🌸",
        "desc": "Нежно-розовые лепестки в темноте.",
        "desc_full": "Нежно-розовые лепестки в темноте.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "gold_dust",
        "bg_images": ["medal_10_1.png", "medal_10_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#ff88aa", "secondary": "#cc6688", "accent": "#ffaacc",
            "glow": "#ff77aa",
            "bg_top": (24, 10, 16), "bg_mid": (14, 5, 10), "bg_bot": (26, 12, 18),
            "border": "#884466",
            "fire_core": (255, 120, 170), "fire_mid": (200, 80, 130), "fire_tip": (160, 60, 100),
            "ember_colors": [(255, 120, 170), (200, 80, 130), (160, 60, 100)],
        },
    },
    {
        "id": "classic_lemon",
        "category": "classic",
        "name": "Кислотный лимон ⚡",
        "desc": "Ослепительно жёлтый, как удар молнии.",
        "desc_full": "Ослепительно жёлтый, как удар молнии.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "gold_dust",
        "bg_images": ["medal_09_1.png", "medal_09_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#dddd00", "secondary": "#aaaa00", "accent": "#ffff44",
            "glow": "#cccc00",
            "bg_top": (20, 18, 4), "bg_mid": (10, 9, 2), "bg_bot": (24, 22, 5),
            "border": "#777700",
            "fire_core": (230, 230, 0), "fire_mid": (180, 180, 0), "fire_tip": (140, 140, 0),
            "ember_colors": [(230, 230, 0), (200, 200, 0), (160, 160, 0)],
        },
    },
    {
        "id": "classic_royal",
        "category": "classic",
        "name": "Королевский пурпур 👑",
        "desc": "Глубокий фиолет, достойный трона.",
        "desc_full": "Глубокий фиолет, достойный трона.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "blue_dust",
        "bg_images": ["medal_08_1.png", "medal_08_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#aa44ff", "secondary": "#7722cc", "accent": "#cc77ff",
            "glow": "#9933ee",
            "bg_top": (16, 6, 26), "bg_mid": (8, 2, 14), "bg_bot": (18, 8, 28),
            "border": "#5522aa",
            "fire_core": (170, 60, 255), "fire_mid": (120, 30, 200), "fire_tip": (80, 20, 140),
            "ember_colors": [(170, 60, 255), (120, 30, 200), (80, 20, 140)],
        },
    },
    {
        "id": "classic_ember",
        "category": "classic",
        "name": "Тлеющий уголь 🔶",
        "desc": "Тёплый оранжевый, как догорающий костёр.",
        "desc_full": "Тёплый оранжевый, как догорающий костёр.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "gold_dust",
        "bg_images": ["medal_07_1.png", "medal_07_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#ee7722", "secondary": "#bb5500", "accent": "#ff9944",
            "glow": "#dd6600",
            "bg_top": (24, 12, 4), "bg_mid": (14, 6, 2), "bg_bot": (26, 14, 5),
            "border": "#884400",
            "fire_core": (240, 120, 30), "fire_mid": (200, 80, 0), "fire_tip": (160, 60, 0),
            "ember_colors": [(240, 120, 30), (200, 80, 0), (160, 60, 0)],
        },
    },
    {
        "id": "classic_mint",
        "category": "classic",
        "name": "Мятная свежесть 🍃",
        "desc": "Прохладный мятный на тёмном фоне.",
        "desc_full": "Прохладный мятный на тёмном фоне.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "blue_dust",
        "bg_images": ["medal_06_1.png", "medal_06_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#44ddaa", "secondary": "#22aa77", "accent": "#77ffcc",
            "glow": "#33cc99",
            "bg_top": (4, 20, 14), "bg_mid": (2, 10, 7), "bg_bot": (6, 22, 16),
            "border": "#228866",
            "fire_core": (60, 220, 160), "fire_mid": (30, 170, 120), "fire_tip": (20, 120, 80),
            "ember_colors": [(60, 220, 160), (30, 170, 120), (20, 120, 80)],
        },
    },
    {
        "id": "classic_blood",
        "category": "classic",
        "name": "Кровавый закат 🩸",
        "desc": "Глубокий тёмно-красный, как последний луч.",
        "desc_full": "Глубокий тёмно-красный, как последний луч.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "gold_dust",
        "bg_images": ["medal_05_1.png", "medal_05_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#cc2222", "secondary": "#991111", "accent": "#ee4444",
            "glow": "#bb1111",
            "bg_top": (22, 4, 4), "bg_mid": (12, 2, 2), "bg_bot": (24, 6, 6),
            "border": "#771111",
            "fire_core": (200, 30, 30), "fire_mid": (150, 20, 20), "fire_tip": (100, 10, 10),
            "ember_colors": [(200, 30, 30), (150, 20, 20), (100, 10, 10)],
        },
    },
    {
        "id": "classic_ocean",
        "category": "classic",
        "name": "Океанская бездна 🌊",
        "desc": "Глубокий синий, как дно океана.",
        "desc_full": "Глубокий синий, как дно океана.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "blue_dust",
        "bg_images": ["medal_04_1.png", "medal_04_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#2266ee", "secondary": "#1144aa", "accent": "#4488ff",
            "glow": "#2255dd",
            "bg_top": (4, 8, 26), "bg_mid": (2, 4, 14), "bg_bot": (6, 10, 28),
            "border": "#113388",
            "fire_core": (30, 100, 230), "fire_mid": (20, 70, 180), "fire_tip": (10, 50, 130),
            "ember_colors": [(30, 100, 230), (20, 70, 180), (10, 50, 130)],
        },
    },
    {
        "id": "classic_lime",
        "category": "classic",
        "name": "Токсичный лайм 🍀",
        "desc": "Ядовито-зелёный, как мутаген.",
        "desc_full": "Ядовито-зелёный, как мутаген.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "gold_dust",
        "bg_images": ["medal_03_1.png", "medal_03_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#66ee00", "secondary": "#44aa00", "accent": "#88ff33",
            "glow": "#55dd00",
            "bg_top": (10, 20, 4), "bg_mid": (5, 10, 2), "bg_bot": (12, 22, 5),
            "border": "#338800",
            "fire_core": (100, 230, 0), "fire_mid": (70, 180, 0), "fire_tip": (40, 130, 0),
            "ember_colors": [(100, 230, 0), (70, 180, 0), (40, 130, 0)],
        },
    },
    {
        "id": "classic_lavender",
        "category": "classic",
        "name": "Лавандовый туман 💜",
        "desc": "Мягкий лиловый, тёплый и загадочный.",
        "desc_full": "Мягкий лиловый, тёплый и загадочный.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "blue_dust",
        "bg_images": ["medal_02_1.png", "medal_02_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#bb88dd", "secondary": "#8855aa", "accent": "#ddaaff",
            "glow": "#aa77cc",
            "bg_top": (18, 10, 24), "bg_mid": (10, 5, 14), "bg_bot": (20, 12, 26),
            "border": "#664488",
            "fire_core": (180, 130, 220), "fire_mid": (140, 90, 180), "fire_tip": (100, 60, 140),
            "ember_colors": [(180, 130, 220), (140, 90, 180), (100, 60, 140)],
        },
    },
    {
        "id": "classic_copper",
        "category": "classic",
        "name": "Старая медь 🥉",
        "desc": "Тусклый медный блеск потемневшего металла.",
        "desc_full": "Тусклый медный блеск потемневшего металла.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "gold_dust",
        "bg_images": ["medal_01_1.png", "medal_01_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#bb7744", "secondary": "#885522", "accent": "#dd9966",
            "glow": "#aa6633",
            "bg_top": (22, 14, 8), "bg_mid": (12, 7, 4), "bg_bot": (24, 16, 10),
            "border": "#664422",
            "fire_core": (190, 120, 70), "fire_mid": (140, 80, 40), "fire_tip": (100, 60, 30),
            "ember_colors": [(190, 120, 70), (140, 80, 40), (100, 60, 30)],
        },
    },
    {
        "id": "classic_snow",
        "category": "classic",
        "name": "Белый шум 🤍",
        "desc": "Почти монохром — серебристо-белый на чёрном.",
        "desc_full": "Почти монохром — серебристо-белый на чёрном.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "blue_dust",
        "bg_images": ["medal_12_1.png", "medal_12_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#cccccc", "secondary": "#999999", "accent": "#eeeeee",
            "glow": "#bbbbbb",
            "bg_top": (12, 12, 14), "bg_mid": (6, 6, 7), "bg_bot": (14, 14, 16),
            "border": "#555555",
            "fire_core": (200, 200, 210), "fire_mid": (150, 150, 160), "fire_tip": (100, 100, 110),
            "ember_colors": [(200, 200, 210), (150, 150, 160), (100, 100, 110)],
        },
    },
    {
        "id": "classic_coral",
        "category": "classic",
        "name": "Коралловый риф 🪸",
        "desc": "Тёплый коралловый, как тропический закат.",
        "desc_full": "Тёплый коралловый, как тропический закат.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "gold_dust",
        "bg_images": ["medal_13_1.png", "medal_13_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#ff6655", "secondary": "#cc4433", "accent": "#ff8877",
            "glow": "#ee5544",
            "bg_top": (26, 10, 8), "bg_mid": (14, 5, 4), "bg_bot": (28, 12, 10),
            "border": "#883322",
            "fire_core": (255, 100, 80), "fire_mid": (200, 65, 50), "fire_tip": (150, 40, 30),
            "ember_colors": [(255, 100, 80), (200, 65, 50), (150, 40, 30)],
        },
    },
    {
        "id": "classic_forest",
        "category": "classic",
        "name": "Тёмный лес 🌲",
        "desc": "Глубокий тёмно-зелёный, как хвойная чаща.",
        "desc_full": "Глубокий тёмно-зелёный, как хвойная чаща.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "gold_dust",
        "bg_images": ["medal_14_1.png", "medal_14_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#228844", "secondary": "#115522", "accent": "#44bb66",
            "glow": "#117733",
            "bg_top": (4, 16, 8), "bg_mid": (2, 8, 4), "bg_bot": (6, 18, 10),
            "border": "#114422",
            "fire_core": (30, 140, 60), "fire_mid": (20, 100, 40), "fire_tip": (10, 70, 30),
            "ember_colors": [(30, 140, 60), (20, 100, 40), (10, 70, 30)],
        },
    },
    {
        "id": "classic_candy",
        "category": "classic",
        "name": "Карамелька 🍬",
        "desc": "Яркий маджента — сладкий и кричащий.",
        "desc_full": "Яркий маджента — сладкий и кричащий.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "blue_dust",
        "bg_images": ["medal_15_1.png", "medal_15_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#ee33aa", "secondary": "#aa1177", "accent": "#ff66cc",
            "glow": "#dd22aa",
            "bg_top": (24, 6, 18), "bg_mid": (14, 3, 10), "bg_bot": (26, 8, 20),
            "border": "#881166",
            "fire_core": (230, 50, 170), "fire_mid": (180, 30, 120), "fire_tip": (130, 20, 80),
            "ember_colors": [(230, 50, 170), (180, 30, 120), (130, 20, 80)],
        },
    },
    {
        "id": "classic_steel",
        "category": "classic",
        "name": "Холодная сталь ⚔️",
        "desc": "Стальной голубовато-серый, как клинок.",
        "desc_full": "Стальной голубовато-серый, как клинок.<br><br>• Особая цветовая гамма<br>• Фоновые частицы",
        "unlock": "hidden",
        "fire_scale": 0.75, "no_glow": True,
        "bg_particles": "blue_dust",
        "bg_images": ["medal_16_1.png", "medal_16_2.png"],
        "counter_font": "Arial",
        "colors": {
            "primary": "#7799bb", "secondary": "#556688", "accent": "#99bbdd",
            "glow": "#6688aa",
            "bg_top": (10, 14, 20), "bg_mid": (5, 7, 12), "bg_bot": (12, 16, 22),
            "border": "#445566",
            "fire_core": (120, 155, 190), "fire_mid": (80, 110, 140), "fire_tip": (50, 75, 100),
            "ember_colors": [(120, 155, 190), (80, 110, 140), (50, 75, 100)],
        },
    },

    # ─── НЕОНОВЫЕ (все текущие темы) ─────────────────────
    {
        "id": "inferno_classic",
        "category": "neon",
        "name": "Адское пламя 🔥",
        "desc": "Классический красно-оранжевый огонь. Начало всех начал.",
        "desc_full": "Классический красно-оранжевый огонь. Начало всех начал.<br><br>• Особая цветовая гамма<br>• Эффекты при обнаружении<br>• Особый шрифт",
        "unlock": "total:100",
        "tier": "gold",
        "theme_icon_text": ("🔥", "#ff2020"),
        "bg_particles": "embers",
        "detection_effect": "ember_shower",
        "colors": {
            "primary": "#ff2020",
            "secondary": "#ff6600",
            "accent": "#ffcc00",
            "glow": "#ff4000",
            "bg_top": (18, 3, 3),
            "bg_mid": (8, 0, 0),
            "bg_bot": (22, 5, 2),
            "border": "#ff0000",
            "fire_core": (255, 60, 0),
            "fire_mid": (255, 130, 0),
            "fire_tip": (255, 180, 30),
            "ember_colors": [(255, 80, 0), (255, 160, 0), (255, 30, 30)],
        },
    },
    {
        "id": "golden_emperor",
        "category": "neon",
        "name": "Золотой Император 👑",
        "desc": "Чистое золото и дождь из монет. Символ абсолютной власти.",
        "desc_full": "Чистое золото и дождь из монет. Символ абсолютной власти.<br><br>• Особая цветовая гамма<br>• Эффекты при обнаружении<br>• Особый шрифт",
        "unlock": "hidden",
        "tier": "purple",
        "theme_icon_text": ("👑", "#ffcc00"),
        "special_effect": "gold_rain",
        "bg_particles": "gold_rain",
        "detection_effect": "coin_shower",
        "colors": {
            "primary": "#ffcc00",
            "secondary": "#cc8800",
            "accent": "#ffee66",
            "glow": "#ffaa00",
            "bg_top": (18, 12, 2),
            "bg_mid": (8, 5, 0),
            "bg_bot": (22, 15, 3),
            "border": "#cc8800",
            "fire_core": (255, 180, 0),
            "fire_mid": (255, 220, 50),
            "fire_tip": (255, 240, 120),
            "ember_colors": [(255, 200, 0), (255, 160, 0), (255, 240, 80)],
        },
    },
    {
        "id": "shadow_lord",
        "category": "neon",
        "name": "Эго Жнеца 🫀",
        "desc": "Ядрёный красный на мерцающем чёрно-фиолетовом фоне.",
        "desc_full": "Ядрёный красный на мерцающем чёрно-фиолетовом фоне.<br><br>• Особая цветовая гамма<br>• Эффекты при обнаружении<br>• Особый шрифт",
        "unlock": "total:1000",
        "tier": "purple",
        "theme_icon_text": ("🫀", "#ff0000"),
        "unlock_condition_desc": "???",
        "animated": True,
        "bg_particles": "blood_rain",
        "detection_effect": "blood_rain",
        "colors": {
            "primary": "#ff0000",
            "secondary": "#cc0000",
            "accent": "#ff4444",
            "glow": "#ff0000",
            "bg_top": (0, 0, 0),
            "bg_mid": (0, 0, 0),
            "bg_bot": (60, 0, 70),
            "border": "#cc0000",
            "fire_core": (255, 0, 0),
            "fire_mid": (190, 0, 0),
            "fire_tip": (0, 0, 0),
            "ember_colors": [(255, 0, 0), (190, 0, 0), (190, 0, 50), (0, 0, 0)],
        },
    },

{
        "id": "toxic_green",
        "category": "neon",
        "name": "Токсичный ☢️",
        "desc": "Ядовито-зелёный радиоактивный огонь.",
        "desc_full": "Ядовито-зелёный радиоактивный огонь.<br><br>• Особая цветовая гамма<br>• Эффекты при обнаружении<br>• Особый шрифт",
        "unlock": "hidden",
        "tier": "gold",
        "theme_icon_text": ("☢️", "#33ff33"),
        "bg_particles": "radiation",
        "detection_effect": "radiation",
        "colors": {
            "primary": "#33ff33",
            "secondary": "#00cc00",
            "accent": "#aaff00",
            "glow": "#00ff44",
            "bg_top": (3, 15, 3),
            "bg_mid": (0, 6, 0),
            "bg_bot": (5, 18, 2),
            "border": "#00cc00",
            "fire_core": (0, 200, 30),
            "fire_mid": (50, 255, 50),
            "fire_tip": (150, 255, 80),
            "ember_colors": [(0, 220, 40), (80, 255, 0), (0, 180, 60)],
        },
    },
    {
        "id": "inferno_blue",
        "category": "neon",
        "name": "Инферно ❄️",
        "desc": "Глубокий синий огонь с проблесками белого льда.",
        "desc_full": "Глубокий синий огонь с проблесками белого льда.<br><br>• Особая цветовая гамма<br>• Эффекты при обнаружении<br>• Особый шрифт",
        "unlock": "hidden",
        "tier": "gold",
        "theme_icon_text": ("❄️", "#4488ff"),
        "bg_particles": "snow_wind",
        "detection_effect": "snow_wind",
        "colors": {
            "primary": "#4488ff",
            "secondary": "#0044cc",
            "accent": "#88ccff",
            "glow": "#0066ff",
            "bg_top": (3, 5, 20),
            "bg_mid": (0, 2, 10),
            "bg_bot": (2, 8, 25),
            "border": "#2244aa",
            "fire_core": (30, 80, 255),
            "fire_mid": (60, 140, 255),
            "fire_tip": (200, 230, 255),
            "ember_colors": [(40, 100, 255), (0, 60, 200), (220, 240, 255), (180, 210, 255)],
        },
    },
    {
        "id": "void_purple",
        "category": "neon",
        "name": "Пустота 🔮",
        "desc": "Фиолетово-чёрная бездна. Холодный огонь.",
        "desc_full": "Фиолетово-чёрная бездна. Холодный огонь.<br><br>• Особая цветовая гамма<br>• Эффекты при обнаружении<br>• Особый шрифт",
        "unlock": "hidden",
        "tier": "gold",
        "theme_icon_text": ("🔮", "#bb44ff"),
        "bg_particles": "fog",
        "detection_effect": "fog",
        "colors": {
            "primary": "#bb44ff",
            "secondary": "#8800cc",
            "accent": "#dd88ff",
            "glow": "#9900ff",
            "bg_top": (10, 3, 18),
            "bg_mid": (3, 0, 8),
            "bg_bot": (12, 2, 22),
            "border": "#8800cc",
            "fire_core": (140, 20, 255),
            "fire_mid": (180, 60, 255),
            "fire_tip": (220, 120, 255),
            "ember_colors": [(160, 40, 255), (100, 0, 200), (200, 80, 255)],
        },
    },

{
        "id": "hysteria",
        "category": "neon",
        "name": "Истерия 🃏",
        "desc": "Лиловый хаос с бежевым интерфейсом. Радужный огонь.",
        "desc_full": "Лиловый хаос с бежевым интерфейсом. Радужный огонь.<br><br>• Особая цветовая гамма<br>• Эффекты при обнаружении<br>• Особый шрифт",
        "unlock": "hidden",
        "tier": "gold",
        "theme_icon_text": ("🃏", "#6633dd"),
        "unlock_condition_desc": "???",
        "animated": True,
        "bg_particles": "pulse_matter",
        "detection_effect": "dark_pulse",
        "colors": {
            "primary": "#6633dd",
            "secondary": "#c4a878",
            "accent": "#e8d0a8",
            "glow": "#bb88ee",
            "bg_top": (255, 255, 255),
            "bg_mid": (235, 195, 130),
            "bg_bot": (200, 100, 40),
            "border": "#9966cc",
            "fire_core": (200, 50, 50),
            "fire_mid": (50, 200, 50),
            "fire_tip": (50, 100, 255),
            "ember_colors": [
                (255, 80, 80), (80, 255, 80), (80, 80, 255),
                (255, 255, 0), (255, 0, 255), (0, 255, 255),
                (255, 160, 0), (160, 0, 255),
            ],
        },
    },

    # ─── САТИРИЧЕСКИЕ ──────────────────────────────────
    {
        "id": "hellish_mexican",
        "icon": "mex.png",
        "category": "satirical",
        "name": "Адская 🌶",
        "desc": "Мексиканский ад. Перцы, огонь, маракасы и марьячи.",
        "desc_full": "Мексиканский ад. Перцы, огонь, маракасы и марьячи.<br><br>• Особая цветовая гамма<br>• Эффекты при обнаружении<br>• Особый шрифт<br>• Фоновый рисунок<br><br>✦ <b>ПЕРСОНАЛЬНАЯ ОСОБЕННОСТЬ</b><br>Эффекты при любом взаимодействии с окном.",
        "unlock": "hidden",
        "fire_scale": 0.85,
        "no_glow": True,
        "bg_image_file": "backmex.png",
        "bg_particles": "gold_dust",
        "emoji_explosions": True,
        "counter_font": "Trebuchet MS",
        "counter_outline_color": "#ff6600",
        "colors": {
            "primary": "#006847",       # зелёный (флаг Мексики)
            "secondary": "#ce1126",     # красный (флаг)
            "accent": "#ffffff",        # белый (флаг)
            "glow": "#ff4500",
            "bg_top": (18, 6, 2),
            "bg_mid": (10, 2, 0),
            "bg_bot": (22, 8, 3),
            "border": "#ce1126",
            "fire_core": (255, 60, 0),
            "fire_mid": (255, 130, 0),
            "fire_tip": (255, 200, 30),
            "ember_colors": [(255, 80, 0), (255, 40, 20), (255, 200, 0), (255, 150, 30)],
        },
    },
    {
        "id": "modern_windows",
        "icon": "win_ico.png",
        "category": "satirical",
        "name": "Современная 🖥",
        "desc": "Стилизация под раннюю Windows. Пузырьки, дельфин и медиа-плеер.",
        "desc_full": "Стилизация под раннюю Windows. Пузырьки, дельфин и медиа-плеер.<br><br>• Особая цветовая гамма<br>• Фоновые частицы<br>• Эффекты при обнаружении<br>• Особый шрифт<br>• Фоновый рисунок",
        "unlock": "hidden",
        "fire_scale": 0.0,             # нет огня — пузыри вместо него
        "no_glow": True,
        "no_grid": True,
        "sharp_corners": True,
        "bg_image_file": "win_bg.jpg",
        "bg_particles": "bubbles",
        "bubble_detection": True,       # пузыри вместо огня + дельфин
        "counter_font": "Digital-7 Mono",  # LCD циферблат часов
        "counter_font_scale": 0.45,
        "counter_color": "#ffffff",
        "counter_bg_image": "win_display.png",  # медиа-плеер за счётчиком
        "btn_images": {
            "start": "win_btn_start.png",
            "zone": "win_btn_zone.png",
            "mercy": "win_btn_mercy.png",
            "colorpicker": "win_btn_colorpicker.png",
        },
        "colors": {
            "primary": "#00ff55",       # ярко-зелёный надписи
            "secondary": "#3388ff",
            "accent": "#66bbff",
            "glow": "#0066ff",
            "bg_top": (0, 90, 200),     # голубой сверху
            "bg_mid": (0, 60, 150),
            "bg_bot": (0, 40, 120),     # тёмно-синий снизу
            "border": "#0044aa",
            "fire_core": (100, 180, 255),   # голубые пузыри
            "fire_mid": (60, 140, 220),
            "fire_tip": (150, 210, 255),
            "ember_colors": [(100, 180, 255), (60, 200, 255), (150, 220, 255), (200, 240, 255)],
        },
    },
    # ─── Системная: наказание / анти-чит — максимально неприятная «коричневая» тема ───
    {
        "id": "cheater_clown",
        "category": "satirical",
        "name": "Читерство — позор 🤡💩",
        "desc": "Системная тема за накрутку. Наслаждайся.",
        "unlock": None,
        "fire_scale": 0.88,
        "no_glow": True,
        "bg_particles": "gold_dust",
        "counter_font": "Comic Sans MS",
        "counter_font_scale": 1.02,
        "colors": {
            "primary": "#6b3d22",
            "secondary": "#4a2c16",
            "accent": "#8b5a2b",
            "glow": "#3d2814",
            "bg_top": (55, 35, 22),
            "bg_mid": (40, 25, 15),
            "bg_bot": (28, 18, 10),
            "border": "#5c3d26",
            "fire_core": (120, 70, 40),
            "fire_mid": (90, 55, 30),
            "fire_tip": (140, 85, 45),
            "ember_colors": [(100, 60, 35), (75, 45, 25), (130, 80, 45), (60, 40, 22)],
        },
    },
    # Награда после отбытия наказания — прежняя «клоунская» палитра (яркая), скрытая в магазине
    {
        "id": "clown_redemption",
        "category": "satirical",
        "name": "Цирк остыл 🤡✨",
        "desc": "Тема за честное отбытие наказания за накрутку.",
        "unlock": "hidden",
        "fire_scale": 0.92,
        "bg_particles": "gold_dust",
        "counter_font": "Comic Sans MS",
        "counter_font_scale": 1.0,
        "colors": {
            "primary": "#ff00ff",
            "secondary": "#00ffff",
            "accent": "#ffff00",
            "glow": "#ff0088",
            "bg_top": (80, 20, 90),
            "bg_mid": (40, 10, 60),
            "bg_bot": (120, 60, 20),
            "border": "#00ff00",
            "fire_core": (255, 0, 200),
            "fire_mid": (0, 255, 255),
            "fire_tip": (255, 255, 0),
            "ember_colors": [(255, 0, 255), (0, 255, 0), (255, 128, 0), (0, 128, 255)],
        },
    },
]

CHEATER_THEME_ID = "cheater_clown"
CLOWN_REDEMPTION_THEME_ID = "clown_redemption"

DEFAULT_THEME_ID = "ultra_default"


def get_theme_by_id(theme_id: str) -> dict | None:
    for t in THEMES:
        if t["id"] == theme_id:
            return t
    return None


def get_themes_by_category() -> list[tuple[dict, list[dict]]]:
    """
    Возвращает список (category_info, [themes...]) в порядке THEME_CATEGORY_ORDER.
    Пустые категории тоже возвращаются (для будущего заполнения).
    """
    from collections import OrderedDict
    grouped = OrderedDict()
    for cat in THEME_CATEGORIES:
        grouped[cat["id"]] = (cat, [])
    for t in THEMES:
        cat_id = t.get("category", "neon")
        if cat_id in grouped:
            grouped[cat_id][1].append(t)
    return list(grouped.values())


def get_unlocked_themes(unlocked_categories: set, total_twos: int,
                        total_achievements: int = 0, max_combo: int = 0,
                        streak: int = 0, purchased_themes: set | None = None,
                        streak_lost: bool = False) -> list:
    """
    Возвращает список тем с полем 'available': True/False.
    unlock=None          → всегда доступна
    unlock="total:X"     → доступна при total_twos >= X
    unlock="hidden"      → доступна ТОЛЬКО если theme_id в purchased_themes
    unlock="streak_lost" → доступна если streak_lost=True или theme_id в purchased_themes
    """
    if purchased_themes is None:
        purchased_themes = set()

    result = []
    for t in THEMES:
        theme = dict(t)
        unlock = t.get("unlock")
        available = False
        lock_reason = ""

        if unlock is None:
            available = True
        elif isinstance(unlock, str) and unlock.startswith("total:"):
            try:
                required = int(unlock.split(":")[1])
            except (IndexError, ValueError):
                required = 0
            if total_twos >= required:
                available = True
            else:
                lock_reason = f"Нужно {required} двоек (сейчас {total_twos})"
        elif unlock == "hidden":
            if t["id"] in purchased_themes:
                available = True
            else:
                lock_reason = "???"
        elif unlock == "streak_lost":
            if streak_lost or t["id"] in purchased_themes:
                available = True
            else:
                lock_reason = "???"
        else:
            # Неизвестный тип — не открыта
            lock_reason = "Условие не выполнено"

        theme["available"] = available
        theme["lock_reason"] = lock_reason
        result.append(theme)
    return result
