"""
Inferno Grade Tracker — Overlay (v4)
Массивный огонь. Все randint безопасны.
"""
import math
import random
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QRadialGradient, QPixmap, QMovie, QTransform
from modules.asset_loader import load_pixmap, load_movie, is_gif


def safe_randint(a, b):
    """randint без краша если a >= b."""
    if a >= b: return a
    return random.randint(a, b)


class Particle:
    def __init__(self, x, y, color, size=4, lifetime=80):
        self.x, self.y = float(x), float(y)
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-6, -1)
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.age = 0
    def update(self):
        self.x += self.vx; self.y += self.vy
        self.vy += 0.03; self.vx *= 0.99; self.age += 1
    @property
    def alpha(self):
        return max(0, int(255 * (1 - self.age / max(1, self.lifetime))))
    @property
    def alive(self): return self.age < self.lifetime


class GoldCoin:
    """Золотая монета для эффекта дождя из монет (тема Золотой Император)."""
    def __init__(self, x, y, sw, sh):
        self.x, self.y = float(x), float(y)
        self.vy = random.uniform(2, 6)
        self.vx = random.uniform(-1.5, 1.5)
        self.size = random.randint(4, 10)
        self.rotation = random.uniform(0, 6.28)
        self.rot_speed = random.uniform(0.05, 0.2)
        self.lifetime = int(sh / self.vy) + 30
        self.age = 0
        self.bright = random.randint(180, 255)
        self._fading = False
        self._fade_alpha = 255
    def update(self):
        self.x += self.vx; self.y += self.vy
        self.rotation += self.rot_speed; self.age += 1
        self.vy += 0.02
        if self._fading:
            self._fade_alpha = max(0, self._fade_alpha - 4)
    def start_fade(self):
        """Начать плавное угасание монеты."""
        self._fading = True
    @property
    def alive(self):
        if self._fading:
            return self._fade_alpha > 0
        return self.age < self.lifetime
    @property
    def alpha(self):
        if self._fading:
            return self._fade_alpha
        if self.age < 10: return int(255 * self.age / 10)
        if self.age > self.lifetime - 40: return max(0, int(255 * (self.lifetime - self.age) / 40))
        return 255


class ZoneIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._label = ""; self._debug = ""; self._active = False; self._blink = False
        t = QTimer(self); t.timeout.connect(lambda: (setattr(self, '_blink', not self._blink), self.update())); t.start(800)

    def update_zone(self, x, y, w, h):
        self.setGeometry(x-3, y-3, w+6, h+6); self._label = f"{w}×{h}"; self.show(); self.raise_()

    def set_active(self, a): self._active = a; self.update()
    def set_debug_text(self, t): self._debug = t; self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        c = QColor(0,255,0,180 if self._blink else 100) if self._active else QColor(255,40,40,150)
        p.setPen(QPen(c, 2, Qt.PenStyle.DashLine)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(2,2,w-4,h-4)
        bg = QRect(0,0,min(w,250),18)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0,0,0,180)); p.drawRect(bg)
        p.setPen(c); p.setFont(QFont("Consolas",8,QFont.Weight.Bold))
        st = "●" if self._active else "○"
        p.drawText(bg, Qt.AlignmentFlag.AlignCenter, f"🔥 {self._label} {st}")
        if self._debug:
            db = QRect(0,h-16,min(w,350),16)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0,0,0,180)); p.drawRect(db)
            p.setPen(QColor(255,200,50)); p.setFont(QFont("Consolas",7))
            p.drawText(db, Qt.AlignmentFlag.AlignCenter, self._debug)
        p.end()


class InfernoOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._p = []; self._fire = 0.0; self._gl = 0; self._msg = ""; self._ma = 0
        self._mpm = None; self._mr = QRect(); self._sh = QPoint(0,0); self._lv = 0; self._fr = 0
        self._movie = None  # QMovie для GIF-анимации
        # Цвета огня (обновляются при смене темы)
        self._fire_core = (255, 60, 0)
        self._fire_mid = (255, 130, 0)
        self._fire_tip = (255, 180, 30)
        self._ember_colors = [(255,80,0), (255,160,0), (255,30,30), (255,220,50), (200,200,200,120)]
        self._text_color = (255, 40, 40)
        self._special_effect = None
        self._gold_coins = []
        self._theme_id = ""
        self._overlay_lasers = []   # злодейская: багровые лазеры через весь экран
        self._overlay_stars = []    # закат: звёздочки-искорки
        self._overlay_bubbles = []  # современная: пузыри
        self._dolphins = []         # современная: несколько дельфинов
        self._particles = []        # тематические эффекты детекции
        self._detection_effect = ""
        self._at = QTimer(self); self._at.timeout.connect(self._tick)
        self._ht = QTimer(self); self._ht.setSingleShot(True); self._ht.timeout.connect(self._done)

    def set_theme(self, theme):
        """Обновляет цвета огня из темы."""
        c = theme["colors"]
        self._fire_core = tuple(c["fire_core"])
        self._fire_mid = tuple(c["fire_mid"])
        self._fire_tip = tuple(c["fire_tip"])
        self._ember_colors = [tuple(e) for e in c["ember_colors"]]
        # Не добавляем яркие частицы к тёмным/дымным темам
        if theme.get("id") != "ominous":
            self._ember_colors.append((255, 220, 50))
            self._ember_colors.append((200, 200, 200))
        pc = QColor(c["primary"])
        self._text_color = (pc.red(), pc.green(), pc.blue())
        # Спец-эффект
        self._special_effect = theme.get("special_effect", None)
        self._gold_coins = []
        # Масштаб огня (0.0–1.0, по умолчанию 1.0)
        self._fire_scale = theme.get("fire_scale", 1.0)
        self._theme_id = theme.get("id", "")
        self._detection_effect = theme.get("detection_effect", "")

    def trigger(self, msg, level=0, meme=None, dur=6000):
        self._lv = level; self._msg = msg; self._ma = 255
        fs = self._fire_scale
        self._fire = min((0.6 + level * 0.15) * fs, 1.0)
        self._gl = max(1, int((8 + level * 12) * fs)); self._fr = 0
        self._overlay_bubbles = []
        self._dolphin = None
        scr = QApplication.primaryScreen()
        if scr: self.setGeometry(scr.geometry())
        sw, sh = self.width() or 1920, self.height() or 1080
        is_ominous = self._theme_id == "ominous"
        if is_ominous:
            # Зловещая: огромный клуб чёрного дыма по всему экрану
            smoke_colors = [QColor(10,10,15), QColor(20,20,25), QColor(5,5,8),
                            QColor(30,28,32), QColor(15,12,18)]
            # Снизу — плотный клуб
            for _ in range(250 + level * 100):
                c = random.choice(smoke_colors)
                pa = Particle(random.randint(0, sw), sh + safe_randint(0, 60), c,
                              safe_randint(15, 45 + level * 10), 120 + safe_randint(0, 100))
                pa.vy = random.uniform(-6 - level * 2, -0.5)
                pa.vx = random.uniform(-3, 3)
                self._p.append(pa)
            # Со сторон — клубы заползающие внутрь
            for _ in range(100 + level * 50):
                side = random.choice([0, sw])
                c = random.choice(smoke_colors)
                pa = Particle(side, safe_randint(0, sh), c,
                              safe_randint(20, 50), 90 + safe_randint(0, 80))
                pa.vx = random.uniform(2, 6) * (1 if side == 0 else -1)
                pa.vy = random.uniform(-4, 2)
                self._p.append(pa)
            # Сверху — дым падает
            for _ in range(80 + level * 40):
                c = random.choice(smoke_colors)
                pa = Particle(random.randint(0, sw), -safe_randint(10, 60), c,
                              safe_randint(12, 35), 80 + safe_randint(0, 70))
                pa.vy = random.uniform(0.5, 4)
                pa.vx = random.uniform(-2, 2)
                self._p.append(pa)
        elif self._theme_id == "bottomless":
            # Бездонная: тёмные частицы летят к счётчику, от чёрных до белых
            self._abyss_particles = []
            self._abyss_glow_boost = 0.0  # нарастание свечения счётчика
            app_cx, app_cy = sw // 2, sh // 2
            for w_obj in QApplication.topLevelWidgets():
                if hasattr(w_obj, 'counter_label'):
                    geo = w_obj.geometry()
                    app_cx = geo.x() + geo.width() // 2
                    app_cy = geo.y() + geo.height() // 2
                    break
            for i in range(305):
                # Спавн по краям экрана с задержкой (0-250 кадров = ~4с при 16мс тике)
                delay = int(i * 250 / 305)
                brightness = int(i * 255 / 304)  # 0=чёрный → 255=белый
                side = random.choice([0, 1, 2, 3])
                if side == 0: sx, sy = random.randint(0, sw), 0
                elif side == 1: sx, sy = random.randint(0, sw), sh
                elif side == 2: sx, sy = 0, random.randint(0, sh)
                else: sx, sy = sw, random.randint(0, sh)
                self._abyss_particles.append({
                    "x": float(sx), "y": float(sy),
                    "tx": float(app_cx), "ty": float(app_cy),
                    "brightness": brightness, "delay": delay,
                    "size": random.uniform(3, 8),
                    "alpha": 220, "speed": random.uniform(3.0, 7.0),
                    "alive": True,
                })
        else:
            cs = [QColor(*e[:3]) for e in self._ember_colors]
            # Адская: классический огонь — только круги, красно-жёлтые
            is_classic_fire = self._theme_id == "hellish_mexican"
            # 2x больше частиц, крупнее, ярче
            p_count = int((160 + level * 120) * fs)
            for _ in range(p_count):
                pa = Particle(random.randint(0,sw), sh + safe_randint(0,30), random.choice(cs),
                              safe_randint(6, 16+level*5), 80+safe_randint(0, 70+level*40))
                pa.vy = random.uniform(-14-level*4, -3); pa.vx = random.uniform(-5,5)
                if is_classic_fire:
                    pa._shape = 0  # только круги
                else:
                    pa._shape = random.choice([3, 5, 6])  # треугольник/пятиугольник/шестиугольник
                    pa._rot = random.uniform(0, math.pi * 2)
                self._p.append(pa)
            fc = self._fire_core
            for _ in range(int((40 + level * 30) * fs)):
                side = random.choice([0, sw])
                pa = Particle(side, safe_randint(sh//3, sh), QColor(fc[0], safe_randint(min(fc[1],50),max(fc[1],180)), fc[2]),
                              safe_randint(4,12), 60+safe_randint(0,50))
                pa.vx = random.uniform(3,8) * (1 if side==0 else -1); pa.vy = random.uniform(-10,-3)
                if is_classic_fire:
                    pa._shape = 0
                else:
                    pa._shape = random.choice([3, 5, 6])
                    pa._rot = random.uniform(0, math.pi * 2)
                self._p.append(pa)
        # Современная: пузыри вместо огня + несколько дельфинов
        if self._theme_id == "modern_windows":
            self._fire = 0.5
            import os
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
            dolphin_path = os.path.join(base, "win_dolphin.png.enc")
            if not os.path.exists(dolphin_path):
                dolphin_path = os.path.join(base, "win_dolphin.png")
            dpm = load_pixmap(dolphin_path)
            self._dolphins = []
            if not dpm.isNull():
                dsz = 220 + level * 50  # огромные дельфины
                dpm_scaled = dpm.scaled(dsz, dsz, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                dpm_flipped = dpm_scaled.transformed(QTransform().scale(-1, 1))
                # Несколько дельфинов с разными позициями и задержками
                positions = [0.12, 0.35, 0.55, 0.78, 0.92]
                delays = [0, 30, 12, 45, 22]
                jump_strengths = [16, 12, 18, 11, 14]
                hang_times = [35, 28, 40, 25, 32]  # тиков зависания в воздухе
                flips = [False, True, False, True, False]
                for i, (xfrac, delay, jstr, hang, flip) in enumerate(zip(positions, delays, jump_strengths, hang_times, flips)):
                    dx = int(sw * xfrac) - dpm_scaled.width() // 2
                    pm_use = dpm_flipped if flip else dpm_scaled
                    self._dolphins.append({
                        "pm": pm_use,
                        "x": float(dx), "y": float(sh + 50),
                        "vy": -(jstr + level * 2),
                        "age": -delay,
                        "rotation": 0,
                        "rot_speed": 0.4 if not flip else -0.4,
                        "flip": flip,
                        "hang_time": hang,  # зависание на вершине
                        "hanging": 0,       # счётчик зависания
                        "phase": "rise",    # rise -> hang -> fall
                    })
            for _ in range(120 + level * 60):
                bx = random.randint(0, sw)
                by = sh + random.randint(0, 80)
                bsz = random.uniform(8, 35 + level * 8)
                self._overlay_bubbles.append({
                    "x": float(bx), "y": float(by),
                    "vx": random.uniform(-2, 2),
                    "vy": random.uniform(-8 - level * 2, -2),
                    "size": bsz,
                    "phase": random.uniform(0, 6.28),
                    "sway_speed": random.uniform(0.05, 0.15),
                    "alpha": random.randint(150, 255),
                    "age": 0,
                    "lifetime": random.randint(80, 180),
                })
        self._mpm = None
        if self._movie:
            self._movie.stop(); self._movie = None
        if meme:
            try:
                sz = min(350+level*60, 550)
                # GIF — используем QMovie для анимации (поддержка .gif и .gif.enc)
                if is_gif(meme):
                    self._movie = load_movie(meme)
                    if self._movie and self._movie.isValid():
                        self._movie.setScaledSize(QSize(sz, sz))
                        self._movie.start()
                        pm = self._movie.currentPixmap()
                        if not pm.isNull():
                            self._mpm = pm
                            self._mr = QRect((sw-pm.width())//2, (sh-pm.height())//2-60, pm.width(), pm.height())
                    else:
                        self._movie = None
                else:
                    pm = load_pixmap(meme)
                    if not pm.isNull():
                        self._mpm = pm.scaled(sz,sz,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
                        self._mr = QRect((sw-self._mpm.width())//2, (sh-self._mpm.height())//2-60, self._mpm.width(), self._mpm.height())
            except: pass
        # Злодейская: лазеры волнами (5-7 штук, по 1-2 за волну каждые ~30 кадров)
        self._overlay_lasers = []
        self._villain_laser_queue = []
        if self._theme_id == "villain":
            total = random.randint(5, 7)
            spawned = 0
            wave_frame = 0
            while spawned < total:
                batch = random.randint(1, min(2, total - spawned))
                for _ in range(batch):
                    self._villain_laser_queue.append(wave_frame)
                spawned += batch
                wave_frame += 30  # ~0.5 секунды между волнами
        # Закат: пышный хлопок звёзд из солнца + снизу
        self._overlay_stars = []
        if self._theme_id == "sunset":
            # Из центра (солнце) — 40-55 звёздочек
            cx, cy = sw // 2, sh // 2 - 60
            for _ in range(random.randint(40, 55)):
                angle = random.uniform(0, 360)
                speed = random.uniform(1.5, 9.0)
                self._overlay_stars.append({
                    "x": float(cx) + random.uniform(-20, 20),
                    "y": float(cy) + random.uniform(-20, 20),
                    "vx": math.cos(math.radians(angle)) * speed,
                    "vy": math.sin(math.radians(angle)) * speed,
                    "size": random.randint(6, 18),
                    "rotation": random.uniform(0, 360),
                    "rot_speed": random.uniform(3, 10),
                    "alpha": 255, "age": 0,
                    "lifetime": random.randint(150, 320),  # дольше живут
                    "color_idx": random.randint(0, 3),
                })
            # Снизу — 20-30 звёздочек взлетают вверх
            for _ in range(random.randint(20, 30)):
                sx = random.randint(int(sw * 0.1), int(sw * 0.9))
                sy = float(sh) + random.uniform(0, 20)
                angle = random.uniform(240, 300)  # вверх
                speed = random.uniform(3.0, 10.0)
                self._overlay_stars.append({
                    "x": float(sx), "y": sy,
                    "vx": math.cos(math.radians(angle)) * speed,
                    "vy": math.sin(math.radians(angle)) * speed,
                    "size": random.randint(5, 14),
                    "rotation": random.uniform(0, 360),
                    "rot_speed": random.uniform(3, 10),
                    "alpha": 255, "age": 0,
                    "lifetime": random.randint(120, 280),
                    "color_idx": random.randint(0, 3),
                })
        # Заряженная: 2 молнии с интервалом + искры из окна наружу
        self._charged_sparks_out = []
        if self._theme_id == "charged":
            # 2 молнии: первая сразу, вторая через ~0.4с (25 кадров)
            self._villain_laser_queue = [0, 25]
            self._overlay_lasers = []
            # Искры из центра окна наружу (ищем окно приложения)
            app_cx, app_cy = sw // 2, sh // 2
            # Пробуем найти главное окно
            for w_obj in QApplication.topLevelWidgets():
                if hasattr(w_obj, 'counter_label'):
                    geo = w_obj.geometry()
                    app_cx = geo.x() + geo.width() // 2
                    app_cy = geo.y() + geo.height() // 2
                    break
            for _ in range(40):
                angle = random.uniform(0, 360)
                speed = random.uniform(4.0, 14.0)
                self._charged_sparks_out.append({
                    "x": float(app_cx) + random.uniform(-30, 30),
                    "y": float(app_cy) + random.uniform(-30, 30),
                    "vx": math.cos(math.radians(angle)) * speed,
                    "vy": math.sin(math.radians(angle)) * speed,
                    "size": random.randint(3, 8),
                    "alpha": 255, "age": 0,
                    "lifetime": random.randint(60, 140),
                    "color": random.choice([(200,220,255), (255,255,180), (180,200,255), (255,255,255)]),
                })
        # Тематические эффекты детекции
        self._particles = []
        det = self._detection_effect
        if det == "coin_shower":
            # Gold coins falling from top
            for _ in range(80 + level * 40):
                x = random.uniform(0, sw)
                self._particles.append({
                    "x": x, "y": random.uniform(-50, -10),
                    "vx": random.uniform(-0.5, 0.5),
                    "vy": random.uniform(2.0, 5.0),
                    "size": random.randint(4, 10),
                    "life": random.randint(120, 250),
                    "max_life": 250,
                    "color": random.choice([(255, 215, 0), (255, 200, 50), (218, 165, 32), (255, 223, 100)]),
                    "shape": "circle",
                    "spin": random.uniform(-3, 3),
                })
        elif det == "blood_rain":
            # Blood drops falling + purple flashes
            for _ in range(100 + level * 50):
                x = random.uniform(0, sw)
                self._particles.append({
                    "x": x, "y": random.uniform(-80, -5),
                    "vx": random.uniform(-0.3, 0.3),
                    "vy": random.uniform(3.0, 7.0),
                    "size": random.randint(2, 6),
                    "life": random.randint(100, 200),
                    "max_life": 200,
                    "color": random.choice([(180, 0, 0), (140, 0, 0), (200, 20, 20), (100, 0, 0)]),
                    "shape": "circle",
                })
        elif det == "fog":
            # Slow fog particles drifting
            for _ in range(40 + level * 15):
                self._particles.append({
                    "x": random.uniform(0, sw),
                    "y": random.uniform(sh * 0.5, sh),
                    "vx": random.uniform(-0.5, 0.5),
                    "vy": random.uniform(-0.3, 0.3),
                    "size": random.randint(20, 50),
                    "life": random.randint(200, 400),
                    "max_life": 400,
                    "color": (80, 50, 120),
                    "alpha": random.randint(20, 60),
                    "shape": "fog",
                })
        elif det == "dark_pulse":
            # Pulsing dark matter from center
            cx, cy = sw // 2, sh // 2
            for _ in range(60 + level * 30):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(1.0, 5.0)
                self._particles.append({
                    "x": cx + random.uniform(-30, 30),
                    "y": cy + random.uniform(-30, 30),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "size": random.randint(3, 12),
                    "life": random.randint(80, 180),
                    "max_life": 180,
                    "color": random.choice([(30, 0, 40), (50, 0, 70), (20, 0, 30), (60, 10, 80)]),
                    "shape": "circle",
                })
        elif det == "ember_shower":
            # Glowing embers rising from bottom
            for _ in range(90 + level * 40):
                x = random.uniform(0, sw)
                self._particles.append({
                    "x": x, "y": random.uniform(sh * 0.8, sh + 20),
                    "vx": random.uniform(-1.0, 1.0),
                    "vy": random.uniform(-4.0, -1.0),
                    "size": random.randint(2, 7),
                    "life": random.randint(100, 250),
                    "max_life": 250,
                    "color": random.choice([(255, 100, 0), (255, 60, 0), (255, 160, 30), (255, 200, 50)]),
                    "shape": "circle",
                })
        elif det == "radiation":
            # Radioactive glow particles spreading outward
            cx, cy = sw // 2, sh // 2
            for _ in range(50 + level * 25):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(50, 300)
                speed = random.uniform(0.5, 3.0)
                self._particles.append({
                    "x": cx + math.cos(angle) * dist * 0.3,
                    "y": cy + math.sin(angle) * dist * 0.3,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "size": random.randint(3, 10),
                    "life": random.randint(100, 200),
                    "max_life": 200,
                    "color": random.choice([(0, 255, 0), (50, 200, 0), (80, 255, 30), (0, 180, 0)]),
                    "shape": "circle",
                })
        elif det == "snow_wind":
            # Snowflakes blowing from left to right
            for _ in range(70 + level * 30):
                self._particles.append({
                    "x": random.uniform(-30, sw * 0.3),
                    "y": random.uniform(0, sh),
                    "vx": random.uniform(2.0, 6.0),
                    "vy": random.uniform(-1.0, 1.0),
                    "size": random.randint(2, 6),
                    "life": random.randint(150, 300),
                    "max_life": 300,
                    "color": (200, 220, 255),
                    "shape": "circle",
                })
        self.showFullScreen(); self.raise_()
        base_dur = max(dur, 6000+level*2000)
        if self._theme_id == "bottomless":
            base_dur = max(base_dur, 14000)  # 14с для всех частиц
        self._at.start(16); self._ht.start(base_dur)

    def kill(self):
        self._at.stop(); self._ht.stop(); self._p.clear(); self._gold_coins.clear(); self._mpm = None
        self._overlay_lasers.clear(); self._overlay_stars.clear(); self._villain_laser_queue = []; self._charged_sparks_out = []
        self._overlay_bubbles = []; self._dolphins = []; self._particles = []
        if self._movie: self._movie.stop(); self._movie = None
        self.hide()

    def _tick(self):
        self._fr += 1
        for pa in self._p: pa.update()
        self._p = [pa for pa in self._p if pa.alive]
        if self._fr > 80: self._ma = max(0, self._ma - 2)
        if self._gl > 0:
            self._gl -= 1; s = self._lv + 1
            self._sh = QPoint(safe_randint(-10,10)*s, safe_randint(-6,6)*s)
        else: self._sh = QPoint(0,0)
        self._fire = max(0, self._fire - 0.002)
        # Золотой дождь из монет
        if self._special_effect == "gold_rain":
            sw, sh = self.width() or 1920, self.height() or 1080
            if self._fire > 0.1:
                # Спавним новые монеты пока огонь горит
                for _ in range(random.randint(1, 3)):
                    self._gold_coins.append(GoldCoin(random.randint(0, sw), -10, sw, sh))
            elif self._gold_coins:
                # Огонь гаснет — запускаем плавное угасание всех монет
                for coin in self._gold_coins:
                    coin.start_fade()
            for coin in self._gold_coins: coin.update()
            self._gold_coins = [c for c in self._gold_coins if c.alive]
        # Злодейская: спавн лазеров из очереди по волнам
        if hasattr(self, '_villain_laser_queue') and self._villain_laser_queue:
            sw_, sh_ = self.width() or 1920, self.height() or 1080
            new_queue = []
            for spawn_frame in self._villain_laser_queue:
                if self._fr >= spawn_frame:
                    lx = random.randint(int(sw_ * 0.1), int(sw_ * 0.9))
                    ly = random.randint(int(sh_ * 0.1), int(sh_ * 0.9))
                    self._overlay_lasers.append({
                        "x": lx, "y": ly,
                        "angle": random.uniform(0, 360),
                        "length": random.randint(5000, 8000),
                        "alpha": 0, "age": 0,
                        "max_age": random.randint(40, 80),
                    })
                else:
                    new_queue.append(spawn_frame)
            self._villain_laser_queue = new_queue
        # Злодейская: обновление лазеров
        if self._overlay_lasers:
            alive = []
            for las in self._overlay_lasers:
                las["age"] += 1
                prog = las["age"] / las["max_age"]
                if prog < 0.15:
                    las["alpha"] = int(220 * (prog / 0.15))
                elif prog < 0.5:
                    las["alpha"] = 220
                else:
                    las["alpha"] = int(220 * (1.0 - (prog - 0.5) / 0.5))
                if las["age"] < las["max_age"]:
                    alive.append(las)
            self._overlay_lasers = alive
        # Закат: обновление звёздочек
        if self._overlay_stars:
            alive = []
            for st in self._overlay_stars:
                st["age"] += 1
                st["x"] += st["vx"]
                st["y"] += st["vy"]
                st["vx"] *= 0.99; st["vy"] *= 0.99  # замедление
                st["rotation"] += st["rot_speed"]
                # Затухание
                remaining = 1.0 - st["age"] / st["lifetime"]
                st["alpha"] = max(0, int(255 * remaining))
                if st["age"] < st["lifetime"]:
                    alive.append(st)
            self._overlay_stars = alive
        # Заряженная: обновление искр наружу
        if hasattr(self, '_charged_sparks_out') and self._charged_sparks_out:
            alive = []
            for sp in self._charged_sparks_out:
                sp["age"] += 1
                sp["x"] += sp["vx"]
                sp["y"] += sp["vy"]
                sp["vx"] *= 0.98; sp["vy"] *= 0.98
                remaining = 1.0 - sp["age"] / sp["lifetime"]
                sp["alpha"] = max(0, int(255 * remaining))
                if sp["age"] < sp["lifetime"]:
                    alive.append(sp)
            self._charged_sparks_out = alive
        # Тематические частицы детекции
        if self._particles:
            alive = []
            for pt in self._particles:
                pt["life"] -= 1
                pt["x"] += pt["vx"]
                pt["y"] += pt["vy"]
                if pt["life"] > 0:
                    alive.append(pt)
            self._particles = alive
        # Бездонная: частицы летят к счётчику + нарастание свечения
        if hasattr(self, '_abyss_particles') and self._abyss_particles:
            alive = []
            any_active = False
            for ap in self._abyss_particles:
                if ap["delay"] > 0:
                    ap["delay"] -= 1
                    alive.append(ap)
                    continue
                if not ap["alive"]:
                    continue
                any_active = True
                dx = ap["tx"] - ap["x"]
                dy = ap["ty"] - ap["y"]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 15:
                    ap["alive"] = False
                    continue
                spd = ap["speed"]
                ap["x"] += dx / dist * spd
                ap["y"] += dy / dist * spd
                ap["speed"] *= 1.01  # ускоряются при приближении
                alive.append(ap)
            self._abyss_particles = alive
            # Свечение счётчика: нарастает до 200% пока частицы летят
            if any_active:
                self._abyss_glow_boost = min(2.0, getattr(self, '_abyss_glow_boost', 0) + 0.01)
            else:
                self._abyss_glow_boost = max(0, getattr(self, '_abyss_glow_boost', 0) - 0.012)
            # Обновляем свечение счётчика (DropShadow, не фон)
            boost = self._abyss_glow_boost
            if boost > 0.01:
                for w_obj in QApplication.topLevelWidgets():
                    if hasattr(w_obj, 'counter_label'):
                        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
                        cg = QGraphicsDropShadowEffect()
                        cg.setColor(QColor(255, 255, 255, min(255, int(120 + 135 * boost))))
                        cg.setBlurRadius(int(45 + 135 * boost))  # 45 → 315 при макс
                        cg.setOffset(0, 0)
                        w_obj.counter_label.setGraphicsEffect(cg)
                        break
        # Современная: обновление пузырей + дельфин
        if self._overlay_bubbles:
            alive = []
            for b in self._overlay_bubbles:
                b["age"] += 1
                b["x"] += b["vx"] + math.sin(b["phase"]) * 1.5
                b["y"] += b["vy"]
                b["vy"] *= 0.995
                b["phase"] += b["sway_speed"]
                remaining = 1.0 - b["age"] / b["lifetime"]
                b["alpha"] = max(0, int(200 * remaining))
                if b["age"] < b["lifetime"]:
                    alive.append(b)
            self._overlay_bubbles = alive
        if self._dolphins:
            alive_d = []
            sh = self.height() or 1080
            for d in self._dolphins:
                d["age"] += 1
                if d["age"] <= 0:
                    alive_d.append(d)
                    continue
                phase = d.get("phase", "rise")
                if phase == "rise":
                    d["y"] += d["vy"]
                    d["vy"] += 0.20
                    d["rotation"] += d["rot_speed"]
                    if d["vy"] >= 0:  # достиг вершины
                        d["phase"] = "hang"
                        d["hanging"] = 0
                        d["vy"] = 0
                elif phase == "hang":
                    d["hanging"] += 1
                    # Лёгкое покачивание при зависании
                    d["y"] += math.sin(d["hanging"] * 0.15) * 0.5
                    d["rotation"] += d["rot_speed"] * 0.2
                    if d["hanging"] >= d.get("hang_time", 30):
                        d["phase"] = "fall"
                elif phase == "fall":
                    d["y"] += d["vy"]
                    d["vy"] += 0.35  # ускоренное падение
                    d["rotation"] += d["rot_speed"] * 1.5
                if d["y"] <= sh + 300:
                    alive_d.append(d)
            self._dolphins = alive_d
        # Обновляем кадр GIF-анимации
        if self._movie and self._movie.state() == QMovie.MovieState.Running:
            pm = self._movie.currentPixmap()
            if not pm.isNull():
                self._mpm = pm
        self.update()

    def _done(self):
        self._p.clear(); self._mpm = None
        if self._movie: self._movie.stop(); self._movie = None
        # Если есть монеты — начинаем плавное угасание, не скрываем сразу
        if self._gold_coins:
            for coin in self._gold_coins:
                coin.start_fade()
            # Таймер продолжает работать пока монеты угасают
            QTimer.singleShot(3000, self._final_hide)
        else:
            self._at.stop()
            self.hide()

    def _final_hide(self):
        """Окончательное скрытие после угасания монет."""
        self._at.stop(); self._gold_coins.clear()
        self.hide()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self._sh); w, h = self.width(), self.height()
        fi = self._fire
        fc = self._fire_core; fm = self._fire_mid; ft = self._fire_tip
        if fi > 0.03:
            fh = int(200 * fi); a = int(230 * fi)
            g = QLinearGradient(0,h,0,h-fh)
            g.setColorAt(0, QColor(fc[0],fc[1],fc[2],a)); g.setColorAt(0.2, QColor(fm[0],fm[1],fm[2],int(a*0.8)))
            g.setColorAt(0.5, QColor(ft[0],ft[1],ft[2],int(a*0.4))); g.setColorAt(1, QColor(0,0,0,0))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(g); p.drawRect(0,h-fh,w,fh)
            fh2 = int(fh * 0.6)
            g2 = QLinearGradient(0,h,0,h-fh2)
            g2.setColorAt(0, QColor(ft[0],ft[1],ft[2],int(a*0.7))); g2.setColorAt(0.5, QColor(fc[0],fc[1],fc[2],int(a*0.3)))
            g2.setColorAt(1, QColor(0,0,0,0)); p.setBrush(g2); p.drawRect(0,h-fh2,w,fh2)
            for _ in range(int(25*fi)):
                fx, fy = random.randint(0,w), h-safe_randint(10,fh+40)
                fs = safe_randint(4,14); fa = max(61,int(200*fi))
                ec = random.choice(self._ember_colors)
                if self._theme_id == "retro":
                    f2 = QFont("Consolas", max(10, fs * 3)); f2.setBold(True)
                    p.setFont(f2); p.setPen(QColor(0,255,0,safe_randint(60,fa)))
                    p.drawText(fx, fy, random.choice("01"))
                else:
                    p.setBrush(QColor(ec[0],ec[1],ec[2],safe_randint(60,fa)))
                    p.drawEllipse(fx,fy,fs,fs)
        if self._lv >= 1 and fi > 0.1:
            th = int(80*fi); a = int(150*fi)
            gt = QLinearGradient(0,0,0,th)
            gt.setColorAt(0, QColor(fc[0],fc[1],fc[2],a)); gt.setColorAt(1, QColor(0,0,0,0))
            p.setBrush(gt); p.drawRect(0,0,w,th)
        if self._lv >= 2 and fi > 0.1:
            sw_ = int(60*fi); a = int(160*fi)
            for sx in [0, w-sw_]:
                d = 1 if sx==0 else -1
                gs = QLinearGradient(sx,0,sx+sw_*d,0)
                gs.setColorAt(0, QColor(fc[0],fc[1],fc[2],a)); gs.setColorAt(1, QColor(0,0,0,0))
                p.setBrush(gs); p.drawRect(sx,0,sw_,h)
        va = int(40+40*fi)
        vg = QRadialGradient(w/2,h/2,max(w,h)*0.7)
        vc = self._fire_core
        vg.setColorAt(0,QColor(0,0,0,0)); vg.setColorAt(0.6,QColor(0,0,0,0)); vg.setColorAt(1,QColor(vc[0]//2,vc[1]//2,vc[2]//2,va))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(vg); p.drawRect(0,0,w,h)
        if self._theme_id == "retro":
            # Ретро: вместо искорок — 0 и 1
            for pa in self._p:
                a = pa.alpha
                if a <= 0:
                    continue
                if not hasattr(pa, '_char'):
                    pa._char = random.choice("01")
                f = QFont("Consolas", max(10, pa.size * 3))
                f.setBold(True)
                p.setFont(f)
                p.setPen(QColor(0, 255, 0, a))
                p.drawText(int(pa.x), int(pa.y), pa._char)
        else:
            from PyQt6.QtGui import QPainterPath
            from PyQt6.QtCore import QPointF
            for pa in self._p:
                a = pa.alpha
                if a <= 0: continue
                c = QColor(pa.color); c.setAlpha(a)
                sides = getattr(pa, '_shape', 0)
                sz = pa.size
                cx_p, cy_p = pa.x + sz / 2, pa.y + sz / 2
                if sides >= 3:
                    # Полигон: треугольник/пятиугольник/шестиугольник
                    rot = getattr(pa, '_rot', 0)
                    path = QPainterPath()
                    for k in range(sides):
                        angle = 2 * math.pi / sides * k + rot
                        px = cx_p + sz * 0.6 * math.cos(angle)
                        py = cy_p + sz * 0.6 * math.sin(angle)
                        if k == 0: path.moveTo(px, py)
                        else: path.lineTo(px, py)
                    path.closeSubpath()
                    # Свечение
                    sg = QRadialGradient(cx_p, cy_p, sz * 1.2)
                    sg.setColorAt(0, QColor(c.red(), c.green(), c.blue(), a // 2))
                    sg.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))
                    p.setPen(Qt.PenStyle.NoPen); p.setBrush(sg)
                    p.drawEllipse(QPointF(cx_p, cy_p), sz * 1.2, sz * 1.2)
                    p.setBrush(c); p.drawPath(path)
                else:
                    p.setPen(Qt.PenStyle.NoPen); p.setBrush(c)
                    p.drawEllipse(int(pa.x),int(pa.y),sz,sz)
        # Бездонная: тёмные→белые частицы летящие к счётчику
        for ap in getattr(self, '_abyss_particles', []):
            if ap["delay"] > 0 or not ap["alive"]:
                continue
            b = ap["brightness"]
            al = ap["alpha"]
            sz = ap["size"]
            from PyQt6.QtCore import QPointF as _QP
            # Свечение
            sg = QRadialGradient(ap["x"], ap["y"], sz * 2)
            sg.setColorAt(0, QColor(b, b, b, al))
            sg.setColorAt(0.5, QColor(b, b, b, al // 3))
            sg.setColorAt(1, QColor(b, b, b, 0))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(sg)
            p.drawEllipse(_QP(ap["x"], ap["y"]), sz * 2, sz * 2)
            # Ядро
            p.setBrush(QColor(b, b, b, al))
            p.drawEllipse(_QP(ap["x"], ap["y"]), sz * 0.5, sz * 0.5)
        # Золотые монеты
        for coin in self._gold_coins:
            ca = coin.alpha
            # Эффект вращения через сжатие по X
            squeeze = abs(math.cos(coin.rotation))
            cw = max(1, int(coin.size * squeeze))
            ch = coin.size
            # Ядро монеты
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(coin.bright, int(coin.bright * 0.75), 0, ca))
            p.drawEllipse(int(coin.x) - cw // 2, int(coin.y) - ch // 2, cw, ch)
            # Блик
            if squeeze > 0.3:
                p.setBrush(QColor(255, 255, 200, ca // 2))
                bs = max(1, cw // 3)
                p.drawEllipse(int(coin.x) - bs // 2, int(coin.y) - bs // 2, bs, bs)
        # Лазеры через весь экран (злодейская — багровые, заряженная — бело-голубые)
        from PyQt6.QtCore import QPointF
        is_charged = self._theme_id == "charged"
        for las in self._overlay_lasers:
            al = las["alpha"]
            if al <= 0:
                continue
            angle_rad = math.radians(las["angle"])
            half_len = las["length"] / 2
            dx = math.cos(angle_rad) * half_len
            dy = math.sin(angle_rad) * half_len
            x1, y1 = las["x"] - dx, las["y"] - dy
            x2, y2 = las["x"] + dx, las["y"] + dy
            if is_charged:
                # Бело-голубые молнии
                p.setPen(QPen(QColor(120, 160, 255, al // 3), 50))
                p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                p.setPen(QPen(QColor(180, 210, 255, al), 16))
                p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                p.setPen(QPen(QColor(255, 255, 255, al), 6))
            else:
                # Багровые лазеры
                p.setPen(QPen(QColor(220, 40, 50, al // 3), 54))
                p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                p.setPen(QPen(QColor(184, 28, 40, al), 18))
                p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                p.setPen(QPen(QColor(255, 120, 120, al // 2), 9))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        # Закат: звёздочки-искорки разлетающиеся из центра
        from PyQt6.QtCore import QPointF
        star_colors = [(253,192,5), (246,131,24), (255,240,120), (255,200,80)]
        for st in self._overlay_stars:
            al = st["alpha"]
            if al <= 0:
                continue
            sz = st["size"]
            col = star_colors[st["color_idx"] % len(star_colors)]
            cx, cy = st["x"], st["y"]
            # Четырёхконечная звезда
            p.setPen(Qt.PenStyle.NoPen)
            # Свечение
            sg = QRadialGradient(cx, cy, sz * 1.5)
            sg.setColorAt(0, QColor(col[0], col[1], col[2], al // 2))
            sg.setColorAt(1, QColor(col[0], col[1], col[2], 0))
            p.setBrush(sg)
            p.drawEllipse(QPointF(cx, cy), sz * 1.5, sz * 1.5)
            # Лучи звезды (крест)
            half = sz * 0.7
            p.setPen(QPen(QColor(col[0], col[1], col[2], al), 2))
            p.drawLine(QPointF(cx - half, cy), QPointF(cx + half, cy))
            p.drawLine(QPointF(cx, cy - half), QPointF(cx, cy + half))
            # Диагональные лучи (тоньше)
            d = half * 0.5
            p.setPen(QPen(QColor(col[0], col[1], col[2], al // 2), 1))
            p.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
            p.drawLine(QPointF(cx - d, cy + d), QPointF(cx + d, cy - d))
            # Ядро
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 220, al))
            core = max(2, sz // 4)
            p.drawEllipse(QPointF(cx, cy), core, core)
        # Заряженная: искры летящие из окна наружу
        for sp in getattr(self, '_charged_sparks_out', []):
            al = sp["alpha"]
            if al <= 0:
                continue
            col = sp["color"]
            sz = sp["size"]
            p.setPen(Qt.PenStyle.NoPen)
            # Свечение
            sg = QRadialGradient(sp["x"], sp["y"], sz * 2)
            sg.setColorAt(0, QColor(col[0], col[1], col[2], al))
            sg.setColorAt(1, QColor(col[0], col[1], col[2], 0))
            p.setBrush(sg)
            p.drawEllipse(QPointF(sp["x"], sp["y"]), sz * 2, sz * 2)
            # Ядро
            p.setBrush(QColor(255, 255, 255, al))
            p.drawEllipse(QPointF(sp["x"], sp["y"]), sz * 0.5, sz * 0.5)
        # Тематические частицы детекции
        for pt in self._particles:
            if pt["life"] <= 0:
                continue
            if pt.get("shape") == "fog":
                alpha = pt.get("alpha", 40) * (pt["life"] / pt["max_life"])
                p.setBrush(QColor(pt["color"][0], pt["color"][1], pt["color"][2], int(alpha)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(int(pt["x"]) - pt["size"], int(pt["y"]) - pt["size"], pt["size"] * 2, pt["size"] * 2)
            else:
                alpha = int(255 * (pt["life"] / pt["max_life"]))
                col = pt["color"]
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(col[0], col[1], col[2], alpha))
                sz = pt["size"]
                p.drawEllipse(int(pt["x"]) - sz // 2, int(pt["y"]) - sz // 2, sz, sz)
        # Современная: пузыри + дельфин
        for b in getattr(self, '_overlay_bubbles', []):
            al = b["alpha"]
            if al <= 0:
                continue
            sz = b["size"]
            bx, by = b["x"], b["y"]
            # Свечение пузырька
            sg = QRadialGradient(bx, by, sz * 1.3)
            sg.setColorAt(0, QColor(180, 220, 255, al // 3))
            sg.setColorAt(1, QColor(180, 220, 255, 0))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(sg)
            p.drawEllipse(QPointF(bx, by), sz * 1.3, sz * 1.3)
            # Контур
            p.setPen(QPen(QColor(200, 235, 255, al), 1.5))
            p.setBrush(QColor(160, 210, 250, al // 5))
            p.drawEllipse(QPointF(bx, by), sz, sz)
            # Блик
            blik = sz * 0.25
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, int(al * 0.7)))
            p.drawEllipse(QPointF(bx - sz * 0.3, by - sz * 0.3), blik, blik)
        for dolph in getattr(self, '_dolphins', []):
            if dolph["age"] <= 0:
                continue  # ещё ждёт задержку
            pm = dolph.get("pm")
            if not pm:
                continue
            p.save()
            cx = dolph["x"] + pm.width() / 2
            cy = dolph["y"] + pm.height() / 2
            p.translate(cx, cy)
            p.rotate(dolph["rotation"])
            p.setOpacity(1.0)
            p.drawPixmap(int(-pm.width() / 2), int(-pm.height() / 2), pm)
            p.restore()
            p.setOpacity(1.0)
        if self._mpm and not self._mpm.isNull():
            p.setOpacity(min(1.0,self._ma/200.0+0.3)); p.drawPixmap(self._mr.topLeft(),self._mpm); p.setOpacity(1.0)
        if self._ma > 5 and self._msg:
            tc = self._text_color
            fsz = 32+self._lv*10; font = QFont("Arial",fsz,QFont.Weight.Black); p.setFont(font)
            ty = h//2+160+(90 if self._mpm else 0)
            for dx,dy in [(-2,-2),(2,-2),(-2,2),(2,2),(0,-3),(0,3)]:
                p.setPen(QColor(fm[0],fm[1],fm[2],self._ma//3))
                p.drawText(QRect(dx,ty+dy,w,120),Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop,self._msg)
            p.setPen(QColor(0,0,0,self._ma))
            p.drawText(QRect(3,ty+3,w,120),Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop,self._msg)
            p.setPen(QColor(tc[0],tc[1],tc[2],self._ma))
            p.drawText(QRect(0,ty,w,120),Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop,self._msg)
        if self._gl > 0:
            for _ in range(4+self._lv*3):
                gy = random.randint(0,h); gh = safe_randint(1,5); ga = safe_randint(25,90)
                gc = random.choice([QColor(255,0,0,ga),QColor(0,255,255,ga),QColor(255,255,0,ga)])
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(gc)
                off = safe_randint(-25,25)*(self._lv+1)
                p.drawRect(max(0,off),gy,w,gh)
        p.end()


class AchievementPopup(QWidget):
    def __init__(self, ach, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint
                            |Qt.WindowType.Tool|Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._a = ach; self._al = 0; self._fr = 0
        self.setFixedSize(420,100)
        scr = QApplication.primaryScreen()
        if scr: self.move(scr.geometry().width()-440, 20)
        self._t = QTimer(self); self._t.timeout.connect(self._tick)

    def show_popup(self): self.show(); self.raise_(); self._t.start(16)

    def _tick(self):
        self._fr += 1
        if self._fr < 20: self._al = min(255, self._al+15)
        elif self._fr > 180:
            self._al = max(0, self._al-8)
            if self._al <= 0: self._t.stop(); self.hide(); self.deleteLater(); return
        self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        a = self._al
        p.setPen(QPen(QColor(255,40,40,a),2)); p.setBrush(QColor(20,0,0,int(220*a/255)))
        p.drawRoundedRect(2,2,self.width()-4,self.height()-4,10,10)
        p.setPen(QColor(255,255,255,a)); p.setFont(QFont("Arial",36))
        p.drawText(QRect(10,10,80,80),Qt.AlignmentFlag.AlignCenter,self._a.get("icon","🏆"))
        p.setPen(QColor(255,200,50,a)); p.setFont(QFont("Arial",14,QFont.Weight.Bold))
        p.drawText(QRect(90,12,320,30),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,f"🏆 {self._a['name']}")
        p.setPen(QColor(200,200,200,a)); p.setFont(QFont("Arial",11))
        p.drawText(QRect(90,45,320,40),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop,self._a.get("desc",""))
        p.end()


class EmojiExplosion(QWidget):
    """Полноэкранный оверлей со взрывами эмодзи перцев и огня."""
    EMOJIS = ["🌶", "🔥", "💥", "🌶", "🔥", "🌶", "🔥", "💀", "🌶", "🔥"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._particles = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._finish)

    def boom(self, cx=None, cy=None, count=18):
        """Взрыв эмодзи из точки (cx, cy). Если не задано — из центра экрана."""
        scr = QApplication.primaryScreen()
        if scr:
            self.setGeometry(scr.geometry())
        sw, sh = self.width() or 1920, self.height() or 1080
        if cx is None:
            cx = sw // 2
        if cy is None:
            cy = sh // 2
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(4, 16)
            self._particles.append({
                "x": float(cx), "y": float(cy),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - random.uniform(2, 6),
                "emoji": random.choice(self.EMOJIS),
                "size": random.randint(18, 38),
                "rotation": random.uniform(-30, 30),
                "rot_speed": random.uniform(-8, 8),
                "alpha": 255,
                "age": 0,
                "lifetime": random.randint(40, 80),
            })
        if not self._timer.isActive():
            self._timer.start(16)
        self._hide_timer.stop()
        self._hide_timer.start(2500)
        self.show()
        self.raise_()

    def _tick(self):
        alive = []
        for pa in self._particles:
            pa["age"] += 1
            pa["x"] += pa["vx"]
            pa["y"] += pa["vy"]
            pa["vy"] += 0.35  # гравитация
            pa["vx"] *= 0.98
            pa["rotation"] += pa["rot_speed"]
            remaining = 1.0 - pa["age"] / pa["lifetime"]
            pa["alpha"] = max(0, int(255 * remaining))
            if pa["age"] < pa["lifetime"]:
                alive.append(pa)
        self._particles = alive
        if not self._particles:
            self._timer.stop()
            self.hide()
            return
        self.update()

    def _finish(self):
        # Начинаем быстрое затухание оставшихся
        for pa in self._particles:
            pa["lifetime"] = pa["age"] + 10

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for pa in self._particles:
            al = pa["alpha"]
            if al <= 0:
                continue
            p.save()
            p.translate(pa["x"], pa["y"])
            p.rotate(pa["rotation"])
            p.setOpacity(al / 255.0)
            f = QFont("Segoe UI Emoji", pa["size"])
            p.setFont(f)
            p.setPen(QColor(255, 255, 255, al))
            p.drawText(-pa["size"] // 2, pa["size"] // 2, pa["emoji"])
            p.restore()
        p.end()


class ConfettiExplosion(QWidget):
    """Полноэкранный оверлей с конфетти (цветные кусочки)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._pieces = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._finish)

    def burst(self, cx=None, cy=None, count=140):
        scr = QApplication.primaryScreen()
        if scr:
            self.setGeometry(scr.geometry())

        sw = self.width() or 1920
        sh = self.height() or 1080
        if cx is None:
            cx = sw // 2
        if cy is None:
            cy = sh // 2

        import math

        # Небольшая палитра под "Inferno" стиль
        palette = [
            QColor(255, 80, 60),   # красный
            QColor(255, 200, 60),  # золото
            QColor(90, 200, 255),   # циан
            QColor(200, 120, 255),  # фиолет
            QColor(120, 255, 160),  # зелёный
        ]

        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(4, 13)
            w = random.randint(6, 14)
            h = random.randint(3, 10)
            lifetime = random.randint(45, 85)
            self._pieces.append(
                {
                    "x": float(cx),
                    "y": float(cy),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed - random.uniform(1, 6),
                    "w": w,
                    "h": h,
                    "color": random.choice(palette),
                    "alpha": 255,
                    "age": 0,
                    "lifetime": lifetime,
                    "rot": random.uniform(-30, 30),
                    "rot_speed": random.uniform(-8, 8),
                }
            )

        if not self._timer.isActive():
            self._timer.start(16)
        self._hide_timer.stop()
        self._hide_timer.start(2400)
        self.show()
        self.raise_()

    def _tick(self):
        alive = []
        for pc in self._pieces:
            pc["age"] += 1
            pc["x"] += pc["vx"]
            pc["y"] += pc["vy"]
            pc["vy"] += 0.35  # гравитация
            pc["rot"] += pc["rot_speed"]
            remaining = 1.0 - pc["age"] / pc["lifetime"]
            pc["alpha"] = max(0, int(255 * remaining))
            if pc["age"] < pc["lifetime"]:
                alive.append(pc)
        self._pieces = alive

        if not self._pieces:
            self._timer.stop()
            self.hide()
            return
        self.update()

    def _finish(self):
        for pc in self._pieces:
            pc["lifetime"] = pc["age"] + 10

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for pc in self._pieces:
            a = pc["alpha"]
            if a <= 0:
                continue
            col = pc["color"]
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(col.red(), col.green(), col.blue(), a))
            p.save()
            p.translate(pc["x"], pc["y"])
            p.rotate(pc["rot"])
            p.drawRect(int(-pc["w"] // 2), int(-pc["h"] // 2), pc["w"], pc["h"])
            p.restore()
        p.end()
