"""
Inferno Grade Tracker — UI (v7 COMPACT 4K + Auth + Themes + Punishments)
──────────────────────────────────────────────────────────────────────────
• «Файлы {nickname}» вместо «Ачивки», замазанные описания
• Вкладка «Огни» — темы огня/цвета, часть скрыта/открывается
• Микро-ивенты наказаний за чрезмерное помилование
• 480×720, компакт, High-DPI-ready
"""
import math
import random
import time
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QGridLayout, QScrollArea, QFrame,
    QProgressBar, QCheckBox, QApplication, QTableWidget,
    QTableWidgetItem, QHeaderView, QSlider, QSizePolicy,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QSpacerItem,
    QLineEdit, QToolTip, QMessageBox,
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve, QRect, QRectF, QPoint, QPointF,
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPalette, QLinearGradient,
    QRadialGradient, QPen, QBrush, QPixmap, QPolygonF, QTransform,
)
from modules.config import (
    get_rank, get_rank_progress, MOTIVATIONAL_QUOTES,
    ACHIEVEMENTS, CATEGORY_NAMES, DEFAULT_CONFIG,
)
from modules.themes import (
    THEMES, DEFAULT_THEME_ID, CHEATER_THEME_ID, get_theme_by_id, get_unlocked_themes,
    get_themes_by_category, THEME_CATEGORIES,
)
from modules.punishments import PunishmentEngine
from modules.shop_manager import ShopManager
from modules.daily_quests import DailyQuestManager

# ═══════════════════════════════════════════════════════════════
#  Константы размеров
# ═══════════════════════════════════════════════════════════════
WIN_W, WIN_H = 480, 720
WIN_EXP_H = 900
COUNTER_FONT_PT = 150
TOTAL_FONT_PT = 26
STREAK_FONT_PT = 22
RANK_BAR_H = 28
FONT_FAMILY = "'Segoe UI', 'Inter', 'Roboto', 'Arial', sans-serif"
FONT_FAMILY_DISPLAY = "'Impact', 'Arial Black', 'Segoe UI Black', sans-serif"

# Символ замазки для описаний ачивок
CENSOR_CHAR = "\u2588"  # █ — полный блок


def censor_text(text: str, ratio: float = 0.35) -> str:
    """Замазывает ~ratio часть текста блоками █."""
    words = text.split()
    result = []
    for w in words:
        if random.random() < ratio and len(w) > 2:
            result.append(CENSOR_CHAR * len(w))
        else:
            result.append(w)
    return " ".join(result)


# ═══════════════════════════════════════════════════════════════
#  Animated fire border
# ═══════════════════════════════════════════════════════════════
class CursorSparkOverlay(QWidget):
    """Fullscreen прозрачный overlay для искр курсора (заряженная тема)."""
    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._particles = []
        self._active = False

    def set_active(self, active):
        self._active = active
        if active:
            scr = QApplication.primaryScreen()
            if scr:
                self.setGeometry(scr.geometry())
            self.show()
            self.raise_()
        else:
            self._particles.clear()
            self.hide()

    def spawn_at(self, gx, gy, count, in_window):
        """Спавн частиц в глобальных координатах."""
        for _ in range(count):
            lifetime = random.randint(5, 11)  # 0.4-0.9с при 80мс тике
            self._particles.append({
                "x": gx + random.uniform(-6, 6),
                "y": gy + random.uniform(-6, 6),
                "vx": random.uniform(-0.8, 0.8),
                "vy": random.uniform(-1.5, 0.3),
                "size": random.uniform(2.0, 5.0),
                "alpha": random.randint(180, 255),
                "alpha_base": 0,
                "age": 0,
                "lifetime": lifetime,
                "color": random.choice([
                    (160, 200, 255), (200, 220, 255), (255, 255, 180),
                    (180, 210, 255), (255, 255, 255), (120, 180, 255),
                ]),
            })

    def tick(self):
        alive = []
        for sp in self._particles:
            if sp["alpha_base"] == 0:
                sp["alpha_base"] = sp["alpha"]
            sp["age"] += 1
            sp["x"] += sp["vx"]
            sp["y"] += sp["vy"]
            sp["size"] = max(0.5, sp["size"] - 0.15)
            remaining = max(0.0, 1.0 - sp["age"] / sp["lifetime"])
            sp["alpha"] = int(sp["alpha_base"] * remaining)
            if sp["age"] < sp["lifetime"]:
                alive.append(sp)
        self._particles = alive
        if self._active:
            self.raise_()  # всегда поверх основного окна
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        for sp in self._particles:
            al = sp["alpha"]
            if al <= 0:
                continue
            col = sp["color"]
            sz = sp["size"]
            glow_r = sz * 2.5
            sg = QRadialGradient(sp["x"], sp["y"], glow_r)
            sg.setColorAt(0.0, QColor(col[0], col[1], col[2], al))
            sg.setColorAt(0.4, QColor(col[0], col[1], col[2], al // 2))
            sg.setColorAt(1.0, QColor(col[0], col[1], col[2], 0))
            p.setBrush(QBrush(sg))
            p.drawEllipse(QPointF(sp["x"], sp["y"]), glow_r, glow_r)
            p.setBrush(QColor(255, 255, 255, min(255, al + 40)))
            core = max(1.0, sz * 0.4)
            p.drawEllipse(QPointF(sp["x"], sp["y"]), core, core)
        p.end()


class BottomlessStarOverlay(QWidget):
    """Fullscreen overlay для звезды бездонной темы (dm1/dm2).
    Звезда кликабельна — при клике схлопывается с фейерверком."""
    star_clicked = pyqtSignal()  # сигнал при клике на звезду

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self._active = False
        self._star_pixmap = None  # QPixmap dm1 или dm2
        self._star_type = 1       # 1=dm1, 2=dm2
        # Позиция и движение
        self._sx = 0.0; self._sy = 0.0  # текущая позиция (глобальная)
        self._vx = 0.0; self._vy = 0.0  # скорость
        self._target_x = 0.0; self._target_y = 0.0  # центр монитора
        self._phase = 0  # 0=падение, 1=замедление, 2=подъём, 3=дрожание, 4=схлоп, 5=фейерверк
        self._timer_tick = 0
        self._star_scale = 1.0
        self._tremble = 0.0
        # Тёмные частицы притяжения
        self._dark_particles = []
        # Фейерверк
        self._fireworks = []
        self._fw_phase = 0  # время после фейерверка

    def launch(self, gx, gy, star_type=1):
        """Запуск звезды из позиции (gx, gy)."""
        import os
        self._star_type = star_type
        fname = "dm1.png" if star_type == 1 else "dm2.png"
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "45")
        path = os.path.join(base, fname)
        if not os.path.exists(path):
            base2 = r"C:\Users\bibob9000\Desktop\papka\45"
            path = os.path.join(base2, fname)
        self._star_pixmap = QPixmap(path)
        self._sx = float(gx) + random.uniform(-30, 30)
        self._sy = float(gy)
        self._vx = random.uniform(-2, 2)
        self._vy = random.uniform(2, 5)  # падает вниз
        scr = QApplication.primaryScreen()
        if scr:
            sg = scr.geometry()
            self._target_x = sg.x() + sg.width() / 2.0
            self._target_y = sg.y() + sg.height() / 2.0
            self.setGeometry(sg)
        self._phase = 0
        self._timer_tick = 0
        self._star_scale = 1.0
        self._tremble = 0.0
        self._dark_particles = []
        self._fireworks = []
        self._fw_phase = 0
        self._active = True
        self.show()
        self.raise_()

    def tick(self):
        if not self._active:
            return
        self._timer_tick += 1
        if self._phase == 0:
            # Падение + сразу коррекция к центру монитора
            # Начинаем с гравитации, но уже подмешиваем вектор к цели
            self._sx += self._vx
            self._sy += self._vy
            t = min(1.0, self._timer_tick / 10.0)  # 0→1 за 10 тиков
            dx = self._target_x - self._sx
            dy = self._target_y - self._sy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 1:
                # Плавно подмешиваем целевое направление
                corr = t * 0.15
                self._vx += dx / dist * corr
                self._vy += dy / dist * corr
            self._vy += 0.15 * (1.0 - t)  # гравитация слабеет
            # Через 8 тиков переходим к прямому полёту
            if self._timer_tick > 8:
                self._phase = 2
                self._timer_tick = 0
        elif self._phase == 2:
            # Полёт к центру монитора — быстро
            dx = self._target_x - self._sx
            dy = self._target_y - self._sy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 3:
                speed = min(18.0, dist * 0.09)  # быстрее: ×2.25
                self._sx += dx / dist * speed
                self._sy += dy / dist * speed
            else:
                self._sx = self._target_x
                self._sy = self._target_y
                self._phase = 3
                self._timer_tick = 0
        elif self._phase == 3:
            # Дрожание в центре, притягивает частицы
            self._tremble = random.uniform(-3, 3)
            # Спавн тёмных частиц с краёв
            if self._timer_tick % 2 == 0:
                scr = QApplication.primaryScreen()
                if scr:
                    sg = scr.geometry()
                    side = random.randint(0, 3)
                    if side == 0: px, py = random.uniform(sg.x(), sg.x()+sg.width()), float(sg.y())
                    elif side == 1: px, py = random.uniform(sg.x(), sg.x()+sg.width()), float(sg.y()+sg.height())
                    elif side == 2: px, py = float(sg.x()), random.uniform(sg.y(), sg.y()+sg.height())
                    else: px, py = float(sg.x()+sg.width()), random.uniform(sg.y(), sg.y()+sg.height())
                    self._dark_particles.append({
                        "x": px, "y": py, "alpha": random.randint(100, 200),
                        "size": random.uniform(2, 5),
                    })
            # Обновляем тёмные частицы — летят к звезде
            alive = []
            for dp in self._dark_particles:
                dx = self._sx - dp["x"]
                dy = self._sy - dp["y"]
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 8:
                    spd = min(12.0, dist * 0.06)
                    dp["x"] += dx / dist * spd
                    dp["y"] += dy / dist * spd
                    alive.append(dp)
                # Частица достигла звезды — поглощена
            self._dark_particles = alive
        elif self._phase == 4:
            # Схлопывание: рост → сжатие
            self._timer_tick += 1
            total = 20  # ~1.6с
            if self._timer_tick < 5:
                self._star_scale = 1.0 + 0.2 * (self._timer_tick / 5)  # рост на 20%
            else:
                prog = (self._timer_tick - 5) / (total - 5)
                self._star_scale = max(0.0, 1.2 * (1.0 - prog ** 0.5))
            if self._timer_tick >= total:
                # Фейерверк!
                self._phase = 5
                self._timer_tick = 0
                col = (120, 40, 180) if self._star_type == 1 else (200, 30, 30)
                for _ in range(60):
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(3, 14)
                    self._fireworks.append({
                        "x": self._sx, "y": self._sy,
                        "vx": math.cos(angle) * speed,
                        "vy": math.sin(angle) * speed,
                        "alpha": 255, "size": random.uniform(3, 7),
                        "color": (col[0] + random.randint(-30, 30),
                                  col[1] + random.randint(-20, 20),
                                  col[2] + random.randint(-30, 30)),
                    })
        elif self._phase == 5:
            # Фейерверк рассеивается
            alive = []
            for fw in self._fireworks:
                fw["x"] += fw["vx"]
                fw["y"] += fw["vy"]
                fw["vy"] += 0.1
                fw["vx"] *= 0.97
                fw["alpha"] -= 6
                if fw["alpha"] > 0:
                    alive.append(fw)
            self._fireworks = alive
            if not alive:
                self._active = False
                self.hide()
                return
        self.update()

    def mousePressEvent(self, e):
        if self._phase == 3 and e.button() == Qt.MouseButton.LeftButton:
            # Проверяем клик на звезде
            local_x, local_y = e.position().x(), e.position().y()
            dx = local_x - self._sx
            dy = local_y - self._sy
            if dx * dx + dy * dy < 60 * 60:  # радиус клика 60px
                self._phase = 4
                self._timer_tick = 0
                self._dark_particles.clear()
                # Сразу при клике запускаем смену цвета (не ждём фейерверк)
                self.star_clicked.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._phase <= 4 and self._star_pixmap and not self._star_pixmap.isNull():
            sc = self._star_scale
            if sc > 0.01:
                pm = self._star_pixmap
                sw = int(pm.width() * sc)
                sh = int(pm.height() * sc)
                if sw > 0 and sh > 0:
                    scaled = pm.scaled(sw, sh, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                    tx = self._tremble if self._phase == 3 else 0
                    ty = random.uniform(-2, 2) if self._phase == 3 else 0
                    p.drawPixmap(int(self._sx - sw/2 + tx), int(self._sy - sh/2 + ty), scaled)
        # Тёмные частицы
        p.setPen(Qt.PenStyle.NoPen)
        for dp in self._dark_particles:
            al = dp["alpha"]
            sz = dp["size"]
            grad = QRadialGradient(dp["x"], dp["y"], sz * 2)
            grad.setColorAt(0, QColor(20, 0, 0, al))
            grad.setColorAt(0.5, QColor(10, 0, 0, al // 2))
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(grad))
            p.drawEllipse(QPointF(dp["x"], dp["y"]), sz * 2, sz * 2)
        # Фейерверк
        for fw in self._fireworks:
            al = max(0, fw["alpha"])
            sz = fw["size"]
            c = fw["color"]
            grad = QRadialGradient(fw["x"], fw["y"], sz * 2)
            grad.setColorAt(0, QColor(min(255, c[0]), min(255, c[1]), min(255, c[2]), al))
            grad.setColorAt(0.5, QColor(min(255, c[0]), min(255, c[1]), min(255, c[2]), al // 2))
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(grad))
            p.drawEllipse(QPointF(fw["x"], fw["y"]), sz * 2, sz * 2)
            # Яркое ядро
            p.setBrush(QColor(255, 200, 200, al))
            p.drawEllipse(QPointF(fw["x"], fw["y"]), max(1, sz * 0.3), max(1, sz * 0.3))
        p.end()


class FireBorderWidget(QWidget):
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._phase = 0.0
        self._theme = theme or get_theme_by_id(DEFAULT_THEME_ID)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def set_theme(self, theme):
        self._theme = theme

    def _tick(self):
        self._phase += 0.08
        if self._phase > 6.2832:
            self._phase -= 6.2832
        self.update()

    def paintEvent(self, e):
        w, h = self.width(), self.height()
        if w < 10 or h < 10:
            return
        # Для octagon, sharp_corners и no_border тем — скрываем огненную рамку
        if self._theme.get("shape") in ("octagon", "hourglass", "circle") or self._theme.get("no_border") or self._theme.get("sharp_corners") or self._theme.get("edge_lightning"):
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        border_color = QColor(self._theme["colors"]["border"])
        embers = self._theme["colors"]["ember_colors"]
        for i in range(3):
            alpha = int(50 + 35 * math.sin(self._phase + i * 0.6))
            bc = QColor(border_color)
            bc.setAlpha(alpha)
            p.setPen(QPen(bc, max(1, 2 - i * 0.5)))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(i + 1, i + 1, w - 2 * (i + 1), h - 2 * (i + 1), 12 - i, 12 - i)
        for _ in range(4):
            side = random.randint(0, 3)
            if side == 0:
                px, py = random.randint(10, w - 10), random.randint(1, 4)
            elif side == 1:
                px, py = random.randint(10, w - 10), random.randint(h - 4, h - 1)
            elif side == 2:
                px, py = random.randint(1, 4), random.randint(10, h - 10)
            else:
                px, py = random.randint(w - 4, w - 1), random.randint(10, h - 10)
            ea = int(70 + 60 * math.sin(self._phase + random.random() * 6.28))
            p.setPen(Qt.PenStyle.NoPen)
            er, eg, eb = random.choice(embers)
            p.setBrush(QColor(er, eg, eb, ea))
            sz = random.uniform(1.5, 3.0)
            p.drawEllipse(int(px), int(py), int(sz), int(sz))
        p.end()


# ═══════════════════════════════════════════════════════════════
#  Combo Flash
# ═══════════════════════════════════════════════════════════════
class ComboFlashLabel(QLabel):
    def __init__(self, text, parent=None, duration_ms=2500, color="#ff2200"):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._color = color
        self.setStyleSheet(
            f"color: {color}; font-size: 48px; font-weight: bold; "
            f"background: transparent; font-family: {FONT_FAMILY_DISPLAY};"
        )
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(255, 80, 0, 200))
        glow.setBlurRadius(35)
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)
        self._opacity = 1.0
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._fade_step)
        QTimer.singleShot(max(100, duration_ms - 700), self._start_fade)
        QTimer.singleShot(duration_ms, self._finish)

    def _start_fade(self):
        self._fade_timer.start(30)

    def _fade_step(self):
        self._opacity = max(0.0, self._opacity - 0.07)
        if self._opacity <= 0:
            self._fade_timer.stop()
        a = int(self._opacity * 255)
        self.setStyleSheet(
            f"color: rgba(255,34,0,{a}); font-size: 48px; font-weight: bold; "
            f"background: transparent; font-family: {FONT_FAMILY_DISPLAY};"
        )

    def _finish(self):
        self._fade_timer.stop()
        self.hide()
        self.deleteLater()


# ═══════════════════════════════════════════════════════════════
#  Punishment Overlay — предупреждение с таймером
# ═══════════════════════════════════════════════════════════════
class PunishmentOverlay(QLabel):
    """Оверлей наказания поверх окна."""
    def __init__(self, title, desc, parent=None, timeout_sec=0):
        super().__init__(parent)
        self._timeout = timeout_sec
        self._remaining = timeout_sec
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self._base_text = f"{title}\n\n{desc}"
        self._update_text()
        self.setStyleSheet(
            f"color: #ff2020; font-size: 18px; font-weight: bold; "
            f"background: rgba(0,0,0,200); padding: 20px; "
            f"border: 3px solid #ff0000; border-radius: 10px; "
            f"font-family: {FONT_FAMILY_DISPLAY};"
        )
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(255, 0, 0, 150))
        glow.setBlurRadius(25); glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)
        if timeout_sec > 0:
            self._tick_timer = QTimer(self)
            self._tick_timer.timeout.connect(self._tick)
            self._tick_timer.start(1000)
        else:
            QTimer.singleShot(5000, self._finish)

    def _update_text(self):
        if self._remaining > 0:
            self.setText(f"{self._base_text}\n\n\u23f1 {self._remaining}с")
        else:
            self.setText(self._base_text)

    def _tick(self):
        self._remaining -= 1
        self._update_text()
        if self._remaining <= 0:
            self._tick_timer.stop()

    def _finish(self):
        self.hide()
        self.deleteLater()

    def dismiss(self):
        if hasattr(self, '_tick_timer'):
            self._tick_timer.stop()
        self.hide()
        self.deleteLater()


# ═══════════════════════════════════════════════════════════════
#  Окно магазина (отдельное)
# ═══════════════════════════════════════════════════════════════
class ShopWindow(QWidget):
    """Отдельное окно магазина в стиле Golden Emperor."""

    def __init__(self, panel):
        super().__init__(None)
        self._panel = panel
        self._drag_pos = None
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 650)
        # Декоративная анимация "монетного" фона
        self._coin_shimmer_phase = 0.0
        self._decoration_timer = QTimer(self)
        self._decoration_timer.timeout.connect(self._tick_decoration)
        self._decoration_timer.start(60)
        self._build_ui()

    def _tick_decoration(self):
        self._coin_shimmer_phase += 0.18
        if self._coin_shimmer_phase > 1000:
            self._coin_shimmer_phase = 0.0
        self.update()

    # ── Dragging ──
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and ev.position().y() < 40:
            self._drag_pos = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            ev.accept()

    def mouseMoveEvent(self, ev):
        if self._drag_pos and ev.buttons() & Qt.MouseButton.LeftButton:
            self.move(ev.globalPosition().toPoint() - self._drag_pos)
            ev.accept()

    def mouseReleaseEvent(self, ev):
        self._drag_pos = None

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Background gradient
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(25, 12, 0, 245))
        grad.setColorAt(0.5, QColor(15, 8, 0, 250))
        grad.setColorAt(1, QColor(10, 5, 0, 250))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#886611"), 2))
        p.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 12, 12)
        # Gold top accent line
        p.setPen(QPen(QColor("#ffcc00"), 1))
        p.drawLine(20, 40, self.width() - 20, 40)

        # Лёгкая декоративная россыпь "монетного" свечения
        # (чтобы визуально "обогатить" магазин)
        try:
            phase = self._coin_shimmer_phase
        except Exception:
            phase = 0.0
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(14):
            # размещаем сверху, чтобы не мешать контенту
            x = 30 + i * 32 + int(6 * math.sin(phase * 0.12 + i))
            y = 55 + int(10 * math.sin(phase * 0.08 + i * 0.6))
            r = 3 + (i % 3)
            alpha = 40 + int(60 * (0.5 + 0.5 * math.sin(phase * 0.25 + i)))
            p.setBrush(QColor(255, 200, 60, alpha))
            p.drawEllipse(x, y, r * 2, r * 2)
            p.setBrush(QColor(255, 90, 90, alpha // 2))
            p.drawEllipse(x + r // 2, y + r // 2, r, r)
        p.end()

    def _build_ui(self):
        ml = QVBoxLayout(self)
        ml.setContentsMargins(8, 4, 8, 8)
        ml.setSpacing(4)

        # ── Title bar ──
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        title = QLabel("\U0001f6d2 МАГАЗИН")
        title.setStyleSheet(
            "color:#ffcc00; font-size:15px; font-weight:bold; font-family:'Impact','Arial Black',sans-serif;"
            "letter-spacing:2px; background:transparent;"
        )
        hdr.addWidget(title, 1)

        min_btn = QPushButton("\u2014")
        min_btn.setFixedSize(28, 28)
        min_btn.setStyleSheet(
            "QPushButton{border:1px solid #886611;color:#ffcc00;font-size:14px;"
            "padding:0;border-radius:5px;background:rgba(30,15,0,200);min-height:0;min-width:0;}"
            "QPushButton:hover{background:rgba(60,30,0,230);}"
        )
        min_btn.clicked.connect(self.showMinimized)
        hdr.addWidget(min_btn)

        close_btn = QPushButton("\u2716")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(
            "QPushButton{border:1px solid #661111;color:#ff4444;font-size:14px;"
            "padding:0;border-radius:5px;background:rgba(30,5,0,200);min-height:0;min-width:0;}"
            "QPushButton:hover{background:rgba(80,10,0,230);border-color:#cc2222;}"
        )
        close_btn.clicked.connect(self.close)
        hdr.addWidget(close_btn)
        ml.addLayout(hdr)

        # ── Wallet counters (золото/ключи) ──
        wallet = QFrame()
        wallet.setStyleSheet(
            "QFrame{background:rgba(10,5,0,160);border:1px solid #886611;"
            "border-radius:10px;}"
        )
        wl = QHBoxLayout(wallet)
        wl.setContentsMargins(14, 10, 14, 10)
        wl.setSpacing(14)
        wl.addWidget(QLabel("🪙"))
        self._wallet_gold_label = QLabel(str(self._panel.shop.get_gold()))
        self._wallet_gold_label.setStyleSheet(
            "color:#ffcc00; font-size:16px; font-weight:bold; background:transparent;"
        )
        wl.addWidget(self._wallet_gold_label)
        sep = QLabel("│")
        sep.setStyleSheet("color:#444; font-size:12px; background:transparent;")
        wl.addWidget(sep)
        wl.addWidget(QLabel("🥐"))
        self._wallet_keys_label = QLabel(str(self._panel.shop.get_keys()))
        self._wallet_keys_label.setStyleSheet(
            "color:#dda644; font-size:16px; font-weight:bold; background:transparent;"
        )
        wl.addWidget(self._wallet_keys_label)
        wl.addStretch(1)
        ml.addWidget(wallet)

        # ── Navigation ──
        nav = QHBoxLayout()
        nav.setSpacing(4)
        nav_btns = []
        for label, anchor in [("\U0001f6d2 Темы", "shop_themes"), ("\U0001f3b0 Рулетка", "shop_gacha"), ("\U0001f4b1 Обмен", "shop_exchange")]:
            b = QPushButton(label)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                "QPushButton{color:#cc8844;background:rgba(30,12,5,200);border:1px solid #553311;"
                "border-radius:4px;padding:5px 10px;font-size:11px;font-weight:bold;}"
                "QPushButton:hover{background:rgba(50,20,10,230);border-color:#884422;}"
            )
            nav.addWidget(b)
            nav_btns.append((b, anchor))
        ml.addLayout(nav)

        # ── Scroll area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        scroll_w = QWidget()
        scroll_w.setStyleSheet("background:transparent;")
        self._shop_layout = QVBoxLayout(scroll_w)
        self._shop_layout.setContentsMargins(2, 2, 2, 2)
        self._shop_layout.setSpacing(8)
        scroll.setWidget(scroll_w)
        ml.addWidget(scroll)

        panel = self._panel

        # ══ Секция 1: Темы ══
        sec1 = QLabel("\U0001f6d2  МАГАЗИН ТЕМ")
        sec1.setObjectName("shop_themes")
        sec1.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sec1.setStyleSheet("color:#cc8844; padding:4px 0; background:transparent;")
        self._shop_layout.addWidget(sec1)

        pool_rem = panel.shop.pool_time_remaining()
        mins = pool_rem // 60
        self._pool_timer_label = QLabel(f"\u23f1 Обновление пула: {mins // 60}ч {mins % 60}м")
        self._pool_timer_label.setStyleSheet("color:#666; font-size:10px; background:transparent;")
        self._shop_layout.addWidget(self._pool_timer_label)

        self._shop_cards_container = QWidget()
        self._shop_cards_container.setStyleSheet("background:transparent;")
        from PyQt6.QtWidgets import QGridLayout
        self._shop_grid = QGridLayout(self._shop_cards_container)
        self._shop_grid.setSpacing(6)
        self._shop_grid.setContentsMargins(0, 0, 0, 0)
        self._build_shop_cards()
        self._shop_layout.addWidget(self._shop_cards_container)

        # ══ Секция 2: Рулетка ══
        sec2 = QLabel("\U0001f3b0  РУЛЕТКА")
        sec2.setObjectName("shop_gacha")
        sec2.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sec2.setStyleSheet("color:#cc8844; padding:4px 0; background:transparent;")
        self._shop_layout.addWidget(sec2)

        # Keyhole image area
        import os
        keyhole_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "keyhole.png")
        if os.path.exists(keyhole_path):
            kh_label = QLabel()
            kh_pm = QPixmap(keyhole_path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            kh_label.setPixmap(kh_pm)
            kh_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            kh_label.setStyleSheet("background:transparent;")
            self._shop_layout.addWidget(kh_label)

        gacha_desc = QLabel("Потрать \U0001f950 ключ-круассан и испытай удачу!\nШансы: \U0001f36c Карамелька 8% \u2022 \U0001f4b0 Золото \u2022 \U0001f4a8 Ничего 38%")
        gacha_desc.setWordWrap(True)
        gacha_desc.setStyleSheet("color:#888; font-size:10px; padding:2px; background:transparent;")
        self._shop_layout.addWidget(gacha_desc)

        self._gacha_result_label = QLabel("")
        self._gacha_result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._gacha_result_label.setStyleSheet("color:#ffcc00; font-size:14px; font-weight:bold; min-height:30px; background:transparent;")
        self._shop_layout.addWidget(self._gacha_result_label)

        spin_btn = QPushButton("\U0001f3b2  КРУТИТЬ  (1 \U0001f950)")
        spin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        spin_btn.setFixedHeight(40)
        spin_btn.setStyleSheet(
            "QPushButton{color:#fff;font-size:13px;font-weight:bold;border:2px solid #cc8844;"
            "border-radius:8px;background:qlineargradient(y1:0,y2:1,stop:0 #aa5522,stop:1 #773311);}"
            "QPushButton:hover{background:qlineargradient(y1:0,y2:1,stop:0 #cc6633,stop:1 #994422);border-color:#ffaa55;}"
            "QPushButton:pressed{background:#662211;}"
        )
        spin_btn.clicked.connect(self._on_gacha_spin)
        self._shop_layout.addWidget(spin_btn)

        # ── Pie chart showing gacha chances ──
        self._chance_chart = _GachaChanceChart()
        self._shop_layout.addWidget(self._chance_chart)

        # ══ Секция 3: Обменник ══
        sec3 = QLabel("\U0001f4b1  ОБМЕННИК")
        sec3.setObjectName("shop_exchange")
        sec3.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sec3.setStyleSheet("color:#cc8844; padding:4px 0; background:transparent;")
        self._shop_layout.addWidget(sec3)

        exch_btn = QPushButton("\U0001f504  Обменять 1 \U0001f950 \u2192 250 \U0001fa99")
        exch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exch_btn.setFixedHeight(34)
        exch_btn.setStyleSheet(
            "QPushButton{color:#dda644;font-size:11px;font-weight:bold;border:1px solid #886600;"
            "border-radius:6px;background:rgba(40,20,0,200);}"
            "QPushButton:hover{background:rgba(60,30,0,220);border-color:#bb8800;}"
        )
        exch_btn.clicked.connect(self._on_exchange_key)
        self._shop_layout.addWidget(exch_btn)

        self._free_gold_btn = QPushButton("\U0001f381  Бесплатное золото")
        self._free_gold_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._free_gold_btn.setFixedHeight(34)
        self._free_gold_btn.clicked.connect(self._on_claim_free_gold)
        self._shop_layout.addWidget(self._free_gold_btn)

        self._free_key_btn = QPushButton("\U0001f511  Бесплатный ключ (раз в сутки)")
        self._free_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._free_key_btn.setFixedHeight(34)
        self._free_key_btn.clicked.connect(self._on_claim_free_key)
        self._shop_layout.addWidget(self._free_key_btn)
        self._update_free_buttons()

        self._shop_exchange_label = QLabel("")
        self._shop_exchange_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._shop_exchange_label.setStyleSheet("color:#88cc44; font-size:11px; background:transparent;")
        self._shop_layout.addWidget(self._shop_exchange_label)
        panel._shop_exchange_label = self._shop_exchange_label

        self._shop_layout.addStretch()

        # Navigation scroll-to
        for btn, anchor in nav_btns:
            btn.clicked.connect(lambda checked, a=anchor: self._scroll_to_section(a, scroll))

    def _update_wallet_labels(self):
        """Синхронизирует счетчики золота/ключей на шапке магазина."""
        if hasattr(self, "_wallet_gold_label"):
            self._wallet_gold_label.setText(str(self._panel.shop.get_gold()))
        if hasattr(self, "_wallet_keys_label"):
            self._wallet_keys_label.setText(str(self._panel.shop.get_keys()))

    def _scroll_to_section(self, anchor, scroll):
        target = scroll.widget().findChild(QLabel, anchor)
        if target:
            scroll.ensureWidgetVisible(target, 0, 20)

    def _build_shop_cards(self):
        """Build theme cards in shop grid."""
        while self._shop_grid.count():
            item = self._shop_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        panel = self._panel
        pool = panel.shop.get_theme_pool()
        purchased = panel.config.get("shop_purchased_themes", [])
        row, col = 0, 0
        for tid in pool:
            theme = get_theme_by_id(tid)
            if not theme:
                continue
            owned = tid in purchased
            card = QFrame()
            card.setFixedSize(150, 110)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(6, 6, 6, 6)
            cl.setSpacing(2)

            name_l = QLabel(theme.get("name", tid))
            name_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_l.setStyleSheet("color:#ffcc00;font-size:10px;font-weight:bold;background:transparent;")
            name_l.setWordWrap(True)
            cl.addWidget(name_l)

            price = panel.shop.get_theme_price(tid)
            if owned:
                status = QLabel("\u2705 Куплено")
                status.setStyleSheet("color:#44cc44;font-size:9px;background:transparent;")
                status.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cl.addWidget(status)
                card.setStyleSheet(
                    "QFrame{background:rgba(10,30,10,200);border:1px solid #44aa44;border-radius:6px;}"
                )
            else:
                price_l = QLabel(f"\U0001fa99 {price}")
                price_l.setStyleSheet("color:#dda644;font-size:10px;background:transparent;")
                price_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cl.addWidget(price_l)
                buy_btn = QPushButton("Купить")
                buy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                buy_btn.setStyleSheet(
                    "QPushButton{color:#fff;font-size:10px;border:1px solid #886600;"
                    "border-radius:4px;background:rgba(60,30,0,200);padding:3px;}"
                    "QPushButton:hover{background:rgba(90,45,0,220);}"
                )
                buy_btn.clicked.connect(lambda checked, t=tid, p=price: self._buy_theme(t, p))
                cl.addWidget(buy_btn)
                card.setStyleSheet(
                    "QFrame{background:rgba(20,10,0,200);border:1px solid #553311;border-radius:6px;}"
                )
            self._shop_grid.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def _buy_theme(self, tid, price):
        panel = self._panel
        if panel.shop.purchase_theme(tid, price):
            # Трекинг для ачивок
            panel.config["_themes_bought"] = panel.config.get("_themes_bought", 0) + 1
            if price > 1000:
                panel.config["_bought_over_1000"] = True
            if price >= 5000:
                panel.config["_bought_5000"] = True
            from modules.config import save_config
            save_config(panel.config)
            panel._update_currency_display()
            self._build_shop_cards()
            panel._refresh_themes()
            # Уведомление
            t = get_theme_by_id(tid)
            name = t["name"] if t else tid
            flash = ComboFlashLabel(f"🎉 {name}\nкуплена!", panel, 3000)
            flash.setStyleSheet(
                f"color:#ffcc00; font-size:22px; font-weight:bold; "
                f"font-family:'Impact','Arial Black',sans-serif; background:transparent;"
            )
            flash.show()

    def _on_gacha_spin(self):
        """Крутить рулетку (из ShopWindow)."""
        panel = self._panel
        if panel.shop.get_keys() < 1:
            self._gacha_result_label.setText("❌ Недостаточно ключей!")
            self._gacha_result_label.setStyleSheet("color:#ff4444; font-size:14px; font-weight:bold; min-height:30px; background:transparent;")
            return
        result = panel.shop.spin_gacha()
        if not result or result.get("type") == "nothing" and result.get("value") == 0 and panel.shop.get_keys() < 0:
            return
        # Трекинг для ачивок
        panel.config["_gacha_spins"] = panel.config.get("_gacha_spins", 0) + 1
        from modules.config import save_config
        save_config(panel.config)
        panel._update_currency_display()
        rtype = result.get("type", "nothing")
        val = result.get("value", 0)
        if rtype == "theme":
            t = get_theme_by_id(val) if val else None
            name = t["name"] if t else "Тема"
            self._gacha_result_label.setText(f"🍬 {name} разблокирована!")
            self._gacha_result_label.setStyleSheet("color:#ff44ff; font-size:14px; font-weight:bold; min-height:30px; background:transparent;")
            panel._refresh_themes()
        elif rtype == "gold":
            self._gacha_result_label.setText(f"💰 +{val} золота!")
            clr = "#ffcc00" if val >= 500 else "#dda644"
            self._gacha_result_label.setStyleSheet(f"color:{clr}; font-size:14px; font-weight:bold; min-height:30px; background:transparent;")
        elif rtype == "sticker":
            sid = result.get("sticker_id", "sticker_star")
            self._gacha_result_label.setText(f"🏷 Наклейка получена!")
            self._gacha_result_label.setStyleSheet("color:#44ccff; font-size:14px; font-weight:bold; min-height:30px; background:transparent;")
            # Спавн наклейки на вкладке кодов
            panel.config["_sticker_count"] = panel.config.get("_sticker_count", 0) + 1
            save_config(panel.config)
        else:
            self._gacha_result_label.setText("💨 Пусто...")
            self._gacha_result_label.setStyleSheet("color:#555; font-size:14px; font-weight:bold; min-height:30px; background:transparent;")


    def _on_exchange_key(self):
        panel = self._panel
        if panel.shop.exchange_key_to_gold():
            panel._update_currency_display()
            self._shop_exchange_label.setText("✅ +250 🪙")
            QTimer.singleShot(2000, lambda: self._shop_exchange_label.setText(""))
        else:
            self._shop_exchange_label.setText("❌ Нет ключей")
            self._shop_exchange_label.setStyleSheet("color:#ff4444; font-size:11px; background:transparent;")

    def _on_claim_free_gold(self):
        panel = self._panel
        if panel.shop.can_claim_free_gold():
            amt = panel.shop.claim_free_gold()
            panel._update_currency_display()
            self._shop_exchange_label.setText(f"🎁 +{amt} 🪙")
            QTimer.singleShot(2000, lambda: self._shop_exchange_label.setText(""))
        self._update_free_buttons()

    def _on_claim_free_key(self):
        panel = self._panel
        if panel.shop.can_claim_free_key():
            panel.shop.claim_free_key()
            panel._update_currency_display()
            self._shop_exchange_label.setText("🔑 +1 ключ!")
            QTimer.singleShot(2000, lambda: self._shop_exchange_label.setText(""))
        self._update_free_buttons()

    def _update_free_buttons(self):
        panel = self._panel
        if hasattr(self, '_free_gold_btn'):
            can = panel.shop.can_claim_free_gold()
            self._free_gold_btn.setEnabled(can)
            if not can:
                secs = panel.shop.free_gold_seconds_remaining()
                m, s = divmod(secs, 60)
                self._free_gold_btn.setText(f"🎁 Золото через {m}м {s}с")
            else:
                self._free_gold_btn.setText("🎁 Бесплатное золото")
        if hasattr(self, '_free_key_btn'):
            can = panel.shop.can_claim_free_key()
            self._free_key_btn.setEnabled(can)
            if not can:
                self._free_key_btn.setText("🔑 Ключ получен сегодня")
            else:
                self._free_key_btn.setText("🔑 Бесплатный ключ (раз в сутки)")


class _GachaChanceChart(QWidget):
    """Simple pie chart showing gacha drop chances."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(160, 160)
        self.setStyleSheet("background:transparent;")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(10, 10, 140, 140)
        # Chances: Nothing 38%, Gold(small) 30%, Gold(medium) 15%, Gold(big) 9%, Candy 8%
        segments = [
            (38, QColor("#333333"), "Ничего 38%"),
            (30, QColor("#aa8822"), "Золото(м) 30%"),
            (15, QColor("#ccaa33"), "Золото(с) 15%"),
            (9, QColor("#ffcc00"), "Золото(б) 9%"),
            (8, QColor("#ff6699"), "Карамелька 8%"),
        ]
        start = 0
        for pct, color, label in segments:
            span = int(pct * 3.6 * 16)
            p.setBrush(QBrush(color))
            p.setPen(QPen(QColor("#000000"), 1))
            p.drawPie(rect, start, span)
            start += span

        # Legend
        p.setPen(QColor("#999999"))
        p.setFont(QFont("Segoe UI", 7))
        y_off = 155
        p.end()


# ═══════════════════════════════════════════════════════════════
#  Главная панель
# ═══════════════════════════════════════════════════════════════
class DictatorControlPanel(QMainWindow):
    request_calibrate_zone = pyqtSignal()
    request_calibrate_color = pyqtSignal()
    request_start_detection = pyqtSignal()
    request_stop_detection = pyqtSignal()
    request_mercy = pyqtSignal()
    request_panic_stop = pyqtSignal()
    request_show_zone = pyqtSignal()
    threshold_changed = pyqtSignal(float)
    theme_changed = pyqtSignal(dict)  # передаёт новую тему в main.py
    account_wipe_confirmed = pyqtSignal()

    def __init__(self, stats_manager, config, parent=None, cloud_service=None):
        super().__init__(parent)
        self.stats = stats_manager
        self.config = config
        self._cloud_service = cloud_service
        self._cheater_theme_locked = False
        from modules.config import save_config
        self.shop = ShopManager(config, save_config)
        self.daily_quests = DailyQuestManager(self.config, self.stats, save_config)
        self._user_nickname = "???"  # заполняется после авторизации
        self._user_fio = ""
        self._profile_id = None

        # Загрузка кастомных шрифтов
        from PyQt6.QtGui import QFontDatabase
        import os
        fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
        for fname in ("digital-7 (mono).ttf", "digital-7.ttf"):
            fpath = os.path.join(fonts_dir, fname)
            if os.path.exists(fpath):
                fid = QFontDatabase.addApplicationFont(fpath)
                if fid >= 0:
                    families = QFontDatabase.applicationFontFamilies(fid)
                    print(f"[FONT] Loaded: {families}")

        # Текущая тема
        saved_theme = config.get("theme_id", DEFAULT_THEME_ID)
        self._current_theme = get_theme_by_id(saved_theme) or get_theme_by_id(DEFAULT_THEME_ID)

        # Движок наказаний
        self.punishments = PunishmentEngine()
        self._active_punishment_overlay = None
        self._known_unlocked_themes = set()  # для отслеживания новых разблокировок тем
        # Гейтинг (дозированное открытие контента)
        self._content_gate_prev = {"stats": False, "shop": False, "themes": False}
        self._content_gate_prev = dict(self._content_gate_prev)
        self._tab_idx_stats = None
        self._tab_idx_themes = None
        self._tab_idx_goals = None
        self._shop_btn = None

        self.setWindowTitle("INFERNO GRADE TRACKER")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._expanded = False
        self._detection_active = False
        self._combo_count = 0
        self._combo_timer_sec = 0
        self._dragging = False
        self._drag_pos = None
        self._bg_opacity = config.get("bg_opacity", 92)
        self._widget_opacity = config.get("widget_opacity", 95)
        self._fx_opacity = config.get("fx_opacity", 100)
        self._streak_pulse_phase = 0.0
        self._combo_blink_on = True
        self._mercy_timer_sec = 0
        self._bounce_step = 0

        # Overlay для искр курсора (заряженная тема)
        self._spark_overlay = CursorSparkOverlay()
        self._star_overlay = BottomlessStarOverlay()
        self._star_overlay.star_clicked.connect(self._on_star_exploded)

        # Фиксируем seed для censor_text чтобы описания не менялись
        self._censor_seed = config.get("_censor_seed", random.randint(0, 99999))
        config["_censor_seed"] = self._censor_seed

        self._build_ui()
        self._apply_style()
        self._update_theme_effects()
        self._apply_btn_images()
        self._start_timers()

    def show(self):
        """Показывает панель по центру экрана."""
        super().show()
        scr = QApplication.primaryScreen()
        if scr:
            sg = scr.availableGeometry()
            x = (sg.width() - self.width()) // 2 + sg.x()
            y = (sg.height() - self.height()) // 2 + sg.y()
            self.move(x, y)

    def set_user(self, fio: str, nickname: str, profile_id: str | None = None):
        """Устанавливает пользователя после авторизации."""
        self._user_fio = fio
        self._user_nickname = nickname
        self._profile_id = profile_id
        # Обновляем название вкладки ачивок
        if hasattr(self, 'tabs'):
            idx = self._ach_tab_index
            self.tabs.setTabText(idx, f"\U0001f4c2 Файлы\n{nickname}")

    def set_cheater_theme_locked(self, locked: bool):
        """
        True — смена темы не сохраняется в config, интерфейс остаётся «клоунским».
        При снятии блокировки восстанавливается theme_id из конфига.
        """
        self._cheater_theme_locked = bool(locked)
        if locked:
            self._select_theme(CHEATER_THEME_ID)
        else:
            tid = self.config.get("theme_id", DEFAULT_THEME_ID)
            self._select_theme(tid)

    # ── Drag ──────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            # Emoji explosion (Адская тема) — на каждый клик
            gp = e.globalPosition().toPoint()
            self._emoji_boom_at(gp.x(), gp.y(), 12)
            # Бездонная тема: клик по центру воронки
            if self._current_theme.get("spiral_theme") and hasattr(self, '_spiral_cursor_dist'):
                if self._spiral_cursor_dist < 60:
                    self._handle_spiral_click(e)
                    return  # не начинаем drag
            self._dragging = True
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._dragging and self._drag_pos:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._dragging = False

    # ── Фон ───────────────────────────────────────────────────
    def _make_octagon_path(self, x0, y0, x1, y1, chamfer=28):
        """Октагональная форма: прямоугольник со срезанными углами. Координаты: (x0,y0)-(x1,y1)."""
        ch = chamfer
        return QPolygonF([
            QPointF(x0 + ch, y0), QPointF(x1 - ch, y0),
            QPointF(x1, y0 + ch), QPointF(x1, y1 - ch),
            QPointF(x1 - ch, y1), QPointF(x0 + ch, y1),
            QPointF(x0, y1 - ch), QPointF(x0, y0 + ch),
        ])

    def _make_hourglass_path(self, w, h):
        """Форма 'прокладка' / песочные часы: широкая сверху и снизу, узкая в центре."""
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        # Параметры формы
        top_w = w * 0.85       # ширина верхнего купола
        bot_w = w * 0.65       # ширина нижнего купола
        waist_w = w * 0.42     # ширина перетяжки (середина)
        waist_y = h * 0.52     # высота перетяжки
        top_h = h * 0.32       # высота верхнего купола
        bot_h = h * 0.22       # высота нижнего купола
        cx = w / 2
        # Строим путь: начинаем с верхнего центра и идём по часовой
        # Верхний купол — полукруг
        path.moveTo(cx - top_w / 2, top_h)
        path.cubicTo(cx - top_w / 2, 0,
                     cx + top_w / 2, 0,
                     cx + top_w / 2, top_h)
        # Правая сторона: от верхнего купола к перетяжке
        path.cubicTo(cx + top_w / 2, top_h + (waist_y - top_h) * 0.4,
                     cx + waist_w / 2, waist_y - (waist_y - top_h) * 0.3,
                     cx + waist_w / 2, waist_y)
        # Правая сторона: от перетяжки к нижнему куполу
        path.cubicTo(cx + waist_w / 2, waist_y + (h - bot_h - waist_y) * 0.3,
                     cx + bot_w / 2, h - bot_h - (h - bot_h - waist_y) * 0.4,
                     cx + bot_w / 2, h - bot_h)
        # Нижний купол — полукруг
        path.cubicTo(cx + bot_w / 2, h,
                     cx - bot_w / 2, h,
                     cx - bot_w / 2, h - bot_h)
        # Левая сторона: от нижнего купола к перетяжке
        path.cubicTo(cx - bot_w / 2, h - bot_h - (h - bot_h - waist_y) * 0.4,
                     cx - waist_w / 2, waist_y + (h - bot_h - waist_y) * 0.3,
                     cx - waist_w / 2, waist_y)
        # Левая сторона: от перетяжки к верхнему куполу
        path.cubicTo(cx - waist_w / 2, waist_y - (waist_y - top_h) * 0.3,
                     cx - top_w / 2, top_h + (waist_y - top_h) * 0.4,
                     cx - top_w / 2, top_h)
        path.closeSubpath()
        return path

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        a = int(255 * self._bg_opacity / 100)
        c = self._current_theme["colors"]
        bg_top = c["bg_top"]
        bg_mid = c["bg_mid"]
        bg_bot = c["bg_bot"]
        rect = self.rect().adjusted(1, 1, -1, -1)
        is_octagon = self._current_theme.get("shape") == "octagon"
        is_hourglass = self._current_theme.get("shape") == "hourglass"
        is_circle = self._current_theme.get("shape") == "circle"

        # ── Форма "круг" (бездонная тема) ──────────
        if is_circle:
            from PyQt6.QtGui import QPainterPath
            radius = min(w, h) / 2 - 2
            cx_c, cy_c = w / 2, h / 2
            circle_path = QPainterPath()
            circle_path.addEllipse(QPointF(cx_c, cy_c), radius, radius)
            # Чёрный фон
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, a))
            p.drawPath(circle_path)
            # Клиппинг по кругу
            p.setClipPath(circle_path)
            if self._current_theme.get("spiral_theme"):
                self._draw_bottomless_effects(p, w, h, rect)
            # Обводка круга
            p.setClipping(False)
            cs = getattr(self, '_spiral_color_shift', 0.0)
            br = int(230 * (1 - cs) + 100 * cs)
            bb = int(20 * (1 - cs) + 220 * cs)
            p.setPen(QPen(QColor(br, 15, bb, 200), 3.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(circle_path)
            p.end()
            return

        # ── Форма "песочные часы" (legacy) ──────────
        if is_hourglass:
            from PyQt6.QtGui import QPainterPath
            hg_path = self._make_hourglass_path(w, h)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, a))
            p.drawPath(hg_path)
            p.setClipPath(hg_path)
            if self._current_theme.get("spiral_theme"):
                self._draw_bottomless_effects(p, w, h, rect)
            p.setClipping(False)
            cs = getattr(self, '_spiral_color_shift', 0.0)
            br_ = int(200 * (1 - cs) + 90 * cs)
            bb_ = int(15 * (1 - cs) + 200 * cs)
            p.setPen(QPen(QColor(br_, 15, bb_, 180), 2.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(hg_path)
            p.end()
            return

        # ── Октагональная форма ──────────────────────────────
        if is_octagon:
            chamfer = 42
            tab_w = 24  # ширина боковых колб
            # Фон — на всю ширину окна (октагон без боковых отступов)
            octa_full = self._make_octagon_path(1, 1, w - 1, h - 1, chamfer)

            # Фон — тёмно-зелёное полотно с градиентом
            grad = QLinearGradient(0, 0, 0, h)
            grad.setColorAt(0.0, QColor(bg_top[0], bg_top[1], bg_top[2], a))
            grad.setColorAt(0.5, QColor(bg_mid[0], bg_mid[1], bg_mid[2], a))
            grad.setColorAt(1.0, QColor(bg_bot[0], bg_bot[1], bg_bot[2], a))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawPolygon(octa_full)

            # Текстура полотна — мелкий шум
            import random as _rnd
            state = _rnd.getstate()
            _rnd.seed(777)
            for _ in range(100):
                nx = _rnd.randint(6, w - 6)
                ny = _rnd.randint(4, h - 4)
                na = _rnd.randint(5, 18)
                p.setBrush(QColor(0, 0, 0, na))
                p.drawEllipse(nx, ny, 2, 2)
            _rnd.setstate(state)

            # ── Багровые лазерные выстрелы (клиппинг по октагону) ──
            from PyQt6.QtGui import QPainterPath
            if hasattr(self, '_villain_lasers') and self._villain_lasers:
                p.save()
                clip_path = QPainterPath()
                clip_path.addPolygon(octa_full)
                clip_path.closeSubpath()
                p.setClipPath(clip_path)
                for las in self._villain_lasers:
                    al = las["alpha"]
                    if al <= 0:
                        continue
                    angle_rad = math.radians(las["angle"])
                    half_len = las["length"] / 2
                    dx = math.cos(angle_rad) * half_len
                    dy = math.sin(angle_rad) * half_len
                    x1 = las["x"] - dx
                    y1 = las["y"] - dy
                    x2 = las["x"] + dx
                    y2 = las["y"] + dy
                    # Свечение — широкая полупрозрачная линия
                    p.setPen(QPen(QColor(220, 40, 50, al // 3), 13.5))
                    p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                    # Основной луч — яркая линия
                    p.setPen(QPen(QColor(184, 28, 40, al), 4.5))
                    p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                    # Яркое ядро — тонкое, почти белое
                    p.setPen(QPen(QColor(255, 120, 120, al // 2), 2.25))
                    p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                p.restore()

            # Боковые колбы (табы) с прогресс-барами — поверх лазеров
            tab_top = chamfer + 50
            tab_bot = h - chamfer - 50
            tab_h = tab_bot - tab_top
            if tab_h > 40:
                rank_progress = 0.0
                if hasattr(self, 'stats'):
                    total = self.stats.total
                    _, progress, _ = get_rank_progress(total)
                    rank_progress = progress / 100.0
                tab_bg = c.get("bar_bg", (30, 38, 30))
                bar_fill = c.get("bar_fill", (180, 28, 40))
                border_col = QColor(c["border"])
                border_col.setAlpha(200)
                for side in ("left", "right"):
                    if side == "left":
                        tx0, tx1 = 2, tab_w
                    else:
                        tx0, tx1 = w - tab_w, w - 2
                    # Фон колбы — скруглённый прямоугольник
                    flask_rect = QRect(int(tx0), int(tab_top), int(tx1 - tx0), int(tab_h))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(tab_bg[0], tab_bg[1], tab_bg[2], 210))
                    p.drawRoundedRect(flask_rect, 6, 6)
                    # Заливка прогресса снизу вверх
                    fill_h = int(tab_h * rank_progress)
                    if fill_h > 2:
                        fill_rect = QRect(
                            int(tx0) + 2, int(tab_bot) - fill_h,
                            int(tx1 - tx0) - 4, fill_h
                        )
                        fg = QLinearGradient(0, tab_bot, 0, tab_bot - fill_h)
                        fg.setColorAt(0.0, QColor(bar_fill[0], bar_fill[1], bar_fill[2], 230))
                        fg.setColorAt(1.0, QColor(bar_fill[0], bar_fill[1], bar_fill[2], 100))
                        p.setBrush(QBrush(fg))
                        p.drawRoundedRect(fill_rect, 4, 4)
                    # Рамка колбы
                    p.setPen(QPen(border_col, 1.5))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawRoundedRect(flask_rect, 6, 6)
                    # Горлышко колбы — маленький прямоугольник сверху
                    neck_w = int((tx1 - tx0) * 0.5)
                    neck_x = int(tx0 + (tx1 - tx0 - neck_w) / 2)
                    neck_rect = QRect(neck_x, int(tab_top) - 8, neck_w, 10)
                    p.setBrush(QColor(tab_bg[0], tab_bg[1], tab_bg[2], 180))
                    p.drawRoundedRect(neck_rect, 3, 3)
                    p.setPen(QPen(border_col, 1))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawRoundedRect(neck_rect, 3, 3)

            p.end()
            return

        # ── Стандартная форма ─────────────────────────────────
        cr = 0 if self._current_theme.get("sharp_corners") else 12  # corner radius
        # Фон: плоский, волнистый или градиент
        if self._current_theme.get("flat_bg"):
            p.setBrush(QColor(bg_top[0], bg_top[1], bg_top[2], a))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, cr, cr)
        elif self._current_theme.get("wavy_bg"):
            # Волнистый асимметричный градиент — закатный эффект
            from PyQt6.QtGui import QPainterPath
            p.setPen(Qt.PenStyle.NoPen)
            # Базовый фон — нижний цвет
            p.setBrush(QColor(bg_bot[0], bg_bot[1], bg_bot[2], a))
            p.drawRoundedRect(rect, cr, cr)
            phase = getattr(self, '_gold_dust_phase', 0.0)
            # Клиппинг по скруглённому прямоугольнику окна
            clip_rr = QPainterPath()
            clip_rr.addRoundedRect(float(rect.x()), float(rect.y()),
                                   float(rect.width()), float(rect.height()), cr, cr)
            p.setClipPath(clip_rr)
            # Волна 1: верхний цвет — тёмно-синий, занимает ~45% сверху, извилистый край
            wave1 = QPainterPath()
            wave1.moveTo(0, 0)
            wave1.lineTo(w, 0)
            y1_base = h * 0.42
            steps = 32
            for s in range(steps + 1):
                sx = w * s / steps
                sy = y1_base + math.sin(sx * 0.022 + phase * 0.3) * 30 + math.sin(sx * 0.011 + phase * 0.18 + 1.5) * 22 + math.cos(sx * 0.035 + phase * 0.08 + 3.0) * 12
                wave1.lineTo(sx, sy)
            # Нижний край тоже волнистый (не прямая линия)
            for s in range(steps, -1, -1):
                sx = w * s / steps
                sy = y1_base + 15 + math.sin(sx * 0.016 + phase * 0.22 + 4.5) * 18 + math.cos(sx * 0.028 + phase * 0.12 + 2.0) * 10
                wave1.lineTo(sx, sy)
            wave1.closeSubpath()
            p.setBrush(QColor(bg_top[0], bg_top[1], bg_top[2], a))
            p.drawPath(wave1)
            # Волна 2: средний цвет — тёмно-фиолетовый, от ~25% до ~65%
            wave2 = QPainterPath()
            y2_top = h * 0.22
            y2_bot = h * 0.62
            # Верхний край — слева направо
            wave2.moveTo(0, y2_top + math.sin(phase * 0.2 + 2.0) * 20 + math.cos(phase * 0.12) * 15)
            for s in range(1, steps + 1):
                sx = w * s / steps
                sy = y2_top + math.sin(sx * 0.015 + phase * 0.2 + 2.0) * 20 + math.cos(sx * 0.008 + phase * 0.12) * 15
                wave2.lineTo(sx, sy)
            # Нижний край — справа налево (оба края волнистые, без диагоналей)
            for s in range(steps, -1, -1):
                sx = w * s / steps
                sy = y2_bot + math.sin(sx * 0.012 + phase * 0.25 + 0.7) * 22 + math.cos(sx * 0.02 + phase * 0.18 + 3.0) * 14
                wave2.lineTo(sx, sy)
            wave2.closeSubpath()
            p.setBrush(QColor(bg_mid[0], bg_mid[1], bg_mid[2], a))
            p.drawPath(wave2)
            # Волна 3: accent — тёплый багровый блик, полоса ~52-72%
            wave3 = QPainterPath()
            y3_top = h * 0.52
            y3_bot = h * 0.72
            wave3.moveTo(0, y3_top + math.sin(phase * 0.35 + 4.0) * 16 + math.sin(phase * 0.1) * 10)
            for s in range(1, steps + 1):
                sx = w * s / steps
                sy = y3_top + math.sin(sx * 0.02 + phase * 0.35 + 4.0) * 16 + math.sin(sx * 0.01 + phase * 0.1) * 10
                wave3.lineTo(sx, sy)
            for s in range(steps, -1, -1):
                sx = w * s / steps
                sy = y3_bot + math.cos(sx * 0.013 + phase * 0.22 + 1.2) * 18 + math.sin(sx * 0.018 + phase * 0.15 + 2.5) * 10
                wave3.lineTo(sx, sy)
            wave3.closeSubpath()
            p.setBrush(QColor(178, 46, 55, int(a * 0.5)))
            p.drawPath(wave3)
            # Волна 4: тёплый оранжевый/жёлтый блик, полоса ~33-48%
            wave4 = QPainterPath()
            y4_top = h * 0.33
            y4_bot = h * 0.48
            wave4.moveTo(0, y4_top + math.sin(phase * 0.28 + 5.5) * 12 + math.cos(phase * 0.15 + 2.3) * 8)
            for s in range(1, steps + 1):
                sx = w * s / steps
                sy = y4_top + math.sin(sx * 0.025 + phase * 0.28 + 5.5) * 12 + math.cos(sx * 0.011 + phase * 0.15 + 2.3) * 8
                wave4.lineTo(sx, sy)
            for s in range(steps, -1, -1):
                sx = w * s / steps
                sy = y4_bot + math.sin(sx * 0.016 + phase * 0.2 + 3.8) * 14 + math.cos(sx * 0.022 + phase * 0.12 + 1.0) * 8
                wave4.lineTo(sx, sy)
            wave4.closeSubpath()
            p.setBrush(QColor(246, 131, 24, int(a * 0.25)))
            p.drawPath(wave4)
            p.setClipping(False)
        else:
            grad = QLinearGradient(0, 0, 0, h)
            grad.setColorAt(0.0, QColor(bg_top[0], bg_top[1], bg_top[2], a))
            grad.setColorAt(0.4, QColor(bg_mid[0], bg_mid[1], bg_mid[2], a))
            grad.setColorAt(0.8, QColor(bg_mid[0], bg_mid[1], bg_mid[2], a))
            grad.setColorAt(1.0, QColor(bg_bot[0], bg_bot[1], bg_bot[2], a))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, cr, cr)

        # Заряженная: плавно нарастающий голубой оттенок
        charged_int = getattr(self, '_charged_intensity', 0.0)
        if self._current_theme.get("edge_lightning") and charged_int > 0.01:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(40, 100, 220, int(126 * charged_int)))
            p.drawRoundedRect(rect, cr, cr)

        # ── Прозрачность фоновых эффектов ──
        fx_opa = self._fx_opacity / 100.0
        if fx_opa < 0.99:
            p.setOpacity(fx_opa)

        # Фоновая картинка (зловещая тема — sc.jpg)
        if self._current_theme.get("bg_image_file"):
            self._draw_bg_image_file(p, w, h, cr)

        # Сканлайны (ретро-тема: горизонтальные плывущие полосы)
        if self._current_theme.get("bg_scanlines"):
            self._draw_scanlines(p, w, h, a)

        # Сетка (если не отключена)
        if not self._current_theme.get("no_grid"):
            is_light = sum(c["bg_top"]) > 300
            if is_light:
                p.setPen(QColor(120, 100, 80, 15))
            elif self._current_theme.get("flat_bg"):
                p.setPen(QColor(60, 60, 60, 8))
            else:
                p.setPen(QColor(255, 15, 15, 10))
            sp = 20
            for x in range(0, w, sp):
                p.drawLine(x, 0, x, h)
            for y in range(0, h, sp):
                p.drawLine(0, y, w, y)

        # Гексагональная сетка (фрактальная тема)
        if self._current_theme.get("hex_grid"):
            self._draw_hex_grid(p, w, h)

        # Звёзды на фоне (тема "Почти звезда")
        if self._current_theme.get("bg_stars"):
            self._draw_bg_stars(p, w, h)

        # Плавающие картинки (ku/kuu и т.д.)
        if self._current_theme.get("bg_images"):
            self._draw_bg_images(p, w, h)

        # Плавающие символы (классические темы)
        if self._current_theme.get("bg_symbols"):
            self._draw_bg_symbols(p, w, h)

        # Центральная картинка (lol.png)
        if self._current_theme.get("bg_center_image"):
            self._draw_center_image(p, w, h)

        # Пылинки
        particles = self._current_theme.get("bg_particles")
        if particles in ("gold_dust", "blue_dust"):
            self._draw_dust(p, w, h, particles)
        elif particles == "hex_dust":
            self._draw_hex_dust(p, w, h)
        elif particles == "binary_rain":
            self._draw_binary_rain(p, w, h)
        elif particles == "sun_rays":
            # ── Солнце — яркий шар за счётчиком ──
            label_pos = self.counter_label.mapTo(self, QPoint(0, 0))
            cx = label_pos.x() + self.counter_label.width() / 2
            cy = label_pos.y() + self.counter_label.height() / 2
            sun_phase = getattr(self, '_gold_dust_phase', 0.0)
            sun_pulse = 0.9 + 0.1 * math.sin(sun_phase * 0.5)
            # Внешнее мягкое свечение (большое, полупрозрачное)
            outer_r = 180 * sun_pulse
            outer_grad = QRadialGradient(cx, cy, outer_r)
            outer_grad.setColorAt(0.0, QColor(253, 210, 40, 70))
            outer_grad.setColorAt(0.5, QColor(246, 160, 20, 30))
            outer_grad.setColorAt(1.0, QColor(246, 131, 24, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(outer_grad))
            p.drawEllipse(QPointF(cx, cy), outer_r, outer_r)
            # Средний слой — тёплый оранжевый диск
            mid_r = 110 * sun_pulse
            mid_grad = QRadialGradient(cx, cy, mid_r)
            mid_grad.setColorAt(0.0, QColor(255, 220, 60, 200))
            mid_grad.setColorAt(0.4, QColor(253, 192, 5, 160))
            mid_grad.setColorAt(0.75, QColor(246, 131, 24, 80))
            mid_grad.setColorAt(1.0, QColor(246, 131, 24, 0))
            p.setBrush(QBrush(mid_grad))
            p.drawEllipse(QPointF(cx, cy), mid_r, mid_r)
            # Ядро — яркое белёсо-жёлтое пятно
            core_r = 55 * sun_pulse
            core_grad = QRadialGradient(cx, cy, core_r)
            core_grad.setColorAt(0.0, QColor(255, 255, 220, 255))
            core_grad.setColorAt(0.3, QColor(255, 240, 120, 240))
            core_grad.setColorAt(0.7, QColor(253, 200, 40, 180))
            core_grad.setColorAt(1.0, QColor(253, 192, 5, 0))
            p.setBrush(QBrush(core_grad))
            p.drawEllipse(QPointF(cx, cy), core_r, core_r)
            # Лучи-пылинки
            self._draw_sun_rays(p, w, h)
        elif particles == "black_smoke":
            self._draw_ominous_effects(p, w, h, a)
        elif particles == "bubbles":
            self._draw_bubbles(p, w, h)

        # Счётчик с фоновой картинкой (медиа-плеер)
        if self._current_theme.get("counter_bg_image"):
            self._draw_counter_bg_image(p)

        # Бездонная тема: спираль, частицы, шлейф
        if self._current_theme.get("spiral_theme"):
            self._draw_bottomless_effects(p, w, h, rect)

        # Заряженная тема: зигзаги, вспышки, волны
        if self._current_theme.get("edge_lightning"):
            self._draw_charged_effects(p, w, h, rect)

        # Свечение по краям (edge_glow)
        if self._current_theme.get("edge_glow"):
            self._draw_edge_glow(p, w, h)

        # Пульсирующая рамка (закат: жёлтый↔оранжевый)
        if self._current_theme.get("edge_glow_pulse"):
            self._draw_pulsing_border(p, w, h)

        # Мерцание для shadow_lord — фиолетовые вспышки
        if self._current_theme["id"] == "shadow_lord" and hasattr(self, '_shadow_purple_alpha'):
            pa = getattr(self, '_shadow_purple_alpha', 0)
            if pa > 0:
                p.setBrush(QColor(60, 0, 100, pa))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(rect, 12, 12)
        # Мерцание для hysteria — эпилептические вспышки цветом
        if self._current_theme["id"] == "hysteria" and hasattr(self, '_hysteria_flash_color'):
            hfc = getattr(self, '_hysteria_flash_color', None)
            hfa = getattr(self, '_hysteria_flash_alpha', 0)
            if hfc and hfa > 0:
                p.setBrush(QColor(hfc[0], hfc[1], hfc[2], hfa))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(rect, 12, 12)

        # ── Восстановить прозрачность после эффектов ──
        if fx_opa < 0.99:
            p.setOpacity(1.0)

        # Ретро: пиксельный счётчик — рендерим Fixedsys и масштабируем вверх
        if self._current_theme.get("counter_smiley"):
            self._draw_pixel_counter(p, w, h)

        # Зловещая: счётчик с белым текстом и толстым чёрным контуром
        if self._current_theme.get("counter_outline"):
            self._draw_outlined_counter(p, w, h)

        # Обводка счётчика цветом (адская тема и т.п.)
        outline_color = self._current_theme.get("counter_outline_color")
        if outline_color:
            self._draw_counter_color_outline(p, outline_color)

        # Бордер
        if not self._current_theme.get("no_border"):
            border_c = QColor(c["border"])
            border_c.setAlpha(140)
            p.setPen(QPen(border_c, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(rect, cr, cr)
        p.end()

    def _draw_bg_stars(self, p, w, h):
        """Рисуем звёзды из star1/star2.png — плавают и вращаются."""
        if not hasattr(self, '_star_pixmaps'):
            import os
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
            self._star_pixmaps = [QPixmap(os.path.join(base, f)) for f in ("star1.png", "star2.png")]
            self._star_pixmaps = [pm for pm in self._star_pixmaps if not pm.isNull()]
        if not self._star_pixmaps:
            return
        import math as _m
        phase = getattr(self, '_gold_dust_phase', 0.0)
        import random as _rnd
        state = _rnd.getstate()
        _rnd.seed(42)
        from PyQt6.QtGui import QTransform
        for i in range(8):
            pm = self._star_pixmaps[i % len(self._star_pixmaps)]
            bx = _rnd.randint(20, max(21, w - 70))
            by = _rnd.randint(20, max(21, h - 70))
            sz = _rnd.randint(28, 50)
            base_alpha = _rnd.randint(50, 120) / 255.0
            # Плавание
            sp = phase + i * 1.3
            dx = _m.sin(sp * 0.25 + i * 0.9) * 18
            dy = _m.cos(sp * 0.18 + i * 0.6) * 12
            # Вращение
            angle = _m.fmod(sp * 8 + i * 40, 360)
            # Мерцание яркости
            flicker = 0.7 + 0.3 * _m.sin(sp * 0.4 + i * 2.1)
            scaled = pm.scaled(sz, sz, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
            # Вращение через QTransform
            tf = QTransform()
            tf.translate(sz / 2, sz / 2)
            tf.rotate(angle)
            tf.translate(-sz / 2, -sz / 2)
            rotated = scaled.transformed(tf, Qt.TransformationMode.SmoothTransformation)
            ox = (rotated.width() - sz) // 2
            oy = (rotated.height() - sz) // 2
            p.setOpacity(base_alpha * flicker)
            p.drawPixmap(int(bx + dx) - ox, int(by + dy) - oy, rotated)
        p.setOpacity(1.0)
        _rnd.setstate(state)

    def _draw_bg_symbols(self, p, w, h):
        """Классические темы: плавающие символы/фигуры вместо картинок."""
        import math as _m
        import random as _rnd
        symbols = self._current_theme.get("bg_symbols", [])
        if not symbols:
            return
        phase = getattr(self, '_gold_dust_phase', 0.0)
        c = self._current_theme["colors"]
        fc = c.get("fire_core", (200, 100, 50))
        fx_o = self._fx_opacity / 100.0
        state = _rnd.getstate()
        _rnd.seed(42)
        count = 12
        for i in range(count):
            sym = symbols[i % len(symbols)]
            bx = _rnd.randint(15, max(16, w - 50))
            by = _rnd.randint(25, max(26, h - 50))
            sz = _rnd.randint(18, 38)
            base_alpha = _rnd.randint(50, 130) / 255.0
            sp = phase + i * 1.3
            dx = _m.sin(sp * 0.2 + i * 0.9) * 18
            dy = _m.cos(sp * 0.15 + i * 0.6) * 14
            flicker = 0.65 + 0.35 * _m.sin(sp * 0.3 + i * 1.7)
            p.setOpacity(base_alpha * flicker * fx_o)
            font = QFont("Segoe UI Emoji", sz)
            p.setFont(font)
            p.setPen(QColor(fc[0], fc[1], fc[2], int(255 * base_alpha * flicker)))
            p.drawText(int(bx + dx), int(by + dy), sym)
        p.setOpacity(fx_o)
        _rnd.setstate(state)

    def _draw_dust(self, p, w, h, dust_type="gold_dust"):
        """Рисуем медленно плавающие пылинки (золотые или голубые)."""
        if not hasattr(self, '_gold_dust_phase'):
            self._gold_dust_phase = 0.0
        import math as _m
        # Классические темы берут цвет из fire_core, остальные — дефолт
        cat = self._current_theme.get("category", "")
        if cat == "classic":
            color = self._current_theme.get("colors", {}).get("fire_core", (230, 195, 60))
        elif dust_type == "blue_dust":
            color = (80, 160, 255)
        else:
            color = (230, 195, 60)
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(16):
            phase = self._gold_dust_phase + i * 1.1
            dx = _m.sin(phase * 0.3 + i * 0.8) * 18
            dy = _m.cos(phase * 0.2 + i * 0.5) * 14
            bx = 20 + (i * 37) % max(1, w - 40)
            by = 30 + (i * 59) % max(1, h - 60)
            x = bx + dx
            y = by + dy
            sz = 3 + (i % 4)
            alpha = int(55 + 40 * _m.sin(phase * 0.5 + i * 1.7))
            p.setBrush(QColor(color[0], color[1], color[2], alpha))
            p.drawEllipse(int(x), int(y), sz, sz)

    def _draw_hex_grid(self, p, w, h):
        """Фрактальная тема: одна сетка → приближается/крутится → уходит за кадр,
        тем временем на заднем плане появляется новая мелкая, растёт, и цикл повторяется."""
        import math as _m
        from PyQt6.QtGui import QPainterPath
        if not hasattr(self, '_hex_layers'):
            # Начинаем с одной видимой сетки на базовом масштабе
            self._hex_layers = [
                {"scale": 1.0, "rot": 0.0, "rot_speed": 0.0,
                 "state": "idle", "wait": random.randint(25, 50)},
            ]
        cx, cy = w / 2, h / 2
        base_sp = 28

        # Сортируем — дальние (мелкие) рисуем первыми
        sorted_layers = sorted(self._hex_layers, key=lambda l: l["scale"])

        for layer in sorted_layers:
            sc = layer["scale"]
            rot = layer["rot"]
            if sc < 0.06:
                continue

            # Альфа: approaching — постепенное появление через age;
            # zooming — fade-out при огромном масштабе
            age = layer.get("age", 999)
            base_alpha = 110  # яркая, не полупрозрачная
            if layer["state"] == "approaching":
                # Плавный fade-in за ~3с (37 тиков)
                alpha = int(base_alpha * min(1.0, age / 37.0))
            elif sc > 3.0:
                alpha = int(base_alpha * max(0.0, (12.0 - sc) / 9.0))
            else:
                alpha = base_alpha
            if alpha <= 0:
                continue

            sp = base_sp * sc
            if sp < 3:
                continue

            p.save()
            p.translate(cx, cy)
            p.rotate(_m.degrees(rot))
            p.translate(-cx, -cy)

            pen_w = max(1.0, 1.8 * min(sc, 2.5))
            # Цвет сетки из темы
            gc = self._current_theme.get("colors", {}).get("fire_core", (255, 0, 85))
            p.setPen(QPen(QColor(gc[0], gc[1], gc[2], alpha), pen_w))
            p.setBrush(Qt.BrushStyle.NoBrush)

            hex_h = sp * 2
            hex_w = _m.sqrt(3) * sp
            if hex_w < 6 or hex_h < 6:
                p.restore()
                continue
            diag = _m.sqrt(w * w + h * h) / 2 + sp * 2
            cols = int(diag * 2 / hex_w) + 4
            rows = int(diag * 2 / (hex_h * 0.75)) + 4
            # Лимит на количество ячеек для ФПС
            max_cells = 950
            if cols * rows > max_cells:
                ratio = _m.sqrt(max_cells / (cols * rows))
                cols = int(cols * ratio)
                rows = int(rows * ratio)

            for row in range(-rows // 2, rows // 2 + 1):
                for col in range(-cols // 2, cols // 2 + 1):
                    hx = cx + col * hex_w + (hex_w / 2 if row % 2 else 0)
                    hy = cy + row * hex_h * 0.75
                    path = QPainterPath()
                    for k in range(6):
                        angle = _m.pi / 3 * k + _m.pi / 6
                        px = hx + sp * _m.cos(angle)
                        py = hy + sp * _m.sin(angle)
                        if k == 0:
                            path.moveTo(px, py)
                        else:
                            path.lineTo(px, py)
                    path.closeSubpath()
                    p.drawPath(path)

            p.restore()

    def _draw_hex_dust(self, p, w, h):
        """Фрактальная тема: 6 шестиугольных/пятиугольных пылинок."""
        import math as _m
        if not hasattr(self, '_hex_dust_particles'):
            self._hex_dust_particles = []
            for i in range(6):
                sides = random.choice([5, 6])
                self._hex_dust_particles.append({
                    "x": random.uniform(20, w - 20),
                    "y": random.uniform(20, h - 20),
                    "vx": random.uniform(-2.5, 2.5),
                    "vy": random.uniform(-2.5, 2.5),
                    "rot": random.uniform(0, _m.pi * 2),
                    "rot_speed": random.uniform(-0.04, 0.04),
                    "size": random.uniform(5, 9),
                    "sides": sides,
                    "alpha_phase": random.uniform(0, _m.pi * 2),
                })
        phase = getattr(self, '_gold_dust_phase', 0.0)
        dc = self._current_theme.get("colors", {}).get("fire_core", (255, 0, 85))
        dr, dg, db = dc[0], dc[1], dc[2]
        for d in self._hex_dust_particles:
            al = int(80 + 50 * _m.sin(phase * 0.4 + d["alpha_phase"]))
            sz = d["size"]
            sides = d["sides"]
            rot = d["rot"]
            from PyQt6.QtGui import QPainterPath, QRadialGradient
            # Свечение
            grad = QRadialGradient(d["x"], d["y"], sz * 2.5)
            grad.setColorAt(0, QColor(dr, dg, db, al))
            grad.setColorAt(0.5, QColor(dr, dg, db, al // 3))
            grad.setColorAt(1, QColor(dr, dg, db, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(grad)
            p.drawEllipse(QPointF(d["x"], d["y"]), sz * 2.5, sz * 2.5)
            # Форма
            path = QPainterPath()
            for k in range(sides):
                angle = 2 * _m.pi / sides * k + rot
                px = d["x"] + sz * _m.cos(angle)
                py = d["y"] + sz * _m.sin(angle)
                if k == 0:
                    path.moveTo(px, py)
                else:
                    path.lineTo(px, py)
            path.closeSubpath()
            p.setPen(QPen(QColor(dr, dg, db, min(255, al + 60)), 1.5))
            p.setBrush(QColor(dr, dg, db, al // 2))
            p.drawPath(path)

    def _draw_bubbles(self, p, w, h):
        """Современная тема: пузырьки летят снизу вверх, покачиваясь."""
        import math as _m
        if not hasattr(self, '_bubbles'):
            self._bubbles = []
            for _ in range(18):
                self._bubbles.append({
                    "x": random.uniform(10, w - 10),
                    "y": random.uniform(0, h),
                    "size": random.uniform(4, 22),
                    "speed": random.uniform(0.3, 1.2),
                    "phase": random.uniform(0, _m.pi * 2),
                    "sway": random.uniform(15, 40),
                    "sway_speed": random.uniform(0.01, 0.03),
                })
        fx_o = self._fx_opacity / 100.0
        for b in self._bubbles:
            b["y"] -= b["speed"]
            b["phase"] += b["sway_speed"]
            if b["y"] < -b["size"] * 2:
                b["y"] = h + b["size"]
                b["x"] = random.uniform(10, w - 10)
                b["size"] = random.uniform(4, 22)
            sx = b["x"] + _m.sin(b["phase"]) * b["sway"]
            sz = b["size"]
            al = int(120 * fx_o)
            # Свечение
            sg = QRadialGradient(sx, b["y"], sz * 1.5)
            sg.setColorAt(0, QColor(180, 220, 255, al // 3))
            sg.setColorAt(1, QColor(180, 220, 255, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(sg))
            p.drawEllipse(QPointF(sx, b["y"]), sz * 1.5, sz * 1.5)
            # Контур пузырька
            p.setPen(QPen(QColor(200, 230, 255, al), 1.2))
            p.setBrush(QColor(180, 220, 255, al // 4))
            p.drawEllipse(QPointF(sx, b["y"]), sz, sz)
            # Блик
            blik_sz = sz * 0.3
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, int(160 * fx_o)))
            p.drawEllipse(QPointF(sx - sz * 0.3, b["y"] - sz * 0.3), blik_sz, blik_sz)

    def _draw_counter_bg_image(self, p):
        """Рисуем медиа-плеер за счётчиком. Число внутри тёмного окошка дисплея."""
        if not hasattr(self, '_counter_bg_pixmap'):
            import os
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
            name = self._current_theme.get("counter_bg_image", "")
            self._counter_bg_pixmap = QPixmap(os.path.join(base, name))
        pm = self._counter_bg_pixmap
        if pm.isNull():
            return
        # Позиция числа (центр counter_label)
        label_pos = self.counter_label.mapTo(self, QPoint(0, 0))
        num_cx = label_pos.x() + self.counter_label.width() / 2
        num_cy = label_pos.y() + self.counter_label.height() / 2
        # Дисплей 476x426 (после уменьшения в 2.25x)
        # Тёмное окошко: центр ~(236, 133) в масштабе дисплея 476x426
        # Т.е. окошко на 47% от верха, по центру горизонтально
        # При target_h=198 (165*1.2): масштаб от 426 = 198/426 = 0.465
        # Окошко центр в финальном масштабе: (236*0.465, 133*0.465) = (110, 62)
        # Центр дисплея в финальном масштабе: (238*0.465, 213*0.465) = (111, 99)
        # Смещение окошка от центра: dx=-1, dy=-37
        target_h = int(198 * 1.11)  # 198 * 1.11 = 220 (+11%)
        scale_factor = target_h / max(1, pm.height())
        target_w = int(pm.width() * scale_factor)
        scaled = pm.scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        # Окошко смещено от центра дисплея на (dx=-1, dy=-37) при текущем масштабе
        window_offset_x = -1
        window_offset_y = -37
        # Дисплей позиционируется так, чтобы окошко = число
        disp_cx = num_cx - window_offset_x
        disp_cy = num_cy - window_offset_y
        dx = int(disp_cx - scaled.width() / 2) + 34  # +34px правее
        dy = int(disp_cy - scaled.height() / 2) - 23  # дисплей на 23px выше
        fx_o = self._fx_opacity / 100.0
        old_opa = p.opacity()
        p.setOpacity(fx_o)
        p.drawPixmap(dx, dy, scaled)
        p.setOpacity(old_opa)

    def _draw_bg_images(self, p, w, h):
        """Рисуем плавающие/вращающиеся картинки (ku/kuu) на фоне."""
        cache_key = '_bg_images_pixmaps'
        if not hasattr(self, cache_key):
            import os
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
            names = self._current_theme.get("bg_images", [])
            pms = [QPixmap(os.path.join(base, n)) for n in names]
            setattr(self, cache_key, [pm for pm in pms if not pm.isNull()])
        pixmaps = getattr(self, cache_key)
        if not pixmaps:
            return
        import math as _m
        from PyQt6.QtGui import QTransform
        phase = getattr(self, '_gold_dust_phase', 0.0)
        fx_o = self._fx_opacity / 100.0
        import random as _rnd
        state = _rnd.getstate()
        _rnd.seed(77)
        for i in range(8):
            pm = pixmaps[i % len(pixmaps)]
            bx = _rnd.randint(15, max(16, w - 60))
            by = _rnd.randint(15, max(16, h - 60))
            sz = _rnd.randint(28, 50)
            base_alpha = _rnd.randint(190, 255) / 255.0
            sp = phase + i * 1.5
            dx = _m.sin(sp * 0.22 + i * 1.1) * 16
            dy = _m.cos(sp * 0.16 + i * 0.7) * 12
            angle = _m.fmod(sp * 6 + i * 45, 360)
            flicker = 0.7 + 0.3 * _m.sin(sp * 0.35 + i * 1.9)
            scaled = pm.scaled(sz, sz, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
            tf = QTransform()
            tf.translate(sz / 2, sz / 2)
            tf.rotate(angle)
            tf.translate(-sz / 2, -sz / 2)
            rotated = scaled.transformed(tf, Qt.TransformationMode.SmoothTransformation)
            ox = (rotated.width() - sz) // 2
            oy = (rotated.height() - sz) // 2
            p.setOpacity(base_alpha * flicker * fx_o)
            p.drawPixmap(int(bx + dx) - ox, int(by + dy) - oy, rotated)
        p.setOpacity(fx_o)
        _rnd.setstate(state)

    def _draw_center_image(self, p, w, h):
        """Рисуем большую картинку по центру интерфейса."""
        if not hasattr(self, '_center_pixmap'):
            import os
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
            name = self._current_theme.get("bg_center_image", "")
            self._center_pixmap = QPixmap(os.path.join(base, name))
        pm = self._center_pixmap
        if pm.isNull():
            return
        sz = min(w, h) * 0.45
        scaled = pm.scaled(int(sz), int(sz), Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        x = (w - scaled.width()) // 2
        y = (h - scaled.height()) // 2
        fx_o = self._fx_opacity / 100.0
        p.setOpacity(0.15 * fx_o)
        p.drawPixmap(x, y, scaled)
        p.setOpacity(fx_o)

    def _draw_bg_image_file(self, p, w, h, cr):
        """Рисуем фоновую картинку (sc.jpg) масштабированную на весь интерфейс."""
        if not hasattr(self, '_bg_file_pixmap'):
            import os
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
            name = self._current_theme.get("bg_image_file", "")
            self._bg_file_pixmap = QPixmap(os.path.join(base, name))
        pm = self._bg_file_pixmap
        if pm.isNull():
            return
        scaled = pm.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        from PyQt6.QtGui import QPainterPath
        clip = QPainterPath()
        clip.addRoundedRect(0.0, 0.0, float(w), float(h), float(cr), float(cr))
        p.save()
        p.setClipPath(clip)
        p.drawPixmap(0, 0, scaled)
        p.restore()

    def _handle_spiral_click(self, e):
        """Клик по центру воронки: мини-взрыв + счётчик кликов → звезда."""
        local = e.position()
        lx, ly = local.x(), local.y()
        # Мини-взрыв
        burst = {"particles": []}
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            burst["particles"].append({
                "x": lx, "y": ly,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "alpha": 255,
                "size": random.uniform(2, 5),
            })
        if not hasattr(self, '_spiral_bursts'):
            self._spiral_bursts = []
        self._spiral_bursts.append(burst)
        # Счётчик кликов
        if not hasattr(self, '_spiral_click_count'):
            self._spiral_click_count = 0
        self._spiral_click_count += 1
        # 3-5 кликов → запускаем звезду
        threshold = getattr(self, '_spiral_click_threshold', random.randint(3, 5))
        if not hasattr(self, '_spiral_click_threshold'):
            self._spiral_click_threshold = threshold
        if self._spiral_click_count >= self._spiral_click_threshold:
            self._spiral_click_count = 0
            self._spiral_click_threshold = random.randint(3, 5)
            # Запуск звезды
            g_pos = e.globalPosition().toPoint()
            star_type = 1 if getattr(self, '_spiral_color_target', 0.0) == 0.0 else 2
            self._star_overlay.launch(g_pos.x(), g_pos.y(), star_type)

    def _on_star_exploded(self):
        """Звезда схлопнулась — переключаем цвет темы."""
        if not hasattr(self, '_spiral_color_target'):
            self._spiral_color_target = 0.0
        if self._spiral_color_target == 0.0:
            self._spiral_color_target = 1.0  # → фиолетовая
        else:
            self._spiral_color_target = 0.0  # → красная

    def _draw_bottomless_effects(self, p, w, h, rect):
        """Бездонная тема: чёрно-красная спираль, чёрные частицы, малиновый шлейф."""
        from PyQt6.QtGui import QPainterPath
        phase = getattr(self, '_spiral_phase', 0.0)
        cx, cy = w / 2, h / 2
        # Скорость зависит от расстояния курсора до центра (mapFromGlobal)
        cursor_dist = getattr(self, '_spiral_cursor_dist', 999.0)
        max_dist = math.sqrt(w * w + h * h) / 2
        proximity = max(0.0, 1.0 - cursor_dist / max_dist)  # 0=далеко, 1=в центре
        cr = 12

        # ── Фон: тёмный градиент ──
        # (уже нарисован в paintEvent)

        # ── Чёрная рамка-свечение по краям ──
        edge_grad = QLinearGradient(0, 0, 30, 0)
        edge_al = int(80 + 60 * proximity)
        edge_grad.setColorAt(0, QColor(0, 0, 0, edge_al))
        edge_grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(edge_grad))
        p.drawRect(0, 0, 40, h)
        edge_grad2 = QLinearGradient(w, 0, w - 30, 0)
        edge_grad2.setColorAt(0, QColor(0, 0, 0, edge_al))
        edge_grad2.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(edge_grad2))
        p.drawRect(w - 40, 0, 40, h)
        edge_top = QLinearGradient(0, 0, 0, 30)
        edge_top.setColorAt(0, QColor(0, 0, 0, edge_al))
        edge_top.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(edge_top))
        p.drawRect(0, 0, w, 40)
        edge_bot = QLinearGradient(0, h, 0, h - 30)
        edge_bot.setColorAt(0, QColor(0, 0, 0, edge_al))
        edge_bot.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(edge_bot))
        p.drawRect(0, h - 40, w, 40)

        # ── Спираль ──
        n_arms = 2  # 2 рукава
        n_points = 120
        max_r = max(w, h) * 0.55
        # Цветовой сдвиг: 0=красная, 1=фиолетово-синяя
        cs = getattr(self, '_spiral_color_shift', 0.0)
        # Красный: (230,20,20) → Сине-фиолетовый: (80,30,230)
        sr = int(230 * (1 - cs) + 80 * cs)
        sg_c = int(20 * (1 - cs) + 30 * cs)
        sb = int(20 * (1 - cs) + 230 * cs)
        for arm in range(n_arms):
            arm_offset = arm * math.pi
            for layer in range(3):  # 3 слоя: тень, основа, блик
                path = QPainterPath()
                first = True
                for i in range(n_points):
                    t = i / n_points
                    angle = t * math.pi * 5 + phase + arm_offset
                    r = t * max_r
                    px = cx + math.cos(angle) * r
                    py = cy + math.sin(angle) * r
                    if first:
                        path.moveTo(px, py)
                        first = False
                    else:
                        path.lineTo(px, py)
                if layer == 0:
                    # Тень — ×4.75
                    thickness = 85 + 47 * proximity
                    p.setPen(QPen(QColor(0, 0, 0, 60), thickness))
                elif layer == 1:
                    bright = proximity
                    r_ = int(sr + 80 * bright)
                    b_ = int(sb + 40 * bright)
                    thickness = 38 + 28 * proximity
                    p.setPen(QPen(QColor(min(255, r_), sg_c, min(255, b_), 180), thickness))
                else:
                    r_ = int(sr + 60 + 55 * proximity)
                    b_ = int(sb + 40 + 30 * proximity)
                    thickness = 9.5 + 9.5 * proximity
                    p.setPen(QPen(QColor(min(255, r_), 40, min(255, b_), 120), thickness))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(path)

        # ── Центральное свечение (эпицентр воронки) ──
        glow_r = 40 + 30 * proximity
        glow_al = int(50 + 80 * proximity)
        glow = QRadialGradient(cx, cy, glow_r)
        glow.setColorAt(0, QColor(sr, 0, sb, glow_al))
        glow.setColorAt(0.5, QColor(sr // 2, 0, sb // 2, glow_al // 2))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        # ── Малиновый шарик света в центре ──
        spiral_thickness = 38 + 28 * proximity
        orb_r = spiral_thickness * 1.1 / 2 * 2  # ×4 мощнее (×2 радиус = ×4 площадь)
        orb_pulse = 0.8 + 0.2 * math.sin(phase * 3.0)
        orb_al = min(255, int((255 + 0 * proximity) * orb_pulse))
        # Внешнее свечение (большое, мягкое)
        outer_r = orb_r * 3.0
        outer = QRadialGradient(cx, cy, outer_r)
        outer.setColorAt(0, QColor(220, 20, 60, orb_al // 2))
        outer.setColorAt(0.5, QColor(160, 0, 40, orb_al // 4))
        outer.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(outer))
        p.drawEllipse(QPointF(cx, cy), outer_r, outer_r)
        # Ядро (яркое)
        orb = QRadialGradient(cx, cy, orb_r)
        orb.setColorAt(0, QColor(255, 240, 245, min(255, orb_al)))
        orb.setColorAt(0.25, QColor(255, 60, 120, orb_al))
        orb.setColorAt(0.6, QColor(200, 15, 60, orb_al * 2 // 3))
        orb.setColorAt(1, QColor(120, 0, 30, 0))
        p.setBrush(QBrush(orb))
        p.drawEllipse(QPointF(cx, cy), orb_r, orb_r)

        # ── Чёрные частицы (засасываются с краёв) ──
        for dp in getattr(self, '_spiral_particles', []):
            al = dp["alpha"]
            if al <= 0:
                continue
            sz = dp["size"]
            grad = QRadialGradient(dp["x"], dp["y"], sz * 2.5)
            grad.setColorAt(0, QColor(10, 0, 0, al))
            grad.setColorAt(0.5, QColor(0, 0, 0, al // 2))
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(grad))
            p.drawEllipse(QPointF(dp["x"], dp["y"]), sz * 2.5, sz * 2.5)

        # ── Малиновый шлейф курсора (при близости к центру) ──
        for tp in getattr(self, '_spiral_trail', []):
            al = tp["alpha"]
            if al <= 0:
                continue
            sz = tp["size"]
            grad = QRadialGradient(tp["x"], tp["y"], sz * 2)
            grad.setColorAt(0, QColor(200, 20, 60, al))
            grad.setColorAt(0.5, QColor(150, 0, 30, al // 2))
            grad.setColorAt(1, QColor(100, 0, 20, 0))
            p.setBrush(QBrush(grad))
            p.drawEllipse(QPointF(tp["x"], tp["y"]), sz * 2, sz * 2)

        # ── Мини-взрывы от кликов ──
        for bst in getattr(self, '_spiral_bursts', []):
            for bp in bst.get("particles", []):
                al = bp["alpha"]
                if al <= 0:
                    continue
                sz = bp["size"]
                grad = QRadialGradient(bp["x"], bp["y"], sz * 2)
                grad.setColorAt(0, QColor(220, 30, 60, al))
                grad.setColorAt(0.5, QColor(160, 10, 30, al // 2))
                grad.setColorAt(1, QColor(0, 0, 0, 0))
                p.setBrush(QBrush(grad))
                p.drawEllipse(QPointF(bp["x"], bp["y"]), sz * 2, sz * 2)

    def _draw_ominous_effects(self, p, w, h, a):
        """Зловещая тема: чёрные пылинки, дым снизу, вращающиеся глаза, фог."""
        phase = getattr(self, '_gold_dust_phase', 0.0)

        # ── Чёрные дымные пылинки (плавающие слева-направо и справа-налево) ──
        if not hasattr(self, '_ominous_dust'):
            self._ominous_dust = []
            for i in range(40):
                self._ominous_dust.append({
                    "x": random.uniform(0, w),
                    "y": random.uniform(0, h),
                    "vx": random.choice([-1, 1]) * random.uniform(0.3, 1.5),
                    "size": random.randint(4, 12),
                    "alpha_base": random.randint(25, 65),
                })
        for d in self._ominous_dust:
            d["x"] += d["vx"]
            if d["x"] > w + 10:
                d["x"] = -10
            elif d["x"] < -10:
                d["x"] = w + 10
            da = int(d["alpha_base"] + 15 * math.sin(phase * 0.3 + d["y"] * 0.01))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(10, 10, 15, da))
            p.drawEllipse(int(d["x"]), int(d["y"]), d["size"], d["size"])

        # ── Вращающиеся глаза вокруг счётчика ──
        if self._current_theme.get("orbiting_eyes"):
            self._draw_orbiting_eyes(p, w, h)

    def _draw_orbiting_eyes(self, p, w, h):
        """Рисуем глаза, вращающиеся вокруг числа счётчика."""
        if not hasattr(self, '_eye_pixmaps'):
            import os
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
            pm_open = QPixmap(os.path.join(base, "eye1.png"))
            pm_mid = QPixmap(os.path.join(base, "eye_mid.png"))
            pm_closed = QPixmap(os.path.join(base, "eye2.png"))
            self._eye_pixmaps = {
                "open": pm_open if not pm_open.isNull() else None,
                "mid": pm_mid if not pm_mid.isNull() else None,
                "closed": pm_closed if not pm_closed.isNull() else None,
            }
        if not hasattr(self, '_eye_states'):
            # 3 глаза по умолчанию, расстояние 120° друг от друга
            self._eye_states = []
            for i in range(3):
                self._eye_states.append({
                    "angle_offset": i * 120,  # градусы по кругу
                    "state": "open",           # open/mid/closed
                    "state_timer": random.uniform(12, 18),  # секунд в текущем состоянии
                    "elapsed": 0.0,
                    "vibrate": 0.0,            # амплитуда вибрации (0 = нет)
                })
        pms = self._eye_pixmaps
        if not pms.get("open"):
            return

        label_pos = self.counter_label.mapTo(self, QPoint(0, 0))
        cx = label_pos.x() + self.counter_label.width() / 2
        cy = label_pos.y() + self.counter_label.height() / 2
        orbit_r = 130  # радиус орбиты
        eye_size = 100  # размер глаза (×3)

        phase = getattr(self, '_gold_dust_phase', 0.0)
        orbit_speed = 12  # градусов в секунду → phase * 12 / 0.04 tick

        for eye in self._eye_states:
            state = eye["state"]
            vib = eye.get("vibrate", 0)

            # Выбираем пиксмап
            if state == "open":
                pm = pms["open"]
            elif state == "mid":
                pm = pms["mid"]
            else:
                pm = pms["closed"]
            if pm is None:
                continue

            # Позиция на орбите
            angle_deg = eye["angle_offset"] + phase * 12
            angle_rad = math.radians(angle_deg)
            ex = cx + math.cos(angle_rad) * orbit_r
            ey = cy + math.sin(angle_rad) * orbit_r

            # Вибрация
            if vib > 0:
                ex += random.uniform(-vib, vib)
                ey += random.uniform(-vib, vib)

            # Масштабируем глаз
            scaled = pm.scaled(eye_size, eye_size,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)

            # Повернуть светлой частью к центру: угол от глаза к центру
            rotation_angle = math.degrees(math.atan2(cy - ey, cx - ex)) - 90
            tf = QTransform()
            tf.translate(scaled.width() / 2, scaled.height() / 2)
            tf.rotate(rotation_angle)
            tf.translate(-scaled.width() / 2, -scaled.height() / 2)
            rotated = scaled.transformed(tf, Qt.TransformationMode.SmoothTransformation)

            ox = (rotated.width() - eye_size) // 2
            oy = (rotated.height() - eye_size) // 2
            p.drawPixmap(int(ex) - eye_size // 2 - ox,
                         int(ey) - eye_size // 2 - oy, rotated)

    def _draw_edge_glow(self, p, w, h):
        """Яркое свечение по краям интерфейса (с клиппингом по скруглённому прямоугольнику)."""
        eg = self._current_theme.get("edge_glow", (30, 100, 255))
        import math as _m
        from PyQt6.QtGui import QPainterPath
        phase = getattr(self, '_gold_dust_phase', 0.0)
        pulse = 0.6 + 0.4 * _m.sin(phase * 0.5)
        alpha = int(40 * pulse)
        glow_w = 25
        cr = 0 if self._current_theme.get("sharp_corners") else 12
        # Клиппинг по скруглённому rect чтобы свечение не вылезало за углы
        clip = QPainterPath()
        clip.addRoundedRect(0.0, 0.0, float(w), float(h), cr, cr)
        p.setClipPath(clip)
        p.setPen(Qt.PenStyle.NoPen)
        # Левый край
        gl = QLinearGradient(0, 0, glow_w, 0)
        gl.setColorAt(0, QColor(eg[0], eg[1], eg[2], alpha))
        gl.setColorAt(1, QColor(eg[0], eg[1], eg[2], 0))
        p.setBrush(QBrush(gl))
        p.drawRect(0, 0, glow_w, h)
        # Правый край
        gr = QLinearGradient(w, 0, w - glow_w, 0)
        gr.setColorAt(0, QColor(eg[0], eg[1], eg[2], alpha))
        gr.setColorAt(1, QColor(eg[0], eg[1], eg[2], 0))
        p.setBrush(QBrush(gr))
        p.drawRect(w - glow_w, 0, glow_w, h)
        # Верх
        gt = QLinearGradient(0, 0, 0, glow_w)
        gt.setColorAt(0, QColor(eg[0], eg[1], eg[2], alpha))
        gt.setColorAt(1, QColor(eg[0], eg[1], eg[2], 0))
        p.setBrush(QBrush(gt))
        p.drawRect(0, 0, w, glow_w)
        # Низ
        gb = QLinearGradient(0, h, 0, h - glow_w)
        gb.setColorAt(0, QColor(eg[0], eg[1], eg[2], alpha))
        gb.setColorAt(1, QColor(eg[0], eg[1], eg[2], 0))
        p.setBrush(QBrush(gb))
        p.drawRect(0, h - glow_w, w, glow_w)
        p.setClipping(False)

    def _draw_sun_rays(self, p, w, h):
        """Солнечные лучи и пылинки, вылетающие из числа счётчика."""
        if not hasattr(self, '_sun_particles'):
            self._sun_particles = []
        p.setPen(Qt.PenStyle.NoPen)
        colors = [
            (253, 192, 5),    # жёлтый
            (246, 131, 24),   # оранжевый
            (255, 220, 80),   # светло-жёлтый
            (255, 160, 40),   # тёплый оранж
        ]
        for sp in self._sun_particles:
            # Фаза 1: луч (ray)
            if sp["ray_alpha"] > 0:
                angle_rad = math.radians(sp["angle"])
                ray_len = sp["ray_len"]
                cx, cy = sp["ox"], sp["oy"]
                rx = cx + math.cos(angle_rad) * ray_len
                ry = cy + math.sin(angle_rad) * ray_len
                col = colors[sp["color_idx"] % len(colors)]
                ra = sp["ray_alpha"]
                # Свечение луча
                p.setPen(QPen(QColor(col[0], col[1], col[2], ra // 3), 5.0))
                p.drawLine(QPointF(cx, cy), QPointF(rx, ry))
                # Ядро луча
                p.setPen(QPen(QColor(255, 240, 200, ra), 2.0))
                p.drawLine(QPointF(cx, cy), QPointF(rx, ry))
            # Фаза 2: пылинка летит
            if sp["particle_alpha"] > 0:
                col = colors[sp["color_idx"] % len(colors)]
                pa = sp["particle_alpha"]
                sz = sp["size"]
                p.setPen(Qt.PenStyle.NoPen)
                # Свечение пылинки
                p.setBrush(QColor(col[0], col[1], col[2], pa // 3))
                p.drawEllipse(QPointF(sp["x"], sp["y"]), sz + 3, sz + 3)
                # Ядро пылинки
                p.setBrush(QColor(255, 240, 200, pa))
                p.drawEllipse(QPointF(sp["x"], sp["y"]), sz, sz)

    def _draw_pulsing_border(self, p, w, h):
        """Пульсирующая рамка: вспыхивает жёлтым, затухает к оранжевому. Клиппинг по скруглённым углам."""
        from PyQt6.QtGui import QPainterPath
        phase = getattr(self, '_gold_dust_phase', 0.0)
        # Пульсация между жёлтым (253,192,5) и оранжевым (246,131,24)
        pulse = 0.5 + 0.5 * math.sin(phase * 0.6)
        r = int(246 + (253 - 246) * pulse)
        g = int(131 + (192 - 131) * pulse)
        b = int(24 + (5 - 24) * pulse)
        alpha = int(30 + 50 * pulse)
        glow_w = 22
        p.save()
        # Клиппинг по скруглённому прямоугольнику окна
        clip = QPainterPath()
        clip.addRoundedRect(1.0, 1.0, float(w - 2), float(h - 2), 12, 12)
        p.setClipPath(clip)
        p.setPen(Qt.PenStyle.NoPen)
        # 4 стороны
        gl = QLinearGradient(0, 0, glow_w, 0)
        gl.setColorAt(0, QColor(r, g, b, alpha))
        gl.setColorAt(1, QColor(r, g, b, 0))
        p.setBrush(QBrush(gl))
        p.drawRect(0, 0, glow_w, h)
        gr = QLinearGradient(w, 0, w - glow_w, 0)
        gr.setColorAt(0, QColor(r, g, b, alpha))
        gr.setColorAt(1, QColor(r, g, b, 0))
        p.setBrush(QBrush(gr))
        p.drawRect(w - glow_w, 0, glow_w, h)
        gt = QLinearGradient(0, 0, 0, glow_w)
        gt.setColorAt(0, QColor(r, g, b, alpha))
        gt.setColorAt(1, QColor(r, g, b, 0))
        p.setBrush(QBrush(gt))
        p.drawRect(0, 0, w, glow_w)
        gb = QLinearGradient(0, h, 0, h - glow_w)
        gb.setColorAt(0, QColor(r, g, b, alpha))
        gb.setColorAt(1, QColor(r, g, b, 0))
        p.setBrush(QBrush(gb))
        p.drawRect(0, h - glow_w, w, glow_w)
        p.restore()

    def _draw_scanlines(self, p, w, h, bg_alpha):
        """Ретро-сканлайны: полосы 11px каждые 19px, резкие вспышки мерцания."""
        phase = getattr(self, '_gold_dust_phase', 0.0)
        line_h = 11
        gap = 19
        step = line_h + gap
        scroll = (phase * 6) % step
        # ── Мерцание: state machine ──
        if not hasattr(self, '_scan_flicker'):
            self._scan_flicker = {
                "base_alpha": 52,          # нормальная яркость
                "current_alpha": 52,
                "state": "idle",           # idle / flash_in / flash_hold / flash_out / cooldown
                "timer": 0.0,
                "cooldown": random.uniform(3.0, 10.0),  # пауза до следующего мерцания
                "target_alpha": 52,
                "flashes_left": 0,
                "brighten": True,
            }
        sf = self._scan_flicker
        dt = 0.08  # ~80ms тик
        if sf["state"] == "idle":
            sf["timer"] += dt
            if sf["timer"] >= sf["cooldown"]:
                # Начинаем серию вспышек
                sf["flashes_left"] = random.randint(1, 3)
                sf["brighten"] = random.choice([True, False])
                sf["target_alpha"] = int(sf["base_alpha"] * 1.5) if sf["brighten"] else int(sf["base_alpha"] * 0.5)
                sf["state"] = "flash_in"
                sf["timer"] = 0.0
        elif sf["state"] == "flash_in":
            # Резкий переход за 0.2с
            sf["timer"] += dt
            t = min(sf["timer"] / 0.2, 1.0)
            sf["current_alpha"] = int(sf["base_alpha"] + (sf["target_alpha"] - sf["base_alpha"]) * t)
            if t >= 1.0:
                sf["state"] = "flash_hold"
                sf["timer"] = 0.0
        elif sf["state"] == "flash_hold":
            # Держится 0.2с
            sf["timer"] += dt
            sf["current_alpha"] = sf["target_alpha"]
            if sf["timer"] >= 0.2:
                sf["state"] = "flash_out"
                sf["timer"] = 0.0
        elif sf["state"] == "flash_out":
            # Обратно за 0.2с
            sf["timer"] += dt
            t = min(sf["timer"] / 0.2, 1.0)
            sf["current_alpha"] = int(sf["target_alpha"] + (sf["base_alpha"] - sf["target_alpha"]) * t)
            if t >= 1.0:
                sf["current_alpha"] = sf["base_alpha"]
                sf["flashes_left"] -= 1
                if sf["flashes_left"] > 0:
                    # Ещё вспышка — снова flash_in
                    sf["brighten"] = random.choice([True, False])
                    sf["target_alpha"] = int(sf["base_alpha"] * 1.5) if sf["brighten"] else int(sf["base_alpha"] * 0.5)
                    sf["state"] = "flash_in"
                    sf["timer"] = 0.0
                else:
                    sf["state"] = "idle"
                    sf["timer"] = 0.0
                    sf["cooldown"] = random.uniform(3.0, 10.0)
        a = sf["current_alpha"]
        scan_color = QColor(0, 255, 0, a)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(scan_color)
        y = -step + scroll
        while y < h + step:
            p.drawRect(0, int(y), w, line_h)
            y += step
        # Рамки со всех сторон — непрозрачные зелёные
        border_color = QColor(0, 255, 0, 255)
        p.setBrush(border_color)
        p.drawRect(0, 0, line_h, h)
        p.drawRect(w - line_h, 0, line_h, h)
        p.drawRect(0, 0, w, line_h)
        p.drawRect(0, h - line_h, w, line_h)

    def _draw_binary_rain(self, p, w, h):
        """Одна цифра (0/1) падает сверху вниз, отскакивает от пола и стены, улетает за кадр, 8с пауза."""
        if not hasattr(self, '_bin_digit'):
            self._bin_digit = None
            self._bin_cooldown = 0.0  # секунды паузы
        dt = 0.08  # ~80ms тик
        # Пауза между циклами
        if self._bin_digit is None:
            self._bin_cooldown -= dt
            if self._bin_cooldown > 0:
                return
            # Спавн новой цифры сверху
            fall_time = random.uniform(4.0, 6.0)  # секунды до дна
            self._bin_digit = {
                "char": random.choice("01"),
                "x": float(random.randint(20, max(21, w - 60))),
                "y": 11.0,  # начинаем от нижнего края верхней рамки
                "vx": 0.0,
                "vy": h / (fall_time / dt),  # пикселей за тик чтобы долететь за fall_time
                "alpha": 200,
                "size": random.randint(28, 42),
                "bounces": 0,      # 0=падает, 1=отскочил от пола, 2=отскочил от стены → улетает
                "state": "fall",   # fall → bounce1 → bounce2 → flyaway
            }
            return
        d = self._bin_digit
        # Обновление позиции
        d["x"] += d["vx"]
        d["y"] += d["vy"]
        brd = 11  # толщина рамки
        char_h = d["size"]          # drawText рисует от baseline, y — это baseline
        char_w = int(d["size"] * 0.6)
        floor_y = h - brd           # нижний край рамки
        left_wall = brd             # правый край левой рамки
        right_wall = w - brd - char_w  # левый край правой рамки минус ширина символа
        if d["state"] == "fall":
            # Падает вертикально вниз — отскок когда baseline касается нижней рамки
            if d["y"] >= floor_y:
                d["y"] = floor_y
                d["state"] = "bounce1"
                d["vy"] = -abs(d["vy"]) * 1.4
                d["vx"] = random.choice([-1, 1]) * random.uniform(3.0, 6.0)
        elif d["state"] == "bounce1":
            # Летит после первого отскока, ждём удар о боковую рамку
            d["vy"] += 0.3  # гравитация
            if d["x"] <= left_wall or d["x"] >= right_wall:
                d["state"] = "bounce2"
                d["vx"] = -d["vx"] * 0.8  # отскок от стены
                d["vy"] = random.uniform(-8.0, -4.0)  # вверх
        elif d["state"] == "bounce2":
            # После отскока от стены — улетает из кадра
            d["vy"] += 0.2  # слабая гравитация
            # Проверяем вылет за пределы
            if d["y"] < -50 or d["y"] > h + 50 or d["x"] < -50 or d["x"] > w + 50:
                self._bin_digit = None
                self._bin_cooldown = 8.0  # 8 секунд паузы
                return
        # Рисование
        f = QFont("Consolas", d["size"])
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(0, 255, 0, d["alpha"]))
        p.drawText(int(d["x"]), int(d["y"]), d["char"])

    def _draw_pixel_counter(self, p, w, h):
        """Рендерим текст счётчика шрифтом Fixedsys (16px) и масштабируем вверх nearest-neighbor."""
        text = self.counter_label.text()
        if not text:
            return
        # Рендерим в маленький pixmap с Fixedsys
        font = QFont("Fixedsys", 20)
        font.setBold(True)
        from PyQt6.QtGui import QFontMetrics, QImage
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text) + 4
        th = fm.height() + 4
        if tw < 2 or th < 2:
            return
        img = QImage(tw, th, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(0, 0, 0, 0))
        tp = QPainter(img)
        tp.setFont(font)
        tp.setPen(QColor(0, 255, 0, 230))
        tp.drawText(2, fm.ascent() + 2, text)
        tp.end()
        # Масштабируем вверх с nearest-neighbor (пиксельный эффект)
        cl_w = self.counter_label.width()
        cl_h = self.counter_label.height()
        target_h = cl_h
        if target_h < 10:
            target_h = 180
        scale_factor = target_h / th
        target_w = int(tw * scale_factor)
        pm = QPixmap.fromImage(img).scaled(
            target_w, int(target_h),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation  # nearest-neighbor = пиксели!
        )
        # Рисуем по центру области счётчика (координаты в окне)
        label_pos = self.counter_label.mapTo(self, QPoint(0, 0))
        cx = label_pos.x() + (cl_w - pm.width()) // 2
        cy = label_pos.y() + (cl_h - pm.height()) // 2
        p.drawPixmap(cx, cy, pm)

    def _draw_counter_color_outline(self, p, outline_color):
        """Рисуем цветную обводку вокруг цифр счётчика."""
        text = self.counter_label.text()
        if not text:
            return
        label_pos = self.counter_label.mapTo(self, QPoint(0, 0))
        cx = label_pos.x() + self.counter_label.width() / 2
        cy = label_pos.y() + self.counter_label.height() / 2
        font_name = self._current_theme.get("counter_font", FONT_FAMILY_DISPLAY)
        scale = self._current_theme.get("counter_font_scale", 1.0)
        fpt = int(COUNTER_FONT_PT * scale)
        font = QFont(font_name, fpt)
        font.setBold(True)
        p.setFont(font)
        from PyQt6.QtGui import QFontMetrics
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text)
        tx = int(cx - tw / 2)
        ty = int(cy + fm.ascent() / 2 - fm.descent() / 2)
        # Обводка
        oc = QColor(outline_color)
        oc.setAlpha(220)
        p.setPen(oc)
        for dx in range(-3, 4, 2):
            for dy in range(-3, 4, 2):
                if dx == 0 and dy == 0:
                    continue
                p.drawText(tx + dx, ty + dy, text)
        # Основной текст поверх
        counter_color = self._current_theme.get("counter_color",
                        self._current_theme['colors']['primary'])
        p.setPen(QColor(counter_color))
        p.drawText(tx, ty, text)

    def _draw_outlined_counter(self, p, w, h):
        """Зловещая: белый счётчик с толстым чёрным контуром + покачивание."""
        text = self.counter_label.text()
        if not text:
            return
        label_pos = self.counter_label.mapTo(self, QPoint(0, 0))
        cx = label_pos.x() + self.counter_label.width() / 2
        cy = label_pos.y() + self.counter_label.height() / 2
        font_name = self._current_theme.get("counter_font", "Impact")
        scale = self._current_theme.get("counter_font_scale", 1.0)
        fpt = int(COUNTER_FONT_PT * scale)
        font = QFont(font_name, fpt)
        font.setBold(True)
        p.setFont(font)
        from PyQt6.QtGui import QFontMetrics
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text)
        # Покачивание
        wobble_phase = getattr(self, '_wobble_phase', 0.0)
        wx = math.sin(wobble_phase * 0.7) * 6 + math.sin(wobble_phase * 1.3) * 2
        wy = math.cos(wobble_phase * 0.5) * 4 + math.cos(wobble_phase * 1.1) * 1.5
        tx = int(cx - tw / 2 + wx)
        ty = int(cy + fm.ascent() / 2 - fm.descent() / 2 + wy)
        # Чёрный контур — рисуем текст со смещением по 8 направлениям
        outline_w = 4
        p.setPen(QColor(0, 0, 0, 240))
        for dx in range(-outline_w, outline_w + 1, 2):
            for dy in range(-outline_w, outline_w + 1, 2):
                if dx == 0 and dy == 0:
                    continue
                p.drawText(tx + dx, ty + dy, text)
        # Белый текст поверх
        p.setPen(QColor(255, 255, 255, 255))
        p.drawText(tx, ty, text)

    def _draw_charged_effects(self, p, w, h, rect):
        """Заряженная тема: зигзаги-молнии внутри окна, волны-дуги, вспышки."""
        phase = getattr(self, '_charged_phase', 0.0)
        intensity = getattr(self, '_charged_intensity', 0.0)
        is_awake = intensity > 0.01
        cr = 12
        from PyQt6.QtGui import QPainterPath

        # ── Светлая сетка-текстура фона (плывёт влево-вниз при активации) ──
        grid_al = int(12 + 10 * intensity)
        p.setPen(QColor(100, 160, 255, grid_al))
        sp = 24
        goff = getattr(self, '_grid_offset', [0.0, 0.0])
        ox = int(goff[0]) % sp
        oy = int(goff[1]) % sp
        for gx in range(-sp + ox, w + sp, sp):
            p.drawLine(gx, 0, gx, h)
        for gy in range(-sp + oy, h + sp, sp):
            p.drawLine(0, gy, w, gy)

        # Грозовая вспышка — жёлто-белая, долго остаётся
        flash_a = getattr(self, '_charged_flash', 0)
        if flash_a > 0:
            p.setPen(Qt.PenStyle.NoPen)
            # Сначала белая, потом переходит в жёлтую
            if flash_a > 120:
                p.setBrush(QColor(240, 240, 255, flash_a))
            else:
                p.setBrush(QColor(255, 255, 180, flash_a))
            p.drawRoundedRect(rect, cr, cr)
        # Красная вспышка при детекции
        det_a = getattr(self, '_charged_detect_flash', 0)
        if det_a > 0:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 40, 40, det_a))
            p.drawRoundedRect(rect, cr, cr)

        # ── Волны-дуги (голубые, медленные, быстро гаснут) ──
        for wav in getattr(self, '_charged_waves', []):
            radius = wav["radius"]
            al = wav["alpha"]
            if al <= 0:
                continue
            col = wav["color"]
            cx, cy = wav["cx"], wav["cy"]
            p.setPen(QPen(QColor(col[0], col[1], col[2], al), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), radius, radius)

        # ── Шлейф-призрак счётчика ──
        for g in getattr(self, '_counter_ghosts', []):
            al = g["alpha"]
            if al <= 0:
                continue
            # Находим центр counter_container в координатах окна
            cc = getattr(self, '_counter_container', None)
            if not cc:
                continue
            cc_pos = cc.mapTo(self, QPoint(0, 0))
            cx = cc_pos.x() + cc.width() / 2 + g["jx"]
            cy = cc_pos.y() + cc.height() / 2 + g["jy"]
            scale = self._current_theme.get("counter_font_scale", 1.0)
            fpt = int(COUNTER_FONT_PT * scale)
            cfont = self._current_theme.get("counter_font", "Consolas")
            font = QFont(cfont)
            font.setPixelSize(fpt)
            font.setWeight(QFont.Weight.Bold)
            p.setFont(font)
            p.setPen(QColor(140, 190, 255, al))
            tw = p.fontMetrics().horizontalAdvance(g["text"])
            th = p.fontMetrics().height()
            p.drawText(QPointF(cx - tw / 2, cy + th / 4), g["text"])

        # ── Белые пылинки ──
        for d in getattr(self, '_charged_dust', []):
            frac = d["life"] / d["max_life"] if d["max_life"] > 0 else 0
            # При затухании (выключение) — плавно гаснут; при активном — полная яркость
            if frac >= 0.99:
                al = 200  # активный режим, life == max
            elif frac > 0.85:
                al = int(200 * (1.0 - frac) / 0.15)
            else:
                al = int(200 * min(1.0, frac / 0.3))
            if al <= 0:
                continue
            sz = d["size"]
            grad = QRadialGradient(d["x"], d["y"], sz * 2.5)
            grad.setColorAt(0, QColor(255, 255, 255, al))
            grad.setColorAt(0.4, QColor(180, 210, 255, al // 2))
            grad.setColorAt(1, QColor(180, 210, 255, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(grad)
            p.drawEllipse(QPointF(d["x"], d["y"]), sz * 2.5, sz * 2.5)

        # ── Зигзаги-молнии по краям (ВНУТРИ окна) ──
        zph = getattr(self, '_zigzag_phase', 0.0)
        for side in ["left", "right"]:
            base_x = 30 if side == "left" else w - 30
            n_pts = 45
            side_off = 3.0 if side == "right" else 0
            brightness = 0.5 + 0.3 * math.sin(zph * 0.3 + side_off)
            # Плавная яркость: от 30% (покой) до 100% (актив)
            brightness *= 0.3 + 0.7 * intensity
            base_th = 1.8 + 1.5 * abs(math.sin(zph * 0.4 + side_off))
            if abs(math.sin(zph * 0.18 + side_off)) > 0.88:
                base_th = 4.0
            t = (math.sin(zph * 0.25 + side_off) + 1) * 0.5
            r_ = int(140 + 115 * t)
            g_ = int(180 + 75 * t)
            al = int(255 * brightness)
            if al <= 0:
                continue
            path = QPainterPath()
            direction = 1 if side == "left" else -1
            pts = []
            for i in range(n_pts + 1):
                y = h * i / n_pts
                seg_ph = zph * 0.7 + i * 0.55 + side_off
                raw = math.sin(seg_ph)
                angular = (1.0 if raw > 0 else -1.0) * min(1.0, abs(raw) * 4)
                amp = 8 + 14 * abs(math.sin(seg_ph * 0.25))
                if intensity > 0.5 and abs(math.sin(seg_ph * 0.1)) > 0.85:
                    amp = 18 + random.uniform(0, 8)
                offset = angular * amp * direction
                px = max(4, min(w - 4, base_x + offset))
                pts.append((px, y))
            # Сглаженный путь через quadTo: углы плавные, форма та же
            if pts:
                path.moveTo(pts[0][0], pts[0][1])
                for i in range(1, len(pts) - 1):
                    # Контрольная точка = текущая вершина, конец = середина до следующей
                    mx = (pts[i][0] + pts[i + 1][0]) / 2
                    my = (pts[i][1] + pts[i + 1][1]) / 2
                    path.quadTo(pts[i][0], pts[i][1], mx, my)
                # Последний сегмент — прямо до конца
                path.lineTo(pts[-1][0], pts[-1][1])
            # Свечение
            p.setPen(QPen(QColor(r_, g_, 255, al // 3), base_th * 3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
            p.setPen(QPen(QColor(r_, g_, 255, al), base_th))
            p.drawPath(path)
            p.setPen(QPen(QColor(255, 255, 255, al // 2), max(1, base_th * 0.3)))
            p.drawPath(path)

        # Искры курсора рисуются на отдельном fullscreen overlay (_spark_overlay)

    # ── Стиль ─────────────────────────────────────────────────
    def _apply_style(self):
        wa = self._widget_opacity / 100.0
        self.setStyleSheet(self._build_style(wa))

    def _build_style(self, wa):
        a = int(255 * wa)
        c = self._current_theme["colors"]
        primary = c["primary"]
        border = c["border"]
        # Определяем тип темы
        is_light = sum(c["bg_top"]) > 300
        is_villain = self._current_theme.get("shape") == "octagon"
        is_retro = self._current_theme.get("id") == "retro"
        is_sunset = self._current_theme.get("id") == "sunset"
        is_ominous = self._current_theme.get("id") == "ominous"
        if is_ominous:
            # Зловещая: серо-чёрная, мрачная палитра
            text_color = f"rgba(200,200,200,{a})"
            btn_bg_top = f"rgba(30,30,35,{int(220*wa)})"
            btn_bg_bot = f"rgba(18,18,22,{int(200*wa)})"
            btn_hover_top = f"rgba(45,45,50,{int(240*wa)})"
            btn_hover_bot = f"rgba(30,30,35,{int(220*wa)})"
            btn_pressed = f"rgba(60,60,65,{int(250*wa)})"
            mercy_bg_top = f"rgba(25,25,30,{int(220*wa)})"
            mercy_bg_bot = f"rgba(15,15,20,{int(200*wa)})"
            mercy_hover = f"rgba(35,35,40,{int(240*wa)})"
            panic_bg_top = f"rgba(80,20,20,{int(240*wa)})"
            panic_bg_bot = f"rgba(45,10,10,{int(220*wa)})"
            panic_hover = f"rgba(110,30,30,{int(255*wa)})"
            tab_bg = f"rgba(22,22,28,{int(200*wa)})"
            tab_sel_bg = f"rgba(35,35,42,{int(220*wa)})"
            pane_bg = f"rgba(16,16,22,{int(170*wa)})"
            prog_bg = f"rgba(12,12,16,{int(150*wa)})"
            table_bg = f"rgba(18,18,24,{int(150*wa)})"
            table_color = f"rgba(180,180,180,{a})"
            hdr_bg = f"rgba(28,28,34,{int(200*wa)})"
            gridline = "#2a2a30"
            chk_color = f"rgba(180,180,180,{a})"
            slider_groove = "#2a2a30"
            slider_from = "#666666"
            slider_to = "#333333"
            slider_border = "#555555"
            btn_hover_color = f"rgba(220,220,220,{a})"
            mercy_border = f"rgba(80,80,90,{a})"
            mercy_color = f"rgba(130,130,140,{a})"
            mercy_hover_border = f"rgba(120,120,130,{a})"
        elif self._current_theme.get("spiral_theme"):
            # Бездонная: чёрные кнопки с красным контуром
            text_color = f"rgba(200,60,60,{a})"
            btn_bg_top = f"rgba(10,2,2,{int(240*wa)})"
            btn_bg_bot = f"rgba(5,0,0,{int(220*wa)})"
            btn_hover_top = f"rgba(25,5,5,{int(250*wa)})"
            btn_hover_bot = f"rgba(15,2,2,{int(240*wa)})"
            btn_pressed = f"rgba(40,8,8,{int(255*wa)})"
            mercy_bg_top = f"rgba(8,0,0,{int(220*wa)})"
            mercy_bg_bot = f"rgba(4,0,0,{int(200*wa)})"
            mercy_hover = f"rgba(20,4,4,{int(240*wa)})"
            panic_bg_top = f"rgba(100,10,10,{int(240*wa)})"
            panic_bg_bot = f"rgba(60,5,5,{int(220*wa)})"
            panic_hover = f"rgba(140,20,20,{int(255*wa)})"
            tab_bg = f"rgba(8,2,2,{int(200*wa)})"
            tab_sel_bg = f"rgba(18,4,4,{int(220*wa)})"
            pane_bg = f"rgba(6,0,0,{int(170*wa)})"
            prog_bg = f"rgba(4,0,0,{int(150*wa)})"
            table_bg = f"rgba(8,2,2,{int(150*wa)})"
            table_color = f"rgba(180,60,60,{a})"
            hdr_bg = f"rgba(14,3,3,{int(200*wa)})"
            gridline = "#1a0505"
            chk_color = f"rgba(200,60,60,{a})"
            slider_groove = "#1a0505"
            slider_from = "#882222"
            slider_to = "#441111"
            slider_border = "#662222"
            btn_hover_color = f"rgba(255,80,80,{a})"
            mercy_border = f"rgba(100,20,20,{a})"
            mercy_color = f"rgba(160,40,40,{a})"
            mercy_hover_border = f"rgba(140,30,30,{a})"
        elif self._current_theme.get("id") == "charged":
            # Заряженная: бело-голубая грозовая палитра
            text_color = f"rgba(230,240,255,{a})"
            btn_bg_top = f"rgba(25,35,65,{int(220*wa)})"
            btn_bg_bot = f"rgba(15,20,45,{int(200*wa)})"
            btn_hover_top = f"rgba(40,55,90,{int(240*wa)})"
            btn_hover_bot = f"rgba(25,35,65,{int(220*wa)})"
            btn_pressed = f"rgba(60,80,130,{int(250*wa)})"
            mercy_bg_top = f"rgba(20,30,55,{int(220*wa)})"
            mercy_bg_bot = f"rgba(12,18,40,{int(200*wa)})"
            mercy_hover = f"rgba(35,50,80,{int(240*wa)})"
            panic_bg_top = f"rgba(80,30,30,{int(240*wa)})"
            panic_bg_bot = f"rgba(45,15,15,{int(220*wa)})"
            panic_hover = f"rgba(120,40,40,{int(255*wa)})"
            tab_bg = f"rgba(18,25,50,{int(200*wa)})"
            tab_sel_bg = f"rgba(30,40,70,{int(220*wa)})"
            pane_bg = f"rgba(14,20,42,{int(170*wa)})"
            prog_bg = f"rgba(12,16,35,{int(150*wa)})"
            table_bg = f"rgba(16,22,45,{int(150*wa)})"
            table_color = f"rgba(200,220,255,{a})"
            hdr_bg = f"rgba(22,30,55,{int(200*wa)})"
            gridline = "#1a2a50"
            chk_color = f"rgba(200,220,255,{a})"
            slider_groove = "#1a2a50"
            slider_from = "#88bbff"
            slider_to = "#4466aa"
            slider_border = "#6699dd"
            btn_hover_color = f"rgba(180,220,255,{a})"
            mercy_border = f"rgba(80,120,200,{a})"
            mercy_color = f"rgba(100,150,220,{a})"
            mercy_hover_border = f"rgba(120,170,240,{a})"
        elif is_retro:
            # Ретро-терминальная: зелёное на чёрном
            text_color = f"rgba(0,255,0,{a})"
            btn_bg_top = f"rgba(0,30,0,{int(220*wa)})"
            btn_bg_bot = f"rgba(0,15,0,{int(200*wa)})"
            btn_hover_top = f"rgba(0,50,0,{int(240*wa)})"
            btn_hover_bot = f"rgba(0,30,0,{int(220*wa)})"
            btn_pressed = f"rgba(0,70,0,{int(250*wa)})"
            mercy_bg_top = f"rgba(0,25,0,{int(220*wa)})"
            mercy_bg_bot = f"rgba(0,12,0,{int(200*wa)})"
            mercy_hover = f"rgba(0,40,0,{int(240*wa)})"
            panic_bg_top = f"rgba(80,0,0,{int(240*wa)})"
            panic_bg_bot = f"rgba(40,0,0,{int(220*wa)})"
            panic_hover = f"rgba(120,0,0,{int(255*wa)})"
            tab_bg = f"rgba(0,18,0,{int(200*wa)})"
            tab_sel_bg = f"rgba(0,35,0,{int(220*wa)})"
            pane_bg = f"rgba(0,10,0,{int(170*wa)})"
            prog_bg = f"rgba(0,8,0,{int(150*wa)})"
            table_bg = f"rgba(0,12,0,{int(150*wa)})"
            table_color = f"rgba(0,220,0,{a})"
            hdr_bg = f"rgba(0,22,0,{int(200*wa)})"
            gridline = "#003300"
            chk_color = f"rgba(0,220,0,{a})"
            slider_groove = "#003300"
            slider_from = "#00ff00"
            slider_to = "#00aa00"
            slider_border = "#00ff00"
            btn_hover_color = f"rgba(0,255,0,{a})"
            mercy_border = f"rgba(0,180,0,{a})"
            mercy_color = f"rgba(0,200,0,{a})"
            mercy_hover_border = f"rgba(0,255,0,{a})"
        elif is_sunset:
            # Закатная тема: фиолетово-оранжевые тона
            text_color = f"rgba(255,230,200,{a})"
            btn_bg_top = f"rgba(60,35,90,{int(220*wa)})"
            btn_bg_bot = f"rgba(40,20,65,{int(200*wa)})"
            btn_hover_top = f"rgba(80,45,110,{int(240*wa)})"
            btn_hover_bot = f"rgba(55,30,80,{int(220*wa)})"
            btn_pressed = f"rgba(178,46,55,{int(250*wa)})"
            mercy_bg_top = f"rgba(30,40,70,{int(220*wa)})"
            mercy_bg_bot = f"rgba(20,25,55,{int(200*wa)})"
            mercy_hover = f"rgba(45,55,90,{int(240*wa)})"
            panic_bg_top = f"rgba(178,46,55,{int(240*wa)})"
            panic_bg_bot = f"rgba(120,25,35,{int(220*wa)})"
            panic_hover = f"rgba(220,60,60,{int(255*wa)})"
            tab_bg = f"rgba(45,25,70,{int(200*wa)})"
            tab_sel_bg = f"rgba(65,40,95,{int(220*wa)})"
            pane_bg = f"rgba(35,20,60,{int(170*wa)})"
            prog_bg = f"rgba(30,15,50,{int(150*wa)})"
            table_bg = f"rgba(35,20,60,{int(150*wa)})"
            table_color = f"rgba(255,220,180,{a})"
            hdr_bg = f"rgba(50,30,75,{int(200*wa)})"
            gridline = "#4a2a6a"
            chk_color = f"rgba(255,220,180,{a})"
            slider_groove = "#4a2a6a"
            slider_from = "#F68318"
            slider_to = "#B22E37"
            slider_border = "#FDC005"
            btn_hover_color = f"rgba(253,192,5,{a})"
            mercy_border = f"rgba(80,100,180,{a})"
            mercy_color = f"rgba(100,130,200,{a})"
            mercy_hover_border = f"rgba(120,150,220,{a})"
        elif is_villain:
            # Злодейская тема: зелёно-багряная палитра, полотняный вид
            text_color = f"rgba(200,195,180,{a})"
            btn_bg_top = f"rgba(55,70,55,{int(220*wa)})"
            btn_bg_bot = f"rgba(35,45,35,{int(200*wa)})"
            btn_hover_top = f"rgba(70,85,65,{int(240*wa)})"
            btn_hover_bot = f"rgba(50,60,45,{int(220*wa)})"
            btn_pressed = f"rgba(80,30,30,{int(250*wa)})"
            mercy_bg_top = f"rgba(30,50,35,{int(220*wa)})"
            mercy_bg_bot = f"rgba(20,35,25,{int(200*wa)})"
            mercy_hover = f"rgba(40,60,40,{int(240*wa)})"
            panic_bg_top = f"rgba(120,20,25,{int(240*wa)})"
            panic_bg_bot = f"rgba(65,15,20,{int(220*wa)})"
            panic_hover = f"rgba(150,30,35,{int(255*wa)})"
            tab_bg = f"rgba(40,50,40,{int(200*wa)})"
            tab_sel_bg = f"rgba(60,70,55,{int(220*wa)})"
            pane_bg = f"rgba(30,40,30,{int(170*wa)})"
            prog_bg = f"rgba(25,32,25,{int(150*wa)})"
            table_bg = f"rgba(30,40,30,{int(150*wa)})"
            table_color = f"rgba(190,185,170,{a})"
            hdr_bg = f"rgba(45,55,45,{int(200*wa)})"
            gridline = "#3b4a3b"
            chk_color = f"rgba(190,185,170,{a})"
            slider_groove = "#3b4a3b"
            slider_from = "#b81c28"
            slider_to = "#8a1a22"
            slider_border = "#b81c28"
            btn_hover_color = f"rgba(220,180,160,{a})"
            mercy_border = f"rgba(80,130,80,{a})"
            mercy_color = f"rgba(100,160,100,{a})"
            mercy_hover_border = f"rgba(120,180,120,{a})"
        elif self._current_theme.get("id") == "modern_windows":
            # Современная: кнопки-картинки, зелёные надписи
            text_color = f"rgba(0,255,80,{a})"
            btn_bg_top = "rgba(0,0,0,0)"
            btn_bg_bot = "rgba(0,0,0,0)"
            btn_hover_top = "rgba(255,255,255,20)"
            btn_hover_bot = "rgba(255,255,255,10)"
            btn_pressed = "rgba(255,255,255,40)"
            mercy_bg_top = "rgba(0,0,0,0)"
            mercy_bg_bot = "rgba(0,0,0,0)"
            mercy_hover = "rgba(255,255,255,20)"
            panic_bg_top = f"rgba(80,20,20,{int(240*wa)})"
            panic_bg_bot = f"rgba(45,10,10,{int(220*wa)})"
            panic_hover = f"rgba(120,30,30,{int(255*wa)})"
            tab_bg = f"rgba(0,30,80,{int(200*wa)})"
            tab_sel_bg = f"rgba(0,50,120,{int(220*wa)})"
            pane_bg = f"rgba(0,20,60,{int(170*wa)})"
            prog_bg = f"rgba(0,15,50,{int(150*wa)})"
            table_bg = f"rgba(0,20,60,{int(150*wa)})"
            table_color = f"rgba(200,230,255,{a})"
            hdr_bg = f"rgba(0,35,90,{int(200*wa)})"
            gridline = "#003366"
            chk_color = f"rgba(200,230,255,{a})"
            slider_groove = "#003366"
            slider_from = "#00cc66"
            slider_to = "#006633"
            slider_border = "#00ff88"
            btn_hover_color = f"rgba(255,255,255,{a})"
            mercy_border = "rgba(0,0,0,0)"
            mercy_color = f"rgba(255,255,255,{a})"
            mercy_hover_border = "rgba(255,255,255,30)"
        elif is_light:
            # Светлая тема (hysteria): тёмный текст, светлые фоны
            text_color = f"rgba(50,30,30,{a})"
            btn_bg_top = f"rgba(210,195,170,{int(220*wa)})"
            btn_bg_bot = f"rgba(195,180,155,{int(200*wa)})"
            btn_hover_top = f"rgba(225,210,185,{int(240*wa)})"
            btn_hover_bot = f"rgba(200,185,160,{int(220*wa)})"
            btn_pressed = f"rgba(180,165,140,{int(250*wa)})"
            mercy_bg_top = f"rgba(180,220,190,{int(220*wa)})"
            mercy_bg_bot = f"rgba(160,200,170,{int(200*wa)})"
            mercy_hover = f"rgba(170,230,180,{int(240*wa)})"
            panic_bg_top = f"rgba(220,160,160,{int(240*wa)})"
            panic_bg_bot = f"rgba(200,140,140,{int(220*wa)})"
            panic_hover = f"rgba(240,170,170,{int(255*wa)})"
            tab_bg = f"rgba(220,205,180,{int(200*wa)})"
            tab_sel_bg = f"rgba(235,220,195,{int(220*wa)})"
            pane_bg = f"rgba(230,215,190,{int(170*wa)})"
            prog_bg = f"rgba(210,195,170,{int(150*wa)})"
            table_bg = f"rgba(230,215,190,{int(150*wa)})"
            table_color = f"rgba(50,30,30,{a})"
            hdr_bg = f"rgba(215,200,175,{int(200*wa)})"
            gridline = "#c4a878"
            chk_color = f"rgba(60,40,40,{a})"
            slider_groove = "#c4a878"
            slider_from = "#9966cc"
            slider_to = "#7744aa"
            slider_border = "#9966cc"
            btn_hover_color = f"rgba(80,40,80,{a})"
            mercy_border = f"rgba(0,150,60,{a})"
            mercy_color = f"rgba(0,140,50,{a})"
            mercy_hover_border = f"rgba(0,200,100,{a})"
        else:
            text_color = f"rgba(220,220,220,{a})"
            btn_bg_top = f"rgba(45,8,8,{int(220*wa)})"
            btn_bg_bot = f"rgba(18,2,2,{int(200*wa)})"
            btn_hover_top = f"rgba(80,15,15,{int(240*wa)})"
            btn_hover_bot = f"rgba(40,5,5,{int(220*wa)})"
            btn_pressed = f"rgba(100,20,20,{int(250*wa)})"
            mercy_bg_top = f"rgba(5,30,15,{int(220*wa)})"
            mercy_bg_bot = f"rgba(2,12,5,{int(200*wa)})"
            mercy_hover = f"rgba(10,50,25,{int(240*wa)})"
            panic_bg_top = f"rgba(90,0,0,{int(240*wa)})"
            panic_bg_bot = f"rgba(40,0,0,{int(220*wa)})"
            panic_hover = f"rgba(130,0,0,{int(255*wa)})"
            tab_bg = f"rgba(20,4,4,{int(200*wa)})"
            tab_sel_bg = f"rgba(50,10,10,{int(220*wa)})"
            pane_bg = f"rgba(8,0,0,{int(170*wa)})"
            prog_bg = f"rgba(10,0,0,{int(150*wa)})"
            table_bg = f"rgba(10,0,0,{int(150*wa)})"
            table_color = f"rgba(200,200,200,{a})"
            hdr_bg = f"rgba(26,5,5,{int(200*wa)})"
            gridline = "#2a0808"
            chk_color = f"rgba(200,200,200,{a})"
            slider_groove = "#2a0808"
            slider_from = "#ff6040"
            slider_to = "#cc2020"
            slider_border = "#ff2020"
            btn_hover_color = f"rgba(255,180,130,{a})"
            mercy_border = f"rgba(0,180,80,{a})"
            mercy_color = f"rgba(0,210,100,{a})"
            mercy_hover_border = f"rgba(0,255,130,{a})"
        ss = f"""
QWidget {{
    background: transparent;
    color: {text_color};
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}
QLabel {{ color: {text_color}; }}
QToolTip {{
    background: rgba(15, 5, 5, 240);
    color: #cc8844;
    border: 1px solid #553311;
    border-radius: 4px;
    padding: 8px 10px;
    font-size: 11px;
    font-family: {FONT_FAMILY};
}}
QLineEdit {{
    background: rgba(20, 8, 8, 200);
    border: 1px solid #442222;
    border-radius: 6px;
    color: #cc8844;
    font-size: 11px;
    padding: 4px 8px;
}}
QLineEdit:focus {{
    border-color: {primary};
}}
QPushButton {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 {btn_bg_top}, stop:1 {btn_bg_bot});
    color: {primary};
    border: 2px solid {border};
    border-radius: 7px;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: bold;
    font-family: {FONT_FAMILY};
}}
QPushButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 {btn_hover_top}, stop:1 {btn_hover_bot});
    border: 2px solid {primary};
    color: {btn_hover_color};
}}
QPushButton:pressed {{ background: {btn_pressed}; }}
QPushButton#mercy {{
    border: 2px solid {mercy_border};
    color: {mercy_color};
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 {mercy_bg_top}, stop:1 {mercy_bg_bot});
}}
QPushButton#mercy:hover {{
    background: {mercy_hover};
    border-color: {mercy_hover_border};
}}
QPushButton#panic {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 {panic_bg_top}, stop:1 {panic_bg_bot});
    border: 3px solid rgba(255,0,0,{a});
    color: rgba(255,20,20,{a});
    border-radius: 10px; font-size: 15px; padding: 10px 14px;
}}
QPushButton#panic:hover {{
    background: {panic_hover};
    border-color: rgba(255,80,80,{a});
}}
QTabWidget::pane {{
    border: 1px solid {border};
    background: {pane_bg};
    border-radius: 4px;
}}
QTabBar::tab {{
    background: {tab_bg};
    color: {primary};
    border: 1px solid {border};
    padding: 4px 6px; font-weight: bold; font-size: 9px;
}}
QTabBar::tab:selected {{
    background: {tab_sel_bg};
    border-bottom: 3px solid {primary};
}}
QProgressBar {{
    border: 2px solid {border};
    background: {prog_bg};
    text-align: center;
    color: {c["accent"]};
    font-size: 11px; font-weight: bold;
    border-radius: 5px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #1a0000, stop:0.25 #880000, stop:0.55 #cc2020,
        stop:0.8 #ff4400, stop:1.0 #ff8800);
    border-radius: 4px;
}}
QTableWidget {{
    background: {table_bg};
    color: {table_color};
    gridline-color: {gridline};
    border: 1px solid {border};
    font-size: 11px;
}}
QHeaderView::section {{
    background: {hdr_bg};
    color: {primary};
    border: 1px solid {gridline};
    font-weight: bold; padding: 3px;
}}
QScrollArea {{ border: none; }}
QCheckBox {{ color: {chk_color}; font-size: 12px; }}
QSlider::groove:horizontal {{ background: {slider_groove}; height: 6px; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {slider_from},stop:1 {slider_to});
    width: 16px; margin: -5px 0; border-radius: 8px; border: 1px solid {slider_border};
}}
"""
        # Если тема использует кнопки-картинки — полностью сбрасываем стиль для них
        if self._current_theme.get("btn_images"):
            ss += """
QPushButton#imgBtnStart, QPushButton#imgBtnZone,
QPushButton#imgBtnMercy, QPushButton#imgBtnColor {
    border: none; background: transparent; padding: 0; margin: 0;
}
QPushButton#imgBtnStart:hover, QPushButton#imgBtnZone:hover,
QPushButton#imgBtnMercy:hover, QPushButton#imgBtnColor:hover {
    background: rgba(255,255,255,15); border-radius: 20px;
}
QPushButton#imgBtnStart:pressed, QPushButton#imgBtnZone:pressed,
QPushButton#imgBtnMercy:pressed, QPushButton#imgBtnColor:pressed {
    padding-top: 2px;
}
"""
        return ss

    # ═══════════════════════════════════════════════════════════
    #  BUILD UI
    # ═══════════════════════════════════════════════════════════
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        ml = QVBoxLayout(central)
        ml.setSpacing(2)
        extra_w = self._current_theme.get("extra_width", 0) // 2
        # lightning_margin удалён — заряженная не использует extra_width
        border_pad = 14 if self._current_theme.get("sharp_corners") else 0
        ml.setContentsMargins(12 + extra_w + border_pad, 8 + border_pad, 12 + extra_w + border_pad, 8 + border_pad)
        self._main_layout = ml

        self._fire_border = FireBorderWidget(self, self._current_theme)

        # Валюта теперь показана в окне `Магазин` (слева сверху на главном окне не дублируем).

        # ─── Header ──────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        hdr.setSpacing(4)
        self.title_label = QLabel("\U0001f525 INFERNO GRADE TRACKER \U0001f525")
        self.title_label.setStyleSheet(
            f"color: {self._current_theme['colors']['primary']}; font-size: 16px; "
            f"font-weight: bold; font-family: {FONT_FAMILY_DISPLAY}; letter-spacing: 1px;"
        )
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tg = QGraphicsDropShadowEffect()
        tg.setColor(QColor(self._current_theme["colors"]["glow"]))
        tg.setBlurRadius(18); tg.setOffset(0, 0)
        self.title_label.setGraphicsEffect(tg)
        hdr.addWidget(self.title_label, 1)
        shop_btn = QPushButton("\U0001f6d2")
        self._shop_btn = shop_btn
        shop_btn.setFixedSize(34, 34)
        shop_btn.setToolTip("Магазин")
        shop_btn.setStyleSheet(
            "QPushButton{border:2px solid #886611;color:#ffcc00;font-size:18px;"
            "padding:0;border-radius:8px;background:rgba(30,15,0,200);min-height:0;min-width:0;}"
            "QPushButton:hover{background:rgba(60,30,0,230);border-color:#ffaa00;}"
        )
        shop_btn.clicked.connect(self._open_shop_window)
        hdr.addWidget(shop_btn)
        bc = QPushButton("\u2014")
        bc.setFixedSize(28, 28)
        bc.setToolTip("Свернуть в трей")
        bc.setStyleSheet(
            f"border:1px solid {self._current_theme['colors']['primary']}; "
            "font-size:14px; padding:0; border-radius:5px; min-height:0; min-width:0;"
        )
        bc.clicked.connect(self.hide)
        hdr.addWidget(bc)
        ml.addLayout(hdr)

        # ─── Центральный счётчик (в контейнере фикс. размера чтобы jitter не сдвигал layout) ──
        self._counter_container = QWidget()
        self._counter_container.setStyleSheet("background:transparent;")
        self._counter_container.setFixedHeight(145)
        counter_inner = QVBoxLayout(self._counter_container)
        counter_inner.setContentsMargins(0, 0, 0, 0)
        counter_inner.setSpacing(0)
        self.counter_label = QLabel("0")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_counter_style(COUNTER_FONT_PT)
        cg = QGraphicsDropShadowEffect()
        cg.setColor(QColor(self._current_theme["colors"]["glow"]))
        cg.setBlurRadius(45); cg.setOffset(0, 0)
        self.counter_label.setGraphicsEffect(cg)
        counter_inner.addWidget(self.counter_label)
        self.today_lbl = QLabel("СЕГОДНЯ")
        self.today_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.today_lbl.setStyleSheet("color:#552222; font-size:11px; font-weight:bold; letter-spacing:3px;")
        ml.addWidget(self.today_lbl)
        ml.addWidget(self._counter_container)

        # ─── ВСЕГО и помилований ─────────────────────────────
        totals_row = QHBoxLayout()
        totals_row.setSpacing(20)
        totals_row.setContentsMargins(0, 0, 0, 0)
        self.total_big = QLabel("\U0001f480 ВСЕГО: 0")
        self.total_big.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_big.setStyleSheet(
            f"color: #cc4444; font-size: {TOTAL_FONT_PT}px; font-weight: bold; font-family: {FONT_FAMILY};"
        )
        self.mercy_big = QLabel("\U0001f54a ПОМИЛОВАНО: 0")
        self.mercy_big.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mercy_big.setStyleSheet(
            f"color: #44aa66; font-size: {TOTAL_FONT_PT - 6}px; font-weight: bold; font-family: {FONT_FAMILY};"
        )
        totals_row.addWidget(self.total_big, 3)
        totals_row.addWidget(self.mercy_big, 2)
        ml.addLayout(totals_row)

        # ─── Стрик ───────────────────────────────────────────
        self.streak_label = QLabel("\U0001f525 СТРИК: 0 ДНЕЙ")
        self.streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.streak_label.setWordWrap(True)
        self.streak_label.setStyleSheet(
            f"color: #ff6600; font-size: {STREAK_FONT_PT}px; font-weight: bold; "
            f"font-family: {FONT_FAMILY_DISPLAY}; padding: 2px 0;"
        )
        sg = QGraphicsDropShadowEffect()
        sg.setColor(QColor(255, 90, 0, 130))
        sg.setBlurRadius(20); sg.setOffset(0, 0)
        self.streak_label.setGraphicsEffect(sg)
        ml.addWidget(self.streak_label)

        # ─── Мотивационная фраза ──────────────────────────────
        self.quote_label = QLabel("")
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_label.setWordWrap(True)
        self.quote_label.setStyleSheet(
            f"color:#cc8844; font-size:13px; font-style:italic; font-weight:bold; font-family:{FONT_FAMILY}; padding:2px 8px;"
        )
        ml.addWidget(self.quote_label)
        self._quote_index = 0

        # ─── Прогресс ранга ──────────────────────────────────
        rank_row = QHBoxLayout()
        rank_row.setContentsMargins(0, 2, 0, 0)
        self.rank_label = QLabel("\U0001f530 Новичок")
        self.rank_label.setStyleSheet("color:#ffcc00; font-size:13px; font-weight:bold;")
        rank_row.addWidget(self.rank_label)
        rank_row.addStretch()
        self.rank_next_label = QLabel("\u2192 ???")
        self.rank_next_label.setStyleSheet("color:#886600; font-size:13px; font-weight:bold;")
        rank_row.addWidget(self.rank_next_label)
        ml.addLayout(rank_row)
        self.rank_bar = QProgressBar()
        self.rank_bar.setRange(0, 100)
        self.rank_bar.setFixedHeight(RANK_BAR_H)
        self.rank_bar.setFormat("%p%")
        self.rank_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #882200; background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1a0808,stop:1 #0a0000);
                text-align: center; color: #ffcc00; font-size: 12px; font-weight: bold;
                border-radius: 6px; min-height: {RANK_BAR_H}px; max-height: {RANK_BAR_H}px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1a0000,stop:0.2 #880000,stop:0.5 #cc2020,stop:0.8 #ff4400,stop:1.0 #ff8800);
                border-radius: 5px;
            }}
        """)
        # Бар шире на 18% — отрицательные боковые margins
        bar_wrap = QHBoxLayout()
        bar_wrap.setContentsMargins(-15, -2, -15, -2)
        bar_wrap.addWidget(self.rank_bar)
        ml.addLayout(bar_wrap)

        # ─── Комбо ───────────────────────────────────────────
        self.combo_label = QLabel("")
        self.combo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.combo_label.setFixedHeight(0)  # 0 когда пустой, устанавливается при комбо
        self.combo_label.setStyleSheet(
            f"color: #ff4400; font-size: 18px; font-weight: bold; font-family: {FONT_FAMILY_DISPLAY};"
        )
        ml.addWidget(self.combo_label)

        # ─── Лейбл наказания (если активно) ──────────────────
        self.punishment_label = QLabel("")
        self.punishment_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.punishment_label.setFixedHeight(0)
        self.punishment_label.setWordWrap(True)
        self.punishment_label.setStyleSheet(
            "color:#ff2020; font-size:12px; font-weight:bold; background:rgba(40,0,0,180); "
            "border:2px solid #ff0000; border-radius:6px; padding:4px;"
        )
        ml.addWidget(self.punishment_label)

        # ─── Кнопки ──────────────────────────────────────────

        row1 = QHBoxLayout(); row1.setSpacing(6)
        self.btn_zone = QPushButton("\U0001f3af Зона казни")
        self.btn_zone.clicked.connect(self.request_calibrate_zone)
        row1.addWidget(self.btn_zone)
        self.btn_color = QPushButton("\U0001f3a8 Цветпикер")
        self.btn_color.clicked.connect(self.request_calibrate_color)
        row1.addWidget(self.btn_color)
        self.btn_toggle = QPushButton("\u25b6  СТАРТ")
        self.btn_toggle.setStyleSheet(
            "QPushButton{border-color:#00cc00;color:#00cc00;font-size:14px;}"
            "QPushButton:hover{border-color:#00ff40;color:#00ff40;background:rgba(0,40,0,200);}"
        )
        self.btn_toggle.clicked.connect(self._toggle_detection)
        row1.addWidget(self.btn_toggle)
        ml.addLayout(row1)

        row2 = QHBoxLayout(); row2.setSpacing(6)
        row2.setContentsMargins(20, 0, 20, 0)  # сузить на ~20% с каждой стороны
        self.btn_mercy = QPushButton("\U0001f54a ПОМИЛОВАНИЕ")
        self.btn_mercy.setObjectName("mercy")
        self.btn_mercy.clicked.connect(self._on_mercy)
        row2.addWidget(self.btn_mercy, 1)
        self.btn_panic = QPushButton("\u26d4 АВАРИЙНЫЙ СТОП")
        self.btn_panic.setObjectName("panic")
        self.btn_panic.clicked.connect(self.request_panic_stop)
        row2.addWidget(self.btn_panic, 1)
        ml.addLayout(row2)

        self.status_label = QLabel("\U0001f534 Ожидание...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color:#ffffff; font-size:9px; padding:0; margin:0;")
        self.status_label.setMaximumHeight(12)
        ml.addWidget(self.status_label)

        # ─── Подробнее ───────────────────────────────────────
        self.btn_expand = QPushButton("\u25bc  Подробнее")
        self.btn_expand.setStyleSheet(
            "QPushButton{border:1px solid #3a1515;color:#664444;font-size:11px;padding:3px 5px;max-height:22px;}"
            "QPushButton:hover{border-color:#773333;color:#aa6666;}"
        )
        self.btn_expand.clicked.connect(self._toggle_expand)
        expand_wrap = QHBoxLayout()
        expand_wrap.setContentsMargins(60, 0, 60, 0)  # сузить на ~60%
        expand_wrap.addWidget(self.btn_expand)
        ml.addLayout(expand_wrap)

        # ═══ Расширенная секция ═══════════════════════════════
        self._detail = QWidget()
        self._detail.setVisible(False)
        dl = QVBoxLayout(self._detail)
        dl.setSpacing(2); dl.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        stats_w = self._tab_stats_and_records()
        self.tabs.addTab(stats_w, "\U0001f4ca Стат")
        self._tab_idx_stats = self.tabs.count() - 1
        # Ачивки → «Файлы\n{nickname}» — двустрочное название, мелкий шрифт
        self._ach_tab_index = self.tabs.count()
        self.tabs.addTab(self._tab_achievements(), f"\U0001f4c2 Файлы\n{self._user_nickname}")
        themes_w = self._tab_themes()
        self.tabs.addTab(themes_w, "\U0001f525 Огни")
        self._tab_idx_themes = self.tabs.count() - 1
        # Лог и Коды — доступны через кнопки в настройках (отдельные окна)
        self.tabs.addTab(self._tab_settings(), "\u2699 Настр.")
        self.tabs.addTab(self._tab_goals(), "\U0001f3af Цели")
        self._tab_idx_goals = self.tabs.count() - 1
        if self._cloud_service and getattr(self._cloud_service, "available", False):
            from modules.leaderboard_ui import LeaderboardTab

            self.tabs.addTab(LeaderboardTab(self._cloud_service), "\U0001f3c6 Топ")
        dl.addWidget(self.tabs)
        ml.addWidget(self._detail)

        extra = self._current_theme.get("extra_width", 0)
        self.setFixedWidth(WIN_W + extra)
        self._update_height()

    # ── Размеры ───────────────────────────────────────────────
    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._fire_border.setGeometry(0, 0, self.width(), self.height())

    def _toggle_expand(self):
        self._emoji_boom_from_widget(self.btn_expand, 14)
        self._expanded = not self._expanded
        self._detail.setVisible(self._expanded)
        self.btn_expand.setText("\u25b2  Свернуть" if self._expanded else "\u25bc  Подробнее")
        self._update_height()

    def _update_height(self):
        if self._expanded:
            self.setMinimumHeight(WIN_EXP_H)
            self.setMaximumHeight(1100)
        else:
            self.setMinimumHeight(0)
            self.setMaximumHeight(WIN_H)
        self.adjustSize()

    # ═══════════════════════════════════════════════════════════
    #  Вкладки
    # ═══════════════════════════════════════════════════════════
    def _tab_stats_and_records(self):
        """Объединённая вкладка: статистика + рекорды."""
        w = QWidget()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(6, 6, 6, 6); lay.setSpacing(5)
        pc = self._current_theme['colors']['primary']

        self.sv = []
        self._stat_labels = []

        # ── Верхняя большая карточка: Сегодня + Стрик ──
        top_card = QFrame()
        top_card.setStyleSheet(
            "QFrame{background:rgba(20,5,5,200);border:2px solid #662222;border-radius:10px;}"
        )
        top_lay = QVBoxLayout(top_card)
        top_lay.setContentsMargins(12, 10, 12, 10); top_lay.setSpacing(6)
        # Сегодня
        today_row = QHBoxLayout(); today_row.setSpacing(8)
        ic_today = QLabel("\U0001f525"); ic_today.setFont(QFont("Segoe UI", 20)); ic_today.setFixedWidth(32)
        today_row.addWidget(ic_today)
        lb_today = QLabel("Сегодня")
        lb_today.setStyleSheet(f"color:{pc}; font-size:14px; font-weight:bold;")
        self._stat_labels.append(lb_today)
        today_row.addWidget(lb_today, 1)
        v_today = QLabel("0")
        v_today.setStyleSheet("color:#fff; font-size:26px; font-weight:bold;")
        v_today.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        today_row.addWidget(v_today)
        self.sv.append(v_today)
        top_lay.addLayout(today_row)
        # Разделитель
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet("background:#442222;")
        top_lay.addWidget(sep)
        # Стрик
        streak_row = QHBoxLayout(); streak_row.setSpacing(8)
        ic_streak = QLabel("\U0001f525"); ic_streak.setFont(QFont("Segoe UI", 16)); ic_streak.setFixedWidth(32)
        streak_row.addWidget(ic_streak)
        lb_streak = QLabel("Стрик")
        lb_streak.setStyleSheet(f"color:#ff8844; font-size:13px; font-weight:bold;")
        streak_row.addWidget(lb_streak, 1)
        self._stat_streak_val = QLabel("0 дн")
        self._stat_streak_val.setStyleSheet("color:#ffaa44; font-size:20px; font-weight:bold;")
        self._stat_streak_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        streak_row.addWidget(self._stat_streak_val)
        top_lay.addLayout(streak_row)
        lay.addWidget(top_card)

        # ── Средние карточки: Неделя, Месяц, Всё время, Помилований ──
        mid_labels = [
            ("\U0001f4c5", "Неделя"),
            ("\U0001f4c6", "Месяц"),
            ("\U0001f480", "Всё время"),
            ("\U0001f54a", "Помилований"),
        ]
        for icon, title in mid_labels:
            card = QFrame()
            card.setStyleSheet(
                "QFrame{background:rgba(15,5,5,180);border:1px solid #442222;border-radius:6px;}"
            )
            hl = QHBoxLayout(card); hl.setContentsMargins(10, 6, 10, 6); hl.setSpacing(8)
            ic = QLabel(icon)
            ic.setFont(QFont("Segoe UI", 14)); ic.setFixedWidth(26)
            hl.addWidget(ic)
            lb = QLabel(title)
            lb.setStyleSheet(f"color:{pc}; font-size:12px; font-weight:bold;")
            self._stat_labels.append(lb)
            hl.addWidget(lb, 1)
            v = QLabel("0")
            v.setStyleSheet("color:#fff; font-size:16px; font-weight:bold;")
            v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            hl.addWidget(v)
            self.sv.append(v)
            lay.addWidget(card)

        # ── Нижняя плашка: Рекорды ──
        rec_hdr = QLabel("\U0001f3c6 РЕКОРДЫ")
        rec_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rec_hdr.setStyleSheet("color:#ffcc00; font-size:12px; font-weight:bold; padding:6px 0 2px 0;")
        lay.addWidget(rec_hdr)

        self._rec_cards = {}
        records_def = [
            ("max_day",   "\u26a1",  "Макс/день"),
            ("max_week",  "\U0001f4c5", "Макс/неделя"),
            ("max_combo", "\U0001f4a5", "Макс комбо"),
            ("streak",    "\U0001f525", "Стрик"),
            ("total",     "\U0001f480", "Всего"),
            ("mercy",     "\U0001f54a", "Помилований"),
        ]

        # Рекорды в сетке 2 в ряд
        row_lay = None
        for i, (key, icon, title) in enumerate(records_def):
            if i % 2 == 0:
                row_lay = QHBoxLayout(); row_lay.setSpacing(4)
                lay.addLayout(row_lay)
            card = QFrame()
            card.setStyleSheet(
                "QFrame{background:rgba(20,8,3,200);border:1px solid #553311;border-radius:6px;}"
            )
            cl = QVBoxLayout(card); cl.setContentsMargins(8, 5, 8, 5); cl.setSpacing(2)
            top_r = QHBoxLayout(); top_r.setSpacing(4)
            ic = QLabel(icon); ic.setFont(QFont("Segoe UI", 12))
            top_r.addWidget(ic)
            lb = QLabel(title)
            lb.setStyleSheet("color:#cc8844; font-size:10px; font-weight:bold;")
            top_r.addWidget(lb, 1)
            cl.addLayout(top_r)
            val = QLabel("0")
            val.setStyleSheet("color:#ffcc00; font-size:15px; font-weight:bold;")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(val)
            self._rec_cards[key] = val
            row_lay.addWidget(card)

        lay.addStretch()
        scroll.setWidget(inner)
        outer = QVBoxLayout(w); outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return w

    def _tab_achievements(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(4, 4, 4, 4)
        l.setSpacing(4)

        # Шапка — НЕ скроллится
        self.ach_total_label = QLabel("Файлы: 0/0 (0%)")
        self.ach_total_label.setStyleSheet("color:#ffcc00; font-size:13px; font-weight:bold;")
        l.addWidget(self.ach_total_label)

        self.ach_total_bar = QProgressBar()
        self.ach_total_bar.setRange(0, 100)
        self.ach_total_bar.setFixedHeight(10)
        self.ach_total_bar.setFormat("")
        l.addWidget(self.ach_total_bar)

        # Прокручиваемая область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.ach_container = QWidget()
        self.ach_container.setStyleSheet("background:transparent;")
        self.ach_layout = QVBoxLayout(self.ach_container)
        self.ach_layout.setContentsMargins(2, 2, 2, 2)
        self.ach_layout.setSpacing(4)
        scroll.setWidget(self.ach_container)
        l.addWidget(scroll)

        self._ach_cat_collapsed = {}
        self._ach_cat_widgets = {}
        return w

    def _tab_themes(self):
        """Вкладка огней/цветов — привязанные друг к другу темы."""
        w = QWidget(); l = QVBoxLayout(w)
        l.setContentsMargins(4, 4, 4, 4); l.setSpacing(4)

        # Строка поиска
        self._theme_search = QLineEdit()
        self._theme_search.setPlaceholderText("🔍 Поиск темы...")
        self._theme_search.setStyleSheet(
            "QLineEdit{background:rgba(20,8,8,200);border:1px solid #442222;"
            "border-radius:6px;color:#cc8844;font-size:11px;padding:4px 8px;}"
            "QLineEdit:focus{border-color:#ff8800;}"
        )
        self._theme_search.textChanged.connect(self._filter_themes)
        l.addWidget(self._theme_search)

        self._themes_scroll = QScrollArea(); self._themes_scroll.setWidgetResizable(True)
        self.themes_container = QWidget()
        self.themes_layout = QVBoxLayout(self.themes_container)
        self.themes_layout.setContentsMargins(2, 2, 2, 2); self.themes_layout.setSpacing(2)
        self._themes_scroll.setWidget(self.themes_container)
        l.addWidget(self._themes_scroll)

        # Хранилище состояния категорий (свёрнуты/развёрнуты) и виджетов
        self._theme_cat_collapsed = {}  # cat_id → bool
        self._theme_cat_widgets = {}    # cat_id → (header_btn, container_widget)
        self._theme_item_widgets = []   # [(frame, theme_id, name_lower), ...]
        return w

    def _update_currency_display(self):
        """Синхронизировать отображение золота/ключей (только в Магазине)."""
        sw = getattr(self, "_shop_win", None)
        if sw and hasattr(sw, "_update_wallet_labels"):
            sw._update_wallet_labels()

    def _tab_shop(self):
        """Вкладка магазина — 3 каталога."""
        from PyQt6.QtWidgets import QScrollArea, QGridLayout
        w = QWidget()
        main_lay = QVBoxLayout(w)
        main_lay.setContentsMargins(5, 5, 5, 5)
        main_lay.setSpacing(4)

        # ── Навигация по каталогам ──
        nav = QHBoxLayout(); nav.setSpacing(4)
        nav_btns = []
        for label, anchor in [("🛒 Темы", "shop_themes"), ("🎰 Рулетка", "shop_gacha"), ("💱 Обмен", "shop_exchange")]:
            b = QPushButton(label)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                "QPushButton{color:#cc8844;background:rgba(30,12,5,200);border:1px solid #553311;"
                "border-radius:4px;padding:5px 10px;font-size:11px;font-weight:bold;}"
                "QPushButton:hover{background:rgba(50,20,10,230);border-color:#884422;}"
            )
            nav.addWidget(b)
            nav_btns.append((b, anchor))
        main_lay.addLayout(nav)

        # ── Scroll area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        scroll_w = QWidget()
        self._shop_layout = QVBoxLayout(scroll_w)
        self._shop_layout.setContentsMargins(2, 2, 2, 2)
        self._shop_layout.setSpacing(8)
        scroll.setWidget(scroll_w)
        main_lay.addWidget(scroll)

        # ══ Секция 1: Темы ══
        sec1 = QLabel("🛒  МАГАЗИН ТЕМ")
        sec1.setObjectName("shop_themes")
        sec1.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sec1.setStyleSheet("color:#cc8844; padding:4px 0;")
        self._shop_layout.addWidget(sec1)

        # Таймер обновления пула
        pool_rem = self.shop.pool_time_remaining()
        mins = pool_rem // 60
        self._pool_timer_label = QLabel(f"⏱ Обновление пула: {mins // 60}ч {mins % 60}м")
        self._pool_timer_label.setStyleSheet("color:#666; font-size:10px;")
        self._shop_layout.addWidget(self._pool_timer_label)

        # Карточки тем (сетка 2 ряда x 3 столбца)
        self._shop_cards_container = QWidget()
        self._shop_grid = QGridLayout(self._shop_cards_container)
        self._shop_grid.setSpacing(6)
        self._shop_grid.setContentsMargins(0, 0, 0, 0)
        self._build_shop_cards()
        self._shop_layout.addWidget(self._shop_cards_container)

        # ══ Секция 2: Рулетка ══
        sec2 = QLabel("🎰  РУЛЕТКА")
        sec2.setObjectName("shop_gacha")
        sec2.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sec2.setStyleSheet("color:#cc8844; padding:4px 0;")
        self._shop_layout.addWidget(sec2)

        gacha_desc = QLabel("Потрать 🥐 ключ-круассан и испытай удачу!\nШансы: 🍬 Карамелька 8% • 💰 Золото • 💨 Ничего 38%")
        gacha_desc.setWordWrap(True)
        gacha_desc.setStyleSheet("color:#888; font-size:10px; padding:2px;")
        self._shop_layout.addWidget(gacha_desc)

        self._gacha_result_label = QLabel("")
        self._gacha_result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._gacha_result_label.setStyleSheet("color:#ffcc00; font-size:14px; font-weight:bold; min-height:30px;")
        self._shop_layout.addWidget(self._gacha_result_label)

        spin_btn = QPushButton("🎲  КРУТИТЬ  (1 🥐)")
        spin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        spin_btn.setFixedHeight(40)
        spin_btn.setStyleSheet(
            "QPushButton{color:#fff;font-size:13px;font-weight:bold;border:2px solid #cc8844;"
            "border-radius:8px;background:qlineargradient(y1:0,y2:1,stop:0 #aa5522,stop:1 #773311);}"
            "QPushButton:hover{background:qlineargradient(y1:0,y2:1,stop:0 #cc6633,stop:1 #994422);border-color:#ffaa55;}"
            "QPushButton:pressed{background:#662211;}"
        )
        spin_btn.clicked.connect(self._on_gacha_spin)
        self._shop_layout.addWidget(spin_btn)

        # ══ Секция 3: Обменник ══
        sec3 = QLabel("💱  ОБМЕННИК")
        sec3.setObjectName("shop_exchange")
        sec3.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sec3.setStyleSheet("color:#cc8844; padding:4px 0;")
        self._shop_layout.addWidget(sec3)

        # Кнопка обмена ключ -> золото
        exch_btn = QPushButton("🔄  Обменять 1 🥐 → 250 🪙")
        exch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exch_btn.setFixedHeight(34)
        exch_btn.setStyleSheet(
            "QPushButton{color:#dda644;font-size:11px;font-weight:bold;border:1px solid #886600;"
            "border-radius:6px;background:rgba(40,20,0,200);}"
            "QPushButton:hover{background:rgba(60,30,0,220);border-color:#bb8800;}"
        )
        exch_btn.clicked.connect(self._on_exchange_key)
        self._shop_layout.addWidget(exch_btn)

        # Бесплатное золото
        self._free_gold_btn = QPushButton("🎁  Бесплатное золото")
        self._free_gold_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._free_gold_btn.setFixedHeight(34)
        self._free_gold_btn.clicked.connect(self._on_claim_free_gold)
        self._shop_layout.addWidget(self._free_gold_btn)
        self._update_free_gold_btn()

        # Бесплатный ключ
        self._free_key_btn = QPushButton("🔑  Бесплатный ключ (раз в сутки)")
        self._free_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._free_key_btn.setFixedHeight(34)
        self._free_key_btn.clicked.connect(self._on_claim_free_key)
        self._shop_layout.addWidget(self._free_key_btn)
        self._update_free_key_btn()

        self._shop_exchange_label = QLabel("")
        self._shop_exchange_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._shop_exchange_label.setStyleSheet("color:#88cc44; font-size:11px;")
        self._shop_layout.addWidget(self._shop_exchange_label)

        self._shop_layout.addStretch()

        # Навигация scroll-to
        for btn, anchor in nav_btns:
            btn.clicked.connect(lambda checked, a=anchor: self._scroll_to_shop_section(a, scroll))

        return w

    def _scroll_to_shop_section(self, anchor, scroll):
        """Прокрутить к секции магазина."""
        target = scroll.widget().findChild(QLabel, anchor)
        if target:
            scroll.ensureWidgetVisible(target, 0, 20)

    def _open_shop_window(self):
        gate = getattr(self, "_calc_content_gate", None)
        can_shop = True
        try:
            can_shop = gate().get("shop", True)
        except Exception:
            pass
        if not can_shop:
            # Переключаемся на вкладку целей (если она есть)
            if getattr(self, "tabs", None) is not None and self._tab_idx_goals is not None:
                self.tabs.setCurrentIndex(self._tab_idx_goals)
            flash = ComboFlashLabel("🔒 Магазин закрыт.\nНужно 15 двоек.", self, 3200)
            flash.setStyleSheet(
                "color:#ffcc00; font-size:26px; font-weight:bold; background:transparent; font-family:"
                f"{FONT_FAMILY_DISPLAY};"
            )
            flash.setGeometry(0, 60, self.width(), 140)
            flash.show()
            return
        if hasattr(self, '_shop_win') and self._shop_win and self._shop_win.isVisible():
            self._shop_win.raise_()
            self._shop_win.activateWindow()
            return
        self._shop_win = ShopWindow(self)
        # Position near the panel
        pos = self.pos()
        self._shop_win.move(pos.x() + self.width() + 10, pos.y())
        self._shop_win.show()

    def _build_shop_cards(self):
        """Построить карточки тем в магазине."""
        # Очистить сетку
        while self._shop_grid.count():
            item = self._shop_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        pool = self.shop.get_theme_pool()
        for idx, theme_id in enumerate(pool):
            t = get_theme_by_id(theme_id)
            if not t:
                continue
            card = self._build_theme_card(t)
            row, col = divmod(idx, 3)
            self._shop_grid.addWidget(card, row, col)

    def _build_theme_card(self, t):
        """Построить одну карточку темы для магазина."""
        from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect
        import os

        card = QFrame()
        card.setFixedSize(145, 210)
        border_clr = t["colors"].get("border", "#553311")
        primary = t["colors"].get("primary", "#cc8844")
        card.setStyleSheet(
            f"QFrame{{background:rgba(15,8,4,220);border:2px solid {border_clr};"
            f"border-radius:12px;}}"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 10, 8, 8)
        vl.setSpacing(4)

        # Круглая иконка (69x69 — +15%)
        ICON_SZ = 69
        icon_label = QLabel()
        icon_label.setFixedSize(ICON_SZ, ICON_SZ)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = self._get_theme_icon_path(t)
        icon_text = t.get("theme_icon_text")
        if icon_path:
            # Создаём круглый пиксмап: иконка внутри круга
            from PyQt6.QtGui import QPainter as _QP2, QPainterPath
            raw = QPixmap(icon_path).scaled(ICON_SZ - 6, ICON_SZ - 6,
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            circle_pm = QPixmap(ICON_SZ, ICON_SZ)
            circle_pm.fill(QColor(0, 0, 0, 0))
            pp = _QP2(circle_pm)
            pp.setRenderHint(_QP2.RenderHint.Antialiasing)
            # Фон круга
            path = QPainterPath()
            path.addEllipse(3, 3, ICON_SZ - 6, ICON_SZ - 6)
            pp.setClipPath(path)
            pp.fillRect(0, 0, ICON_SZ, ICON_SZ, QColor(0, 0, 0, 180))
            # Иконка по центру (внутри круга)
            ix = (ICON_SZ - raw.width()) // 2
            iy = (ICON_SZ - raw.height()) // 2
            pp.drawPixmap(ix, iy, raw)
            pp.setClipping(False)
            # Обводка круга
            pp.setPen(QPen(QColor(primary), 3))
            pp.setBrush(Qt.BrushStyle.NoBrush)
            pp.drawEllipse(3, 3, ICON_SZ - 6, ICON_SZ - 6)
            pp.end()
            icon_label.setPixmap(circle_pm)
            icon_label.setStyleSheet("border:none;background:transparent;")
        elif icon_text:
            txt, clr = icon_text
            is_emoji = any(ord(ch) > 0x2600 for ch in txt)
            fsz = 32 if is_emoji else 20
            icon_label.setText(txt)
            icon_label.setFont(QFont("Segoe UI Emoji" if is_emoji else "Segoe UI", fsz, QFont.Weight.ExtraBold))
            r = ICON_SZ // 2
            icon_label.setStyleSheet(
                f"color:{clr};border:3px solid {clr};border-radius:{r}px;background:rgba(0,0,0,180);"
            )
        else:
            r = ICON_SZ // 2
            icon_label.setStyleSheet(
                f"background:{primary};border:3px solid {border_clr};border-radius:{r}px;"
            )
        vl.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignHCenter)

        # Название
        name_lbl = QLabel(t["name"])
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setWordWrap(True)
        name_lbl.setStyleSheet(f"color:{primary}; font-size:10px; font-weight:bold; border:none;")
        vl.addWidget(name_lbl)

        # Особенности (краткий список)
        desc_full = t.get("desc_full", t["desc"])
        features = []
        for line in desc_full.replace("<br>", "\n").replace("<b>", "").replace("</b>", "").split("\n"):
            line = line.strip()
            if line.startswith("•"):
                features.append(line)
        feat_text = "\n".join(features[:3]) if features else t["desc"][:40]
        feat_lbl = QLabel(feat_text)
        feat_lbl.setStyleSheet("color:#777; font-size:8px; border:none; padding:0;")
        feat_lbl.setWordWrap(True)
        vl.addWidget(feat_lbl)

        vl.addStretch()

        # Кнопка покупки
        purchased = self.shop.is_theme_purchased(t["id"])
        price = self.shop.get_theme_price(t["id"])
        if purchased:
            buy_btn = QPushButton("✔ Куплено")
            buy_btn.setEnabled(False)
            buy_btn.setStyleSheet(
                "QPushButton{color:#555;font-size:10px;border:1px solid #333;"
                "border-radius:6px;padding:4px;background:rgba(20,20,20,200);}"
            )
        else:
            can_afford = self.shop.get_gold() >= price
            buy_btn = QPushButton(f"🪙 {price}")
            buy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            buy_btn.setFixedHeight(30)
            if can_afford:
                buy_btn.setStyleSheet(
                    "QPushButton{color:#111;font-size:11px;font-weight:bold;border:none;"
                    "border-radius:8px;padding:4px 8px;"
                    "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #88cc22,stop:0.5 #bbee44,stop:1 #88cc22);}"
                    "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #99dd33,stop:0.5 #ccff55,stop:1 #99dd33);}"
                )
            else:
                buy_btn.setStyleSheet(
                    "QPushButton{color:#666;font-size:11px;font-weight:bold;border:1px solid #444;"
                    "border-radius:8px;padding:4px 8px;background:rgba(30,30,30,200);}"
                )
            theme_id = t["id"]
            buy_btn.clicked.connect(lambda checked, tid=theme_id, p=price: self._on_buy_theme(tid, p))
        vl.addWidget(buy_btn)

        return card

    def _on_buy_theme(self, theme_id, price):
        """Купить тему."""
        if self.shop.purchase_theme(theme_id, price):
            # Трекинг для ачивок
            self.config["_themes_bought"] = self.config.get("_themes_bought", 0) + 1
            if price > 1000:
                self.config["_bought_over_1000"] = True
            if price >= 5000:
                self.config["_bought_5000"] = True
            from modules.config import save_config
            save_config(self.config)
            self._update_currency_display()
            self._build_shop_cards()
            # Конфетти
            self._emoji_boom_from_widget(self._shop_cards_container, 30)
            self._confetti_boom_from_widget(self._shop_cards_container, 240)
            # Предложить применить
            t = get_theme_by_id(theme_id)
            name = t["name"] if t else theme_id
            flash = ComboFlashLabel(f"🎉 {name}\nкуплена! Применить?", self, 4000)
            flash.setStyleSheet(
                f"color:#ffcc00; font-size:22px; font-weight:bold; "
                f"font-family:{FONT_FAMILY_DISPLAY}; background:transparent;"
            )
            flash.setCursor(Qt.CursorShape.PointingHandCursor)
            flash.mousePressEvent = lambda ev, tid=theme_id: (self._select_theme(tid), flash.close())
            flash.show()
            # Обновить список тем
            self._refresh_themes()

    def _tab_codes(self):
        """Вкладка ввода секретных кодов."""
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 20, 10, 10)
        icon = QLabel("\U0001f511")
        icon.setFont(QFont("Segoe UI", 36))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(icon)
        title = QLabel("СЕКРЕТНЫЕ КОДЫ")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#aa7733;")
        lay.addWidget(title)
        sub = QLabel("Введи код и нажми Enter")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color:#555; font-size:10px;")
        lay.addWidget(sub)
        self._code_input = QLineEdit()
        self._code_input.setPlaceholderText("Введите код...")
        self._code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._code_input.setMaxLength(50)
        self._code_input.setStyleSheet(
            "QLineEdit{background:rgba(0,0,0,120);border:2px solid #555;"
            "border-radius:8px;color:#ffcc00;font-size:14px;padding:8px;"
            "font-family:Consolas;letter-spacing:2px;}"
            "QLineEdit:focus{border-color:#ffaa00;}"
        )
        self._code_input.returnPressed.connect(self._on_code_submit)
        lay.addWidget(self._code_input)
        self._code_result = QLabel("")
        self._code_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._code_result.setStyleSheet("color:#666; font-size:11px; padding:6px;")
        self._code_result.setWordWrap(True)
        lay.addWidget(self._code_result)
        lay.addStretch()
        # Restore saved stickers
        QTimer.singleShot(200, self._restore_stickers)
        return w

    def _on_code_submit(self):
        """Обработка ввода секретного кода."""
        try:
            self._on_code_submit_inner()
        except Exception as e:
            import traceback; traceback.print_exc()
            self._code_result.setText(f"❌ Ошибка: {e}")
            self._code_result.setStyleSheet("color:#ff0000; font-size:11px; padding:6px;")

    def _on_code_submit_inner(self):
        code = self._code_input.text().strip().lower()
        if not code:
            return
        self._emoji_boom_from_widget(self._code_input, 15)
        used_codes = self.config.setdefault("used_codes", [])
        valid = False

        if code == "666":
            valid = True
            if "666" not in used_codes:
                used_codes.append("666")
                # Разблокировать адскую тему
                purchased = self.config.setdefault("shop_purchased_themes", [])
                if "hellish_mexican" not in purchased:
                    purchased.append("hellish_mexican")
                self._code_result.setText("🌶️ Адская тема разблокирована!")
                self._code_result.setStyleSheet("color:#ff4400; font-size:13px; font-weight:bold; padding:6px;")
                self._emoji_boom_from_widget(self._code_result, 30)
                self._refresh_themes()
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        elif code == "windows":
            valid = True
            if "windows" not in used_codes:
                used_codes.append("windows")
                self._code_result.setText("🖥️ Что-то появилось...")
                self._code_result.setStyleSheet("color:#00ccff; font-size:13px; font-weight:bold; padding:6px;")
                # Наклейка bage
                self._spawn_sticker("bage.png", remove_bg="white", action="modern_windows")
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        elif code == "key":
            valid = True
            if "key" not in used_codes:
                used_codes.append("key")
                self.shop.add_keys(1)
                self._update_currency_display()
                self._code_result.setText("🔑 +1 ключ-круассан!")
                self._code_result.setStyleSheet("color:#dda644; font-size:13px; font-weight:bold; padding:6px;")
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        elif code == "\u0444\u043e\u043b\u043e\u043c\u0435\u0435\u0432":
            valid = True
            if "\u0444\u043e\u043b\u043e\u043c\u0435\u0435\u0432" not in used_codes:
                used_codes.append("\u0444\u043e\u043b\u043e\u043c\u0435\u0435\u0432")
                self.shop.add_gold(222)
                self._animate_currency_add(222, "gold")
                self._code_result.setText("\U0001f393 +222 золота! Фоломеев одобряет!")
                self._code_result.setStyleSheet("color:#ffcc00; font-size:13px; font-weight:bold; padding:6px;")
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        elif code == "\u043c\u0430\u043b\u044b\u0448\u0435\u0432":
            valid = True
            if "\u043c\u0430\u043b\u044b\u0448\u0435\u0432" not in used_codes:
                used_codes.append("\u043c\u0430\u043b\u044b\u0448\u0435\u0432")
                self._spawn_sticker("sticker_sun.jpg", remove_bg="white")
                self._code_result.setText("\u2600\ufe0f Наклейка получена!")
                self._code_result.setStyleSheet("color:#ffcc00; font-size:13px; font-weight:bold; padding:6px;")
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        elif code == "67":
            valid = True
            if "67" not in used_codes:
                used_codes.append("67")
                self._spawn_sticker("sticker_him.png", remove_bg="black")
                self._code_result.setText("\U0001f479 HIM наклейка получена!")
                self._code_result.setStyleSheet("color:#cc0000; font-size:13px; font-weight:bold; padding:6px;")
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        elif code == "sahur":
            valid = True
            if "sahur" not in used_codes:
                used_codes.append("sahur")
                self._spawn_sticker("sticker_sahur.png")
                self._code_result.setText("\U0001f319 Sahur наклейка получена!")
                self._code_result.setStyleSheet("color:#44ccff; font-size:13px; font-weight:bold; padding:6px;")
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        elif code == "2":
            valid = True
            if "2" not in used_codes:
                used_codes.append("2")
                self.shop.add_gold(2)
                self._animate_currency_add(2, "gold")
                self._code_result.setText("\U0001f602 +2 золота! Серьёзно?")
                self._code_result.setStyleSheet("color:#ffcc00; font-size:13px; padding:6px;")
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        elif code == "1874":
            valid = True
            if "1874" not in used_codes:
                used_codes.append("1874")
                self.shop.add_keys(1)
                self._animate_currency_add(1, "keys")
                self._code_result.setText("\U0001f511 +1 ключ! Исторический!")
                self._code_result.setStyleSheet("color:#dda644; font-size:13px; font-weight:bold; padding:6px;")
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        elif code == "\u043a\u0430\u0438\u044220":
            valid = True
            if "\u043a\u0430\u0438\u044220" not in used_codes:
                used_codes.append("\u043a\u0430\u0438\u044220")
                self.shop.add_gold(111)
                self._animate_currency_add(111, "gold")
                self._code_result.setText("\U0001f3eb +111 золота! КАИТ рулит!")
                self._code_result.setStyleSheet("color:#ffcc00; font-size:13px; font-weight:bold; padding:6px;")
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        elif code == "\u043a\u0440\u0443\u0430\u0441\u0441\u0430\u043d":
            valid = True
            if "\u043a\u0440\u0443\u0430\u0441\u0441\u0430\u043d" not in used_codes:
                used_codes.append("\u043a\u0440\u0443\u0430\u0441\u0441\u0430\u043d")
                self._spawn_sticker("sticker_kru.jpg", remove_bg="oval")
                self._code_result.setText("\U0001f950 Круассан наклейка!")
                self._code_result.setStyleSheet("color:#dda644; font-size:13px; font-weight:bold; padding:6px;")
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        elif code == "void":
            valid = True
            if "void" not in used_codes:
                used_codes.append("void")
                purchased = self.config.setdefault("shop_purchased_themes", [])
                if "void_purple" not in purchased:
                    purchased.append("void_purple")
                self._code_result.setText("\U0001f573\ufe0f Пустота разблокирована...")
                self._code_result.setStyleSheet("color:#9933ff; font-size:13px; font-weight:bold; padding:6px;")
                self._refresh_themes()
            else:
                self._code_result.setText("Код уже использован.")
                self._code_result.setStyleSheet("color:#888; font-size:11px; padding:6px;")

        if not valid:
            self._code_result.setText("\u274c Код не распознан. Попытка засчитана.")
            self._code_result.setStyleSheet("color:#cc4444; font-size:11px; padding:6px;")
            # Ачивка за неудачу
            self.config["_code_fail"] = True

        # Ачивка за верный код
        if valid:
            self.config[f"_code_{code}"] = True

        from modules.config import save_config
        save_config(self.config)
        self._code_input.clear()

    def _spawn_bage_sticker(self):
        """Наклейка MSN bage — обёртка над универсальным _spawn_sticker."""
        self._spawn_sticker("bage.png", remove_bg="white", action="modern_windows")

    def _spawn_sticker(self, image_file, remove_bg=None, action=None):
        """Spawn a sticker inside the codes window only.
        Stickers do NOT persist between sessions.
        remove_bg: "white"/"black"/"oval"/None
        action: callback on click, or None
        """
        import os, random
        from PyQt6.QtGui import QTransform, QImage

        # Стикеры появляются только в окне кодов
        if not hasattr(self, '_codes_window') or not self._codes_window or not self._codes_window.isVisible():
            return

        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        img_path = os.path.join(base, image_file)
        img = QImage(img_path)
        if img.isNull():
            return

        img = img.convertToFormat(QImage.Format.Format_ARGB32)

        if remove_bg == "white":
            for y in range(img.height()):
                for x in range(img.width()):
                    c = img.pixelColor(x, y)
                    if c.red() > 220 and c.green() > 220 and c.blue() > 220:
                        img.setPixelColor(x, y, QColor(0, 0, 0, 0))
        elif remove_bg == "black":
            for y in range(img.height()):
                for x in range(img.width()):
                    c = img.pixelColor(x, y)
                    if c.red() < 35 and c.green() < 35 and c.blue() < 35:
                        img.setPixelColor(x, y, QColor(0, 0, 0, 0))
        elif remove_bg == "oval":
            from PyQt6.QtGui import QPainterPath
            w, h = img.width(), img.height()
            mask = QImage(w, h, QImage.Format.Format_ARGB32)
            mask.fill(QColor(0, 0, 0, 0))
            mp = QPainter(mask)
            mp.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, w, h)
            mp.setClipPath(path)
            mp.drawImage(0, 0, img)
            mp.end()
            img = mask

        pm = QPixmap.fromImage(img)

        # Размер наклейки 140-210px (x2 от раньше)
        scale = random.uniform(1.0, 1.5)
        sz = int(140 * scale)
        pm = pm.scaled(sz, sz, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # Random rotation -20..20°
        angle = random.uniform(-20, 20)
        pm = pm.transformed(QTransform().rotate(angle), Qt.TransformationMode.SmoothTransformation)

        # Track sticker count (for achievements, не персистим сами стикеры)
        sticker_count = len(getattr(self, '_active_stickers', []))
        self.config["_sticker_count"] = sticker_count + 1

        # Спавн стикера в окне кодов
        parent = self._codes_window
        sticker = QLabel(parent)
        sticker.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        sticker.setPixmap(pm)
        sticker.setFixedSize(pm.width(), pm.height())
        sticker.setStyleSheet("background:transparent; border:none;")
        sticker.setCursor(Qt.CursorShape.PointingHandCursor)

        # Random position inside codes window
        max_x = max(10, parent.width() - pm.width() - 10)
        max_y = max(200, parent.height() - pm.height() - 10)
        rx = random.randint(10, max_x)
        ry = random.randint(150, max_y)
        sticker.move(rx, ry)
        sticker.show()
        sticker.raise_()

        # Default action for bage: open modern_windows
        if image_file == "bage.png" or action == "modern_windows":
            sticker.mousePressEvent = lambda ev: self._on_bage_click(sticker)

        # Store reference
        if not hasattr(self, '_active_stickers'):
            self._active_stickers = []
        self._active_stickers.append(sticker)

    def _animate_currency_add(self, amount, currency_type="gold"):
        """Animate currency addition with floating text and counter increment."""
        import random
        label_text = f"+{amount} {'золота' if currency_type == 'gold' else 'ключей'}!"
        color = "#ffcc00" if currency_type == "gold" else "#dda644"

        float_label = QLabel(label_text, self)
        float_label.setStyleSheet(f"color:{color}; font-size:18px; font-weight:bold; background:transparent;")
        float_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        float_label.adjustSize()

        # Random position
        x = random.randint(50, max(51, self.width() - 150))
        y = random.randint(100, max(101, self.height() - 200))
        float_label.move(x, y)
        float_label.show()
        float_label.raise_()

        # Animate upward and fade
        anim = QPropertyAnimation(float_label, b"pos")
        anim.setDuration(1500)
        anim.setStartValue(QPoint(x, y))
        anim.setEndValue(QPoint(x, y - 80))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(float_label.deleteLater)
        anim.start()
        # Store ref to prevent GC
        if not hasattr(self, '_float_anims'):
            self._float_anims = []
        self._float_anims.append(anim)

        # Animate counter increment (только если открыто окно магазина)
        sw = getattr(self, "_shop_win", None)
        lbl = None
        if currency_type == "gold":
            lbl = getattr(sw, "_wallet_gold_label", None) if sw else None
        else:
            lbl = getattr(sw, "_wallet_keys_label", None) if sw else None
        if lbl is None:
            return

        current_text = lbl.text()
        current = int(current_text) if current_text.isdigit() else 0
        target = current + amount

        self._currency_anim_target = target
        self._currency_anim_current = current
        self._currency_anim_type = currency_type

        timer = QTimer(self)
        timer.setInterval(30)
        def tick():
            self._currency_anim_current += max(1, (self._currency_anim_target - self._currency_anim_current) // 5)
            if self._currency_anim_current >= self._currency_anim_target:
                self._currency_anim_current = self._currency_anim_target
                timer.stop()
                timer.deleteLater()
            lbl.setText(str(self._currency_anim_current))
        timer.timeout.connect(tick)
        timer.start()

    def _on_bage_click(self, sticker):
        """Клик по наклейке — открыть современную тему."""
        purchased = self.config.setdefault("shop_purchased_themes", [])
        if "modern_windows" not in purchased:
            purchased.append("modern_windows")
            from modules.config import save_config
            save_config(self.config)
        self._select_theme("modern_windows")
        self._emoji_boom_from_widget(sticker, 20)
        self._refresh_themes()

    def _tab_log(self):
        w = QWidget(); l = QVBoxLayout(w)
        self.log_table = QTableWidget(0, 3)
        self.log_table.setHorizontalHeaderLabels(["Время", "Дата", "Memo"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        l.addWidget(self.log_table)
        return w

    def _tab_settings(self):
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        inner_w = QWidget()
        inner_w.setStyleSheet("background:transparent;")
        l = QVBoxLayout(inner_w)
        l.setContentsMargins(6, 6, 6, 6)
        l.setSpacing(8)

        self.chk_sound = QCheckBox("\U0001f50a Звуки")
        self.chk_sound.setChecked(True)
        l.addWidget(self.chk_sound)

        self.chk_overlay = QCheckBox("\U0001f386 Оверлеи")
        self.chk_overlay.setChecked(True)
        l.addWidget(self.chk_overlay)

        l.addWidget(QLabel("Прозрачность фона:"))
        self.sl_bg = QSlider(Qt.Orientation.Horizontal)
        self.sl_bg.setRange(20, 100)
        self.sl_bg.setValue(self._bg_opacity)
        self.sl_bg.valueChanged.connect(self._on_bg_opacity)
        l.addWidget(self.sl_bg)

        l.addWidget(QLabel("Прозрачность элементов:"))
        self.sl_wg = QSlider(Qt.Orientation.Horizontal)
        self.sl_wg.setRange(30, 100)
        self.sl_wg.setValue(self._widget_opacity)
        self.sl_wg.valueChanged.connect(self._on_wg_opacity)
        l.addWidget(self.sl_wg)

        l.addWidget(QLabel("Прозрачность эффектов фона:"))
        self.sl_fx = QSlider(Qt.Orientation.Horizontal)
        self.sl_fx.setRange(0, 100)
        self.sl_fx.setValue(self._fx_opacity)
        self.sl_fx.valueChanged.connect(self._on_fx_opacity)
        l.addWidget(self.sl_fx)

        l.addWidget(QLabel("Порог срабатывания (%):"))
        thr_row = QHBoxLayout()
        self.sl_threshold = QSlider(Qt.Orientation.Horizontal)
        self.sl_threshold.setRange(1, 500)
        self.sl_threshold.setValue(int(self.config.get("pixel_threshold", 0.3) * 100))
        self.sl_threshold.valueChanged.connect(self._on_threshold)
        thr_row.addWidget(self.sl_threshold)
        self.thr_label = QLabel(f"{self.config.get('pixel_threshold', 0.3):.2f}%")
        self.thr_label.setFixedWidth(55)
        thr_row.addWidget(self.thr_label)
        l.addLayout(thr_row)

        # ── Показать зону — крупная заметная кнопка ──
        sep0 = QFrame()
        sep0.setFixedHeight(1)
        sep0.setStyleSheet("background:#553311;")
        l.addWidget(sep0)

        self.btn_show_zone = QPushButton("\U0001f441  Показать / скрыть зону выборки")
        self.btn_show_zone.setFixedHeight(44)
        self.btn_show_zone.setStyleSheet(
            "QPushButton{background:rgba(40,20,5,220);border:2px solid #886622;"
            "border-radius:7px;color:#ffcc44;font-size:13px;font-weight:bold;padding:8px 12px;}"
            "QPushButton:hover{background:rgba(60,30,8,240);border-color:#ffaa22;color:#ffdd66;}"
        )
        self.btn_show_zone.clicked.connect(self.request_show_zone)
        l.addWidget(self.btn_show_zone)

        info = QLabel("Ctrl+Shift+F2 — показать/скрыть\nF12 — экстренный стоп\nПри закрытии — свернуть в трей")
        info.setWordWrap(True)
        info.setStyleSheet("color:#555; font-size:10px; padding:4px 0;")
        l.addWidget(info)

        l.addStretch(1)

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background:#333;")
        l.addWidget(sep2)

        extras_label = QLabel("Дополнительно:")
        extras_label.setStyleSheet("color:#888; font-size:11px; font-weight:bold; padding-top:4px;")
        l.addWidget(extras_label)

        BTN_EXTRA_STYLE = (
            "QPushButton{background:rgba(20,8,5,200);border:1px solid #553322;"
            "border-radius:6px;color:#cc8844;font-size:13px;font-weight:bold;padding:10px;}"
            "QPushButton:hover{border-color:#ff8844;color:#ffaa44;background:rgba(30,12,8,220);}"
        )
        btn_log = QPushButton("\U0001f4cb  Открыть лог")
        btn_log.setStyleSheet(BTN_EXTRA_STYLE)
        btn_log.setMinimumHeight(44)
        btn_log.clicked.connect(self._open_log_window)
        l.addWidget(btn_log)

        btn_codes = QPushButton("\U0001f511  Секретные коды")
        btn_codes.setStyleSheet(BTN_EXTRA_STYLE)
        btn_codes.setMinimumHeight(44)
        btn_codes.clicked.connect(self._open_codes_window)
        l.addWidget(btn_codes)

        l.addSpacing(8)

        sep_wipe = QFrame()
        sep_wipe.setFixedHeight(1)
        sep_wipe.setStyleSheet("background:#882222;")
        l.addWidget(sep_wipe)

        wipe_lbl = QLabel(
            "Опасная зона: сбросит двойки, ачивки, стрик, помилования, квесты и связанный прогресс в config. "
            "В Supabase останутся ФИО и ник; прогресс и валюта на сервере обнулятся."
        )
        wipe_lbl.setWordWrap(True)
        wipe_lbl.setStyleSheet("color:#aa5555; font-size:10px; padding:4px 0;")
        l.addWidget(wipe_lbl)

        self.btn_wipe_account = QPushButton("\U0001f5d1 Очистить все данные аккаунта")
        self.btn_wipe_account.setMinimumHeight(44)
        self.btn_wipe_account.setStyleSheet(
            "QPushButton{background:rgba(50,8,8,230);border:2px solid #aa2020;"
            "border-radius:7px;color:#ff6666;font-size:13px;font-weight:bold;padding:10px;}"
            "QPushButton:hover{background:rgba(80,12,12,240);border-color:#ff4040;color:#ffaaaa;}"
        )
        self.btn_wipe_account.clicked.connect(self._on_wipe_account_clicked)
        l.addWidget(self.btn_wipe_account)

        scroll.setWidget(inner_w)
        outer.addWidget(scroll)
        return w

    def _on_wipe_account_clicked(self):
        """Двойное подтверждение перед полной очисткой прогресса."""
        r1 = QMessageBox.question(
            self,
            "Очистка прогресса",
            "Удалить весь игровой прогресс на этом ПК и синхронизировать сброс с облаком?\n\n"
            "Останутся: ФИО и никнейм в базе, купленные темы, настройки зоны, цвета и хоткеи.\n\n"
            "Будут обнулены: счётчик двоек, ачивки, стрик, помилования, дневники, секретные коды в конфиге, "
            "квесты, золото и ключи (к стартовым значениям магазина).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if r1 != QMessageBox.StandardButton.Yes:
            return
        r2 = QMessageBox.warning(
            self,
            "Последнее предупреждение",
            "Это действие необратимо. Точно очистить все данные аккаунта?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if r2 != QMessageBox.StandardButton.Yes:
            return
        self.account_wipe_confirmed.emit()

    def _tab_goals(self):
        """Вкладка «Цели»: квест дня + дозированное открытие контента."""
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(8)
        l.setContentsMargins(8, 8, 8, 8)

        # ── Квест дня ─────────────────────────────────────────
        q_hdr = QLabel("🎯 Квест дня")
        q_hdr.setStyleSheet("color:#ffcc00; font-size:12px; font-weight:bold; padding:4px 0;")
        l.addWidget(q_hdr)

        self._q_options_box = QFrame()
        self._q_options_box.setStyleSheet("QFrame{background:rgba(15,5,5,150);border:1px solid #442222;border-radius:8px;}")
        ql = QVBoxLayout(self._q_options_box)
        ql.setContentsMargins(10, 10, 10, 10)
        ql.setSpacing(6)

        self._q_option_btns = []
        for _ in range(3):
            btn = QPushButton("—")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton{color:#cc8844;background:rgba(20,8,5,200);border:1px solid #553311;"
                "border-radius:6px;font-size:12px;font-weight:bold;padding:10px;}"
                "QPushButton:hover{border-color:#884422;color:#ffaa55;background:rgba(30,12,8,220);}"
            )
            btn.setEnabled(False)
            ql.addWidget(btn)
            self._q_option_btns.append(btn)
        l.addWidget(self._q_options_box)

        self._q_selected_label = QLabel("")
        self._q_selected_label.setStyleSheet("color:#ffcc00; font-size:12px; font-weight:bold;")
        l.addWidget(self._q_selected_label)

        self._q_progress_pb = QProgressBar()
        self._q_progress_pb.setRange(0, 100)
        self._q_progress_pb.setFixedHeight(10)
        self._q_progress_pb.setFormat("")
        l.addWidget(self._q_progress_pb)

        self._q_progress_label = QLabel("")
        self._q_progress_label.setStyleSheet("color:#888; font-size:10px;")
        l.addWidget(self._q_progress_label)

        self._q_bonus_label = QLabel("")
        self._q_bonus_label.setStyleSheet("color:#44aa66; font-size:11px; font-weight:bold;")
        l.addWidget(self._q_bonus_label)

        # ── Дозированное открытие ────────────────────────────
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background:#333;")
        l.addWidget(sep)

        gate_hdr = QLabel("🔒 Дозированное открытие контента")
        gate_hdr.setStyleSheet("color:#cc8844; font-size:12px; font-weight:bold; padding:2px 0;")
        l.addWidget(gate_hdr)

        self._gate_stats_label = QLabel("")
        self._gate_stats_label.setStyleSheet("color:#ffcc00; font-size:11px; font-weight:bold;")
        l.addWidget(self._gate_stats_label)
        self._gate_stats_pb = QProgressBar()
        self._gate_stats_pb.setRange(0, 100)
        self._gate_stats_pb.setFixedHeight(10)
        self._gate_stats_pb.setFormat("")
        l.addWidget(self._gate_stats_pb)

        self._gate_shop_label = QLabel("")
        self._gate_shop_label.setStyleSheet("color:#dda644; font-size:11px; font-weight:bold;")
        l.addWidget(self._gate_shop_label)
        self._gate_shop_pb = QProgressBar()
        self._gate_shop_pb.setRange(0, 100)
        self._gate_shop_pb.setFixedHeight(10)
        self._gate_shop_pb.setFormat("")
        l.addWidget(self._gate_shop_pb)

        self._gate_themes_label = QLabel("")
        self._gate_themes_label.setStyleSheet("color:#cc66ff; font-size:11px; font-weight:bold;")
        l.addWidget(self._gate_themes_label)
        self._gate_themes_pb = QProgressBar()
        self._gate_themes_pb.setRange(0, 100)
        self._gate_themes_pb.setFixedHeight(10)
        self._gate_themes_pb.setFormat("")
        l.addWidget(self._gate_themes_pb)

        l.addStretch(1)

        # Первичное заполнение
        self._refresh_goals_tab_ui()
        return w

    def _refresh_goals_tab_ui(self):
        """Обновляет UI квеста/гейтов."""
        # ── Квест дня ──
        q = self.daily_quests.get_selected_quest()
        if q is None:
            # Показываем варианты
            for btn in self._q_option_btns:
                btn.setEnabled(False)
                btn.setText("—")
            opts = self.daily_quests.get_today_options(3)
            for i, quest in enumerate(opts):
                if i >= len(self._q_option_btns):
                    break
                btn = self._q_option_btns[i]
                btn.setText(f"{quest.icon} {quest.title}")
                can_pick = self.daily_quests.can_select_quest_today()
                btn.setEnabled(can_pick)
                try:
                    btn.clicked.disconnect()
                except Exception:
                    pass
                btn.clicked.connect(lambda checked, qid=quest.id, b=btn: self._select_daily_quest(qid, b))
            self._q_selected_label.setText("Выбери один квест на сегодня.")
            self._q_progress_pb.setValue(0)
            self._q_progress_label.setText("")
            self._q_bonus_label.setText("")
        else:
            cur, goal = self.daily_quests.get_progress()[1:]
            completed = cur >= goal
            self._q_selected_label.setText(f"{q.icon} {q.title}")
            pct = min(100, int(cur / max(1, goal) * 100))
            self._q_progress_pb.setValue(pct)
            self._q_progress_label.setText(f"{cur}/{goal}")
            if completed:
                self._q_bonus_label.setText(
                    f"Бафф: +{self.daily_quests.gold_per_two()} голды за двойку (сегодня)."
                    if self.daily_quests.is_bonus_active()
                    else "Квест выполнен: бафф активируется."
                )
            else:
                self._q_bonus_label.setText("Бафф появится после выполнения.")

            # Кнопки выбора недоступны после выбора
            opts = self.daily_quests.get_today_options(3)
            for i, quest in enumerate(opts):
                if i >= len(self._q_option_btns):
                    break
                btn = self._q_option_btns[i]
                btn.setEnabled(False)
                btn.setText(f"{quest.icon} {quest.title}")

        # ── Дозированные гейты ──
        self._refresh_content_gate_ui()

    def _refresh_content_gate_ui(self):
        """UI прогресса по гейтингу вкладок/магазина."""
        total_twos = int(self.stats.total)
        mercy_total = int(self.stats.mercy_total)

        stats_twos_req = 2
        stats_mercy_req = 5
        shop_twos_req = 15
        themes_twos_req = 20

        # Статистика: 2 двойки + 5 помилований
        stats_ok = total_twos >= stats_twos_req and mercy_total >= stats_mercy_req
        twos_pct = min(1.0, total_twos / max(1, stats_twos_req))
        mercy_pct = min(1.0, mercy_total / max(1, stats_mercy_req))
        # прогресс берём как "минимум требований" (честно для AND-условия)
        stats_prog = min(twos_pct, mercy_pct)
        self._gate_stats_label.setText(
            f"Статистика: {'✅' if stats_ok else '🔒'} {total_twos}/{stats_twos_req} двойки и {mercy_total}/{stats_mercy_req} помилования"
        )
        self._gate_stats_pb.setValue(int(stats_prog * 100))

        # Магазин: 15 двоек
        shop_ok = total_twos >= shop_twos_req
        shop_prog = min(1.0, total_twos / max(1, shop_twos_req))
        self._gate_shop_label.setText(f"Магазин: {'✅' if shop_ok else '🔒'} {total_twos}/{shop_twos_req} двойки")
        self._gate_shop_pb.setValue(int(shop_prog * 100))

        # Огни/темы: 20 двоек
        themes_ok = total_twos >= themes_twos_req
        themes_prog = min(1.0, total_twos / max(1, themes_twos_req))
        self._gate_themes_label.setText(f"Огни: {'✅' if themes_ok else '🔒'} {total_twos}/{themes_twos_req} двойки")
        self._gate_themes_pb.setValue(int(themes_prog * 100))

    def _select_daily_quest(self, quest_id: str, btn: QPushButton | None = None):
        if not self.daily_quests.select_quest_today(quest_id):
            return
        if btn is not None:
            self._confetti_boom_from_widget(btn, 200)
        self.refresh_all()

    def _calc_content_gate(self) -> dict:
        """Считает разрешения на открытие контента."""
        total_twos = int(self.stats.total)
        mercy_total = int(self.stats.mercy_total)
        return {
            # Статистика: 2 двойки + 5 помилований
            "stats": total_twos >= 2 and mercy_total >= 5,
            # Магазин: 15 двоек
            "shop": total_twos >= 15,
            # Огни/Темы: 20 двоек
            "themes": total_twos >= 20,
        }

    def _apply_content_gate(self):
        """Обновляет доступность вкладок и кнопки магазина + триггерит конфетти при открытии нового."""
        gate = self._calc_content_gate()
        prev = dict(getattr(self, "_content_gate_prev", {}))

        # Обновляем кнопки/вкладки
        if self._shop_btn is not None:
            can_shop = gate["shop"]
            self._shop_btn.setEnabled(can_shop)
            if not can_shop:
                self._shop_btn.setToolTip("🔒 Магазин закрыт. Нужны 15 двоек.")
                # лёгкое "серение"
                self._shop_btn.setStyleSheet(
                    "QPushButton{border:2px solid #333;color:#666;font-size:18px;"
                    "padding:0;border-radius:8px;background:rgba(30,15,0,120);min-height:0;min-width:0;}"
                    "QPushButton:hover{background:rgba(60,30,0,200);border-color:#555;}"
                )
            else:
                self._shop_btn.setToolTip("Магазин")
                # вернём основной стиль (похожий на исходный)
                c = self._current_theme.get("colors", {})
                _p = c.get("primary", "#cc8844")
                self._shop_btn.setStyleSheet(
                    "QPushButton{border:2px solid #886611;color:#ffcc00;font-size:18px;"
                    "padding:0;border-radius:8px;background:rgba(30,15,0,200);min-height:0;min-width:0;}"
                    "QPushButton:hover{background:rgba(60,30,0,230);border-color:#ffaa00;}"
                )

        if self.tabs is not None:
            # Статистика
            if self._tab_idx_stats is not None:
                can_stats = gate["stats"]
                self.tabs.setTabEnabled(self._tab_idx_stats, can_stats)
                self.tabs.setTabText(
                    self._tab_idx_stats,
                    "\U0001f512 🔒 Стат" if not can_stats else "\U0001f4ca Стат"
                )
            # Огни/темы
            if self._tab_idx_themes is not None:
                can_themes = gate["themes"]
                self.tabs.setTabEnabled(self._tab_idx_themes, can_themes)
                self.tabs.setTabText(
                    self._tab_idx_themes,
                    "\U0001f525 🔒 Огни" if not can_themes else "\U0001f525 Огни"
                )

        # Конфетти при переходе locked -> unlocked
        for k in ("stats", "shop", "themes"):
            if not prev.get(k, False) and gate.get(k, False):
                self._confetti_boom_at_center(220 if k != "shop" else 240)

        self._content_gate_prev = gate

    def _confetti_boom_at_center(self, count=220):
        """Конфетти от центра панели."""
        try:
            boom = getattr(self, "_confetti_boom", None)
            if not boom:
                return
            gp = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
            boom.burst(gp.x(), gp.y(), count)
        except Exception:
            pass

    def _open_log_window(self):
        """Открывает лог в отдельном окне."""
        if hasattr(self, '_log_window') and self._log_window and self._log_window.isVisible():
            self._log_window.raise_()
            self._log_window.activateWindow()
            return
        self._log_window = QWidget()
        self._log_window.setWindowTitle("INFERNO — Лог")
        self._log_window.setFixedSize(420, 500)
        self._log_window.setStyleSheet("background:rgb(15,5,5);")
        vl = QVBoxLayout(self._log_window); vl.setContentsMargins(6, 6, 6, 6)
        hdr = QLabel("\U0001f4cb ЛОГ ОБНАРУЖЕНИЙ")
        hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.setStyleSheet("color:#cc8844; font-size:14px; font-weight:bold; padding:6px;")
        vl.addWidget(hdr)
        # Пересоздаём таблицу лога
        self.log_table = QTableWidget(0, 3)
        self.log_table.setHorizontalHeaderLabels(["Время", "Дата", "Memo"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.setStyleSheet(
            "QTableWidget{background:rgba(10,3,3,200);color:#ccc;gridline-color:#332222;border:none;}"
            "QHeaderView::section{background:rgba(30,10,5,220);color:#cc8844;border:1px solid #442222;font-weight:bold;}"
        )
        vl.addWidget(self.log_table)
        self._log_window.show()
        # Заполняем данными
        logs = self.stats.get_recent_log(50)
        self.log_table.setRowCount(len(logs))
        for i, e in enumerate(logs):
            self.log_table.setItem(i, 0, QTableWidgetItem(e["time"]))
            self.log_table.setItem(i, 1, QTableWidgetItem(e["date"]))
            self.log_table.setItem(i, 2, QTableWidgetItem(e["memo"]))

    def _open_codes_window(self):
        """Открывает коды в отдельном окне."""
        if hasattr(self, '_codes_window') and self._codes_window and self._codes_window.isVisible():
            self._codes_window.raise_()
            self._codes_window.activateWindow()
            return
        self._codes_window = QWidget()
        self._codes_window.setWindowTitle("INFERNO — Секретные коды")
        self._codes_window.setFixedSize(420, 500)
        self._codes_window.setStyleSheet("background:rgb(15,5,5);")
        vl = QVBoxLayout(self._codes_window); vl.setContentsMargins(6, 6, 6, 6)
        # Пересоздаём UI кодов
        icon = QLabel("\U0001f511")
        icon.setFont(QFont("Segoe UI", 36))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(icon)
        title = QLabel("СЕКРЕТНЫЕ КОДЫ")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#aa7733;")
        vl.addWidget(title)
        sub = QLabel("Введи код и нажми Enter")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color:#555; font-size:10px;")
        vl.addWidget(sub)
        self._code_input = QLineEdit()
        self._code_input.setPlaceholderText("Введите код...")
        self._code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._code_input.setMaxLength(50)
        self._code_input.setStyleSheet(
            "QLineEdit{background:rgba(0,0,0,120);border:2px solid #555;"
            "border-radius:8px;color:#ffcc00;font-size:14px;padding:8px;"
            "font-family:Consolas;letter-spacing:2px;}"
            "QLineEdit:focus{border-color:#ffaa00;}"
        )
        self._code_input.returnPressed.connect(self._on_code_submit)
        vl.addWidget(self._code_input)
        self._code_result = QLabel("")
        self._code_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._code_result.setStyleSheet("color:#666; font-size:11px; padding:6px;")
        self._code_result.setWordWrap(True)
        vl.addWidget(self._code_result)
        vl.addStretch()
        self._codes_window.show()
        self._code_input.setFocus()

    # ── Callbacks ─────────────────────────────────────────────
    def _on_bg_opacity(self, v):
        self._bg_opacity = v; self.config["bg_opacity"] = v; self.update()

    def _on_wg_opacity(self, v):
        self._widget_opacity = v; self.config["widget_opacity"] = v; self._apply_style()

    def _on_fx_opacity(self, v):
        self._fx_opacity = v; self.config["fx_opacity"] = v; self.update()

    def _on_threshold(self, v):
        pct = v / 100.0
        self.thr_label.setText(f"{pct:.2f}%")
        self.config["pixel_threshold"] = pct
        self.threshold_changed.emit(pct / 100.0)

    # ═══════════════════════════════════════════════════════════
    #  refresh_all
    # ═══════════════════════════════════════════════════════════
    def refresh_all(self):
        s = self.stats
        today = s.get_today_count()
        total = s.get_all_time_count()
        streak = s.streak
        mt = s.mercy_total

        # Ретро-тема: не перезаписываем :D / >:D когда смайлик активен
        if not (self._current_theme.get("counter_smiley") and getattr(self, '_retro_smiley_on', False)):
            self.counter_label.setText(str(today))
        digits = len(str(max(today, 1)))
        fpt = COUNTER_FONT_PT
        if digits == 3: fpt = int(COUNTER_FONT_PT * 0.78)
        elif digits == 4: fpt = int(COUNTER_FONT_PT * 0.62)
        elif digits >= 5: fpt = int(COUNTER_FONT_PT * 0.50)
        self._set_counter_style(fpt)

        self.total_big.setText(f"\U0001f480 ВСЕГО: {total}")
        self.mercy_big.setText(f"\U0001f54a ПОМИЛОВАНО: {mt}")
        self._update_streak_display(streak)

        # Мотивационная фраза (меняется каждые 5с через refresh_all)
        if MOTIVATIONAL_QUOTES:
            self.quote_label.setText(f"\u00ab {MOTIVATIONAL_QUOTES[self._quote_index % len(MOTIVATIONAL_QUOTES)]} \u00bb")
            self._quote_index += 1

        rn, re = get_rank(total)
        self.rank_label.setText(f"{re} {rn}")
        _, prog, nxt = get_rank_progress(total)
        self.rank_bar.setValue(prog)
        self.rank_bar.setFormat(f"  {prog}%  ")
        self.rank_next_label.setText(f"\u2192 {nxt}")

        if self._expanded:
            week = s.get_week_count()
            month = s.get_month_count()
            # sv: [0]=today, [1]=week, [2]=month, [3]=alltime, [4]=mercies
            for i, v in enumerate([today, week, month, total, mt]):
                if i < len(self.sv):
                    self.sv[i].setText(str(v))
            # Стрик в объединённой вкладке
            if hasattr(self, '_stat_streak_val'):
                self._stat_streak_val.setText(f"{streak} дн")
            rec = s.get_records()
            if hasattr(self, '_rec_cards'):
                self._rec_cards["max_day"].setText(str(rec['max_day']))
                self._rec_cards["max_week"].setText(str(rec['max_week']))
                self._rec_cards["max_combo"].setText(str(rec['max_combo']))
                self._rec_cards["streak"].setText(f"{rec['streak']} дн")
                self._rec_cards["total"].setText(str(rec['total']))
                self._rec_cards["mercy"].setText(str(rec.get('mercy_total', 0)))
            self._refresh_achievements()
            self._refresh_themes()
            self._refresh_log()

        # Гейтинг (магазин/огни/статистика) всегда актуален
        self._apply_content_gate()

        # Обновляем UI целей только когда вкладка активна (чтобы не дёргать соединения)
        if getattr(self, "_tab_idx_goals", None) is not None and self.tabs.currentIndex() == self._tab_idx_goals:
            self._refresh_goals_tab_ui()

    def _set_counter_style(self, fpt, font_override=None):
        font = font_override or self._current_theme.get("counter_font", FONT_FAMILY_DISPLAY)
        scale = self._current_theme.get("counter_font_scale", 1.0)
        fpt = int(fpt * scale)
        # Ретро/Зловещая/Адская: текст QLabel прозрачный, рисуем счётчик в paintEvent
        if self._current_theme.get("counter_smiley") or self._current_theme.get("counter_outline") or self._current_theme.get("counter_outline_color"):
            self.counter_label.setStyleSheet(
                f"color: transparent; font-size: {fpt}px; "
                f"font-weight: bold; font-family: {font}; "
                "padding: 0; margin: 0; line-height: 1;"
            )
        else:
            counter_color = self._current_theme.get("counter_color",
                            self._current_theme['colors']['primary'])
            self.counter_label.setStyleSheet(
                f"color: {counter_color}; font-size: {fpt}px; "
                f"font-weight: bold; font-family: {font}; "
                "padding: 0; margin: 0; line-height: 1;"
            )

    def _update_streak_display(self, streak):
        if streak <= 0:
            self.streak_label.setText("\U0001f4a4 СТРИК: нет")
            self.streak_label.setStyleSheet(
                f"color:#443333; font-size:16px; font-weight:bold; font-family:{FONT_FAMILY_DISPLAY}; padding:2px 0;"
            )
            return
        if streak >= 30:
            phrases = [
                f"\u2620\ufe0f ВЕЧНЫЙ ОГОНЬ: {streak} ДНЕЙ",
                f"\U0001f441 АБСОЛЮТНАЯ ТЬМА: {streak} ДНЕЙ",
            ]
            fsize, color = 24, self._current_theme["colors"]["primary"]
        elif streak >= 15:
            phrases = [
                f"\u26a1 СТРИК ЯРОСТИ: {streak} ДНЕЙ",
                f"\U0001f5e1 {streak} ДНЕЙ БЕЗ ПОЩАДЫ!",
            ]
            fsize, color = 22, self._current_theme["colors"]["secondary"]
        elif streak >= 7:
            phrases = [
                f"\U0001f525\U0001f525 СТРИК: {streak} ДНЕЙ!",
                f"\u2694\ufe0f НЕУДЕРЖИМ: {streak} ДНЕЙ",
            ]
            fsize, color = 20, "#ff6600"
        else:
            dw = "ДЕНЬ" if streak == 1 else ("ДНЯ" if streak < 5 else "ДНЕЙ")
            phrases = [f"\U0001f525 СТРИК: {streak} {dw}"]
            fsize, color = 18, "#ff8800"
        self.streak_label.setText(phrases[streak % len(phrases)])
        self.streak_label.setStyleSheet(
            f"color:{color}; font-size:{fsize}px; font-weight:bold; "
            f"font-family:{FONT_FAMILY_DISPLAY}; padding:2px 0; letter-spacing:1px;"
        )

    # ═══════════════════════════════════════════════════════════
    #  Ачивки (→ «Файлы {nickname}»)
    # ═══════════════════════════════════════════════════════════
    def _toggle_ach_category(self, cat_id):
        """Свернуть/развернуть категорию ачивок."""
        collapsed = self._ach_cat_collapsed.get(cat_id, False)
        self._ach_cat_collapsed[cat_id] = not collapsed
        if cat_id in self._ach_cat_widgets:
            btn, container = self._ach_cat_widgets[cat_id]
            container.setVisible(collapsed)
            txt = btn.text()
            if collapsed:
                btn.setText(txt.replace("▶", "▼"))
            else:
                btn.setText(txt.replace("▼", "▶"))

    def _refresh_achievements(self):
        while self.ach_layout.count():
            it = self.ach_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self._ach_cat_widgets = {}

        achs = self.stats.get_unlocked_achievements()
        unlocked_ids = {a["id"] for a in achs if a.get("unlocked")}
        total_count = len(ACHIEVEMENTS)
        unlocked_count = len(unlocked_ids)
        pct = int(unlocked_count / total_count * 100) if total_count else 0
        self.ach_total_label.setText(f"\U0001f4c2 Файлы: {unlocked_count}/{total_count} ({pct}%)")
        self.ach_total_bar.setValue(pct)
        st = self._get_stats_snapshot()

        random.seed(self._censor_seed)

        for cat_id, (cat_name, cat_desc) in CATEGORY_NAMES.items():
            cat_achs = [a for a in ACHIEVEMENTS if a.get("category") == cat_id]
            if not cat_achs:
                continue
            cat_unlocked = sum(1 for a in cat_achs if a["id"] in unlocked_ids)
            cat_total = len(cat_achs)
            cat_pct = int(cat_unlocked / cat_total * 100)

            is_collapsed = self._ach_cat_collapsed.get(cat_id, False)
            arrow = "▶" if is_collapsed else "▼"

            # ── Кнопка-заголовок категории ──
            cat_btn = QPushButton(f" {arrow}  {cat_name}   {cat_unlocked}/{cat_total} ({cat_pct}%)")
            cat_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            cat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cat_btn.setStyleSheet(
                "QPushButton{color:#ff6644;background:rgba(20,6,4,180);border:1px solid #552211;"
                "border-radius:5px;text-align:left;padding:5px 8px;font-size:11px;}"
                "QPushButton:hover{background:rgba(40,12,8,220);border-color:#883322;}"
            )
            self.ach_layout.addWidget(cat_btn)

            # Прогресс-бар категории
            cat_bar = QProgressBar()
            cat_bar.setRange(0, 100); cat_bar.setValue(cat_pct)
            cat_bar.setFixedHeight(8); cat_bar.setFormat("")
            self.ach_layout.addWidget(cat_bar)

            # ── Контейнер ачивок категории ──
            cat_container = QWidget()
            cat_lay = QVBoxLayout(cat_container)
            cat_lay.setContentsMargins(0, 0, 0, 0); cat_lay.setSpacing(2)
            cat_container.setVisible(not is_collapsed)

            self._ach_cat_widgets[cat_id] = (cat_btn, cat_container)
            cid = cat_id
            cat_btn.clicked.connect(lambda checked, c=cid: self._toggle_ach_category(c))


            for ach in cat_achs:
                is_unlocked = ach["id"] in unlocked_ids
                tier = ach.get("tier", "")

                f = QFrame()
                hl = QHBoxLayout(f); hl.setContentsMargins(8, 4, 8, 4)
                icon = QLabel(ach.get("icon", "?")); icon.setFont(QFont("Arial", 16)); icon.setFixedWidth(32)
                hl.addWidget(icon)
                vl = QVBoxLayout()

                if tier == "secret" and not is_unlocked:
                    nm = QLabel(f"{CENSOR_CHAR * 8}")
                    nm.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                    desc = QLabel(f"{CENSOR_CHAR * 20}")
                else:
                    nm = QLabel(ach["name"])
                    nm.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                    if is_unlocked:
                        desc = QLabel(ach.get("desc", ""))
                    else:
                        desc = QLabel(censor_text(ach.get("desc", ""), ratio=0.5))
                desc.setStyleSheet("color:#888;font-size:9px;")
                desc.setWordWrap(True)
                vl.addWidget(nm); vl.addWidget(desc)

                pk = ach.get("progress_key"); pt = ach.get("progress_target", 1)
                if pk and not is_unlocked:
                    cur = st.get(pk, 0)
                    prog = min(100, int(cur / pt * 100)) if pt > 0 else 0
                    pb = QProgressBar(); pb.setRange(0, 100); pb.setValue(prog)
                    pb.setFixedHeight(8); pb.setFormat("")
                    vl.addWidget(pb)
                    plab = QLabel(f"{cur}/???"); plab.setStyleSheet("color:#666;font-size:8px;")
                    vl.addWidget(plab)
                elif is_unlocked:
                    done = QLabel("\u2705 Получено!")
                    done.setStyleSheet("color:#00cc66;font-size:9px;font-weight:bold;")
                    vl.addWidget(done)
                hl.addLayout(vl)

                if tier == "legendary":
                    if is_unlocked:
                        f.setStyleSheet(
                            "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                            "stop:0 rgba(50,30,0,220),stop:0.5 rgba(80,40,0,220),stop:1 rgba(50,30,0,220));"
                            "border:2px solid #ffcc00;border-radius:6px;}"
                        )
                        nm.setStyleSheet("color:#ffcc00;font-size:12px;")
                    else:
                        f.setStyleSheet("QFrame{background:rgba(20,10,0,180);border:2px solid #886600;border-radius:6px;}")
                        nm.setStyleSheet("color:#aa8833;")
                elif tier == "gold":
                    if is_unlocked:
                        f.setStyleSheet(
                            "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                            "stop:0 rgba(50,40,0,220),stop:0.5 rgba(70,55,0,220),stop:1 rgba(50,40,0,220));"
                            "border:2px solid #ddaa00;border-radius:6px;}"
                        )
                        nm.setStyleSheet("color:#ffdd00;font-size:12px;")
                    else:
                        f.setStyleSheet("QFrame{background:rgba(20,15,0,180);border:2px solid #775500;border-radius:6px;}")
                        nm.setStyleSheet("color:#aa8833;")
                elif tier == "purple":
                    if is_unlocked:
                        f.setStyleSheet(
                            "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                            "stop:0 rgba(40,0,50,220),stop:0.5 rgba(60,0,80,220),stop:1 rgba(40,0,50,220));"
                            "border:2px solid #aa44ff;border-radius:6px;}"
                        )
                        nm.setStyleSheet("color:#cc66ff;font-size:12px;")
                    else:
                        f.setStyleSheet("QFrame{background:rgba(15,0,20,180);border:2px solid #552288;border-radius:6px;}")
                        nm.setStyleSheet("color:#774499;")
                elif tier == "secret":
                    if is_unlocked:
                        f.setStyleSheet(
                            "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                            "stop:0 rgba(30,0,30,220),stop:0.5 rgba(60,0,60,220),stop:1 rgba(30,0,30,220));"
                            "border:2px solid #cc00cc;border-radius:6px;}"
                        )
                        nm.setStyleSheet("color:#ff44ff;font-size:12px;")
                    else:
                        f.setStyleSheet("QFrame{background:rgba(10,0,10,180);border:2px dashed #440044;border-radius:6px;}")
                        nm.setStyleSheet("color:#333;")
                elif is_unlocked:
                    f.setStyleSheet("QFrame{background:rgba(30,8,8,200);border:1px solid #ff4040;border-radius:5px;}")
                    nm.setStyleSheet("color:#ffcc00;")
                else:
                    f.setStyleSheet("QFrame{background:rgba(10,3,3,150);border:1px solid #333;border-radius:5px;}")
                    nm.setStyleSheet("color:#777;")


                cat_lay.addWidget(f)

            self.ach_layout.addWidget(cat_container)

        random.seed()
        self.ach_layout.addStretch()

    # ═══════════════════════════════════════════════════════════
    #  Темы (Огни)
    # ═══════════════════════════════════════════════════════════
    def _get_theme_icon_path(self, theme_data):
        """Возвращает путь к иконке темы или None."""
        import os
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        # icon / theme_icon — прямое указание в теме
        icon = theme_data.get("icon") or theme_data.get("theme_icon")
        if icon:
            p = os.path.join(base, icon)
            if os.path.exists(p):
                return p
        # Для классических тем — первая картинка из bg_images
        imgs = theme_data.get("bg_images", [])
        if imgs:
            p = os.path.join(base, imgs[0])
            if os.path.exists(p):
                return p
        return None

    def _refresh_themes(self):
        # Сохраняем scroll-позицию
        scroll_pos = 0
        if hasattr(self, '_themes_scroll'):
            vbar = self._themes_scroll.verticalScrollBar()
            if vbar:
                scroll_pos = vbar.value()

        while self.themes_layout.count():
            it = self.themes_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        self._theme_item_widgets = []
        self._theme_cat_widgets = {}

        # Определяем закрытые категории
        unlocked_cats = self._get_completed_categories()
        total_twos = self.stats.total
        achs = self.stats.get_unlocked_achievements()
        total_achs = sum(1 for a in achs if a.get("unlocked"))
        max_combo = self.stats._cache.get("max_combo", 0)
        current_streak = self.stats.streak
        purchased = set(self.config.get("shop_purchased_themes", []))
        streak_lost = self.config.get("_streak_lost", False)
        all_themes = get_unlocked_themes(unlocked_cats, total_twos, total_achs, max_combo, current_streak, purchased, streak_lost)

        # Проверяем новые разблокировки
        current_unlocked = {t["id"] for t in all_themes if t["available"]}
        newly_unlocked = current_unlocked - self._known_unlocked_themes
        if newly_unlocked and self._known_unlocked_themes:
            for tid in newly_unlocked:
                tdata = next((t for t in all_themes if t["id"] == tid), None)
                if tdata:
                    self._show_theme_unlock_notification(tdata["name"])
        self._known_unlocked_themes = current_unlocked

        themes_map = {t["id"]: t for t in all_themes}

        categories_with_themes = get_themes_by_category()
        for cat_info, cat_themes in categories_with_themes:
            # Скрываем сатирическую вкладку если нет купленных тем из неё
            if cat_info["id"] == "satirical":
                purchased = set(self.config.get("shop_purchased_themes", []))
                sat_ids = {td["id"] for td in cat_themes}
                if not (purchased & sat_ids):
                    continue
            cat_id = cat_info["id"]
            is_collapsed = self._theme_cat_collapsed.get(cat_id, False)
            n_available = sum(1 for td in cat_themes if themes_map.get(td["id"], td).get("available", False))
            n_total = len(cat_themes)

            # ── Заголовок-кнопка категории ──
            arrow = "▶" if is_collapsed else "▼"
            cat_btn = QPushButton(f" {arrow}  {cat_info['name']}   ({n_available}/{n_total})")
            cat_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            cat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cat_btn.setStyleSheet(
                "QPushButton{color:#cc8844;background:rgba(20,8,4,180);border:1px solid #553311;"
                "border-radius:5px;text-align:left;padding:6px 8px;font-size:12px;}"
                "QPushButton:hover{background:rgba(40,16,8,220);border-color:#884422;}"
            )
            self.themes_layout.addWidget(cat_btn)

            # ── Контейнер тем категории ──
            cat_container = QWidget()
            cat_lay = QVBoxLayout(cat_container)
            cat_lay.setContentsMargins(0, 0, 0, 0); cat_lay.setSpacing(2)
            cat_container.setVisible(not is_collapsed)

            self._theme_cat_widgets[cat_id] = (cat_btn, cat_container)
            cid = cat_id  # capture
            cat_btn.clicked.connect(lambda checked, c=cid: self._toggle_theme_category(c))

            if not cat_themes:
                empty = QLabel(f"  {cat_info['desc']}")
                empty.setStyleSheet("color:#444;font-size:9px;font-style:italic;padding:2px 8px 8px 8px;border:none;background:transparent;")
                empty.setWordWrap(True)
                cat_lay.addWidget(empty)
            else:
                for theme_data in cat_themes:
                    t = themes_map.get(theme_data["id"], theme_data)
                    f = QFrame()
                    hl = QHBoxLayout(f); hl.setContentsMargins(6, 5, 6, 5); hl.setSpacing(8)
                    is_current = t["id"] == self._current_theme["id"]
                    tier = t.get("tier", "")
                    available = t.get("available", False)

                    # ── Иконка темы ──
                    preview = QLabel()
                    preview.setFixedSize(40, 40)
                    preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    icon_text = t.get("theme_icon_text")  # ("число", "#цвет")
                    icon_path = self._get_theme_icon_path(t) if available else None
                    if not available:
                        preview.setStyleSheet("background:#222;border:2px solid #333;border-radius:6px;")
                        preview.setText("🔒")
                    elif icon_text:
                        txt, clr = icon_text
                        # Проверяем: содержит ли текст эмодзи (не цифры/буквы)
                        is_emoji = any(ord(ch) > 0x2600 for ch in txt)
                        if is_emoji:
                            fsz = 22  # крупный эмодзи (+50%)
                        else:
                            fsz = 15 if len(txt) <= 2 else 11 if len(txt) == 3 else 9
                        preview.setText(txt)
                        preview.setFont(QFont("Segoe UI Emoji" if is_emoji else "Segoe UI", fsz, QFont.Weight.ExtraBold))
                        preview.setStyleSheet(
                            f"color:{clr};background:rgba(0,0,0,180);border:2px solid {clr};border-radius:6px;"
                        )
                    elif icon_path:
                        icon_sz = 45 if t.get("id") == "modern_windows" else 50 if t.get("category") == "classic" else 40
                        pm = QPixmap(icon_path).scaled(icon_sz, icon_sz, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        preview.setPixmap(pm)
                        preview.setScaledContents(False)
                        preview.setStyleSheet(f"border:2px solid {t['colors']['border']};border-radius:6px;background:rgba(0,0,0,150);")
                    else:
                        pc = t["colors"]["primary"]
                        preview.setStyleSheet(
                            f"background:{pc};border:2px solid {t['colors']['border']};border-radius:6px;"
                        )
                    hl.addWidget(preview)

                    # ── Название ──
                    vl = QVBoxLayout(); vl.setSpacing(1)
                    hidden = not available
                    name_text = "🔒 ???" if hidden else t["name"]
                    nm = QLabel(name_text)
                    nm.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                    if is_current:
                        nm.setStyleSheet("color:#ffcc00;")
                    elif available:
                        nm.setStyleSheet("color:#cc8844;")
                    else:
                        nm.setStyleSheet("color:#555;")
                    vl.addWidget(nm)

                    hl.addLayout(vl, 1)

                    # ── Кнопка описания (i) ──
                    if available and not hidden:
                        full_desc = t.get("desc_full", t["desc"])
                        short_desc_hover = f"<b>{t['name']}</b><br>{t['desc']}"
                        desc_text_full = f"<b>{t['name']}</b><br><br>{full_desc}"
                        info_btn = QPushButton("ℹ")
                        info_btn.setFixedSize(24, 24)
                        info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                        info_btn.setStyleSheet(
                            "QPushButton{border:1px solid #444;color:#888;font-size:12px;border-radius:12px;padding:0;background:transparent;}"
                            "QPushButton:hover{border-color:#cc8844;color:#cc8844;}"
                        )
                        # Клик — полное описание
                        info_btn.clicked.connect(lambda checked, txt=desc_text_full, btn=info_btn: self._show_theme_tooltip(txt, btn, True))
                        # Hover — короткое описание
                        info_btn.enterEvent = lambda ev, txt=short_desc_hover, btn=info_btn: self._show_theme_tooltip(txt, btn, False)
                        info_btn.leaveEvent = lambda ev: self._close_theme_popup(getattr(self, '_theme_info_popup', None)) if not getattr(self, '_theme_popup_locked', False) else None
                        hl.addWidget(info_btn)

                    # ── Кнопка выбора / индикатор текущей ──
                    if available and not is_current:
                        btn = QPushButton("✔")
                        btn.setFixedSize(30, 30)
                        btn.setCursor(Qt.CursorShape.PointingHandCursor)
                        btn.setStyleSheet(
                            "QPushButton{border:1px solid #555;color:#aaa;font-size:14px;border-radius:6px;padding:0;}"
                            "QPushButton:hover{border-color:#ff4040;color:#ff4040;background:rgba(255,60,60,30);}"
                        )
                        theme_id = t["id"]
                        btn.clicked.connect(lambda checked, tid=theme_id: self._select_theme(tid))
                        hl.addWidget(btn)
                    elif is_current:
                        cur_lbl = QLabel("⭐")
                        cur_lbl.setFixedWidth(30)
                        cur_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        hl.addWidget(cur_lbl)

                    # ── Стиль рамки ──
                    if tier == "gold":
                        if is_current:
                            f.setStyleSheet(
                                "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                                "stop:0 rgba(50,40,0,220),stop:0.5 rgba(70,55,0,220),stop:1 rgba(50,40,0,220));"
                                "border:2px solid #ddaa00;border-radius:6px;}"
                            )
                            nm.setStyleSheet("color:#ffdd00;")
                        elif available:
                            f.setStyleSheet(
                                "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                                "stop:0 rgba(35,28,0,200),stop:0.5 rgba(50,40,0,200),stop:1 rgba(35,28,0,200));"
                                "border:2px solid #aa8800;border-radius:6px;}"
                            )
                            nm.setStyleSheet("color:#ddaa00;")
                        else:
                            f.setStyleSheet("QFrame{background:rgba(20,15,0,180);border:2px solid #775500;border-radius:6px;}")
                    elif tier == "purple":
                        if is_current:
                            f.setStyleSheet(
                                "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                                "stop:0 rgba(40,0,50,220),stop:0.5 rgba(60,0,80,220),stop:1 rgba(40,0,50,220));"
                                "border:2px solid #aa44ff;border-radius:6px;}"
                            )
                            nm.setStyleSheet("color:#cc66ff;")
                        elif available:
                            f.setStyleSheet(
                                "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                                "stop:0 rgba(30,0,40,200),stop:0.5 rgba(45,0,60,200),stop:1 rgba(30,0,40,200));"
                                "border:2px solid #8833cc;border-radius:6px;}"
                            )
                            nm.setStyleSheet("color:#aa55dd;")
                        else:
                            f.setStyleSheet("QFrame{background:rgba(15,0,20,180);border:2px solid #552288;border-radius:6px;}")
                    elif tier == "legendary":
                        if is_current:
                            f.setStyleSheet(
                                "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                                "stop:0 rgba(50,30,0,220),stop:0.5 rgba(80,40,0,220),stop:1 rgba(50,30,0,220));"
                                "border:2px solid #ffcc00;border-radius:6px;}"
                            )
                        elif available:
                            f.setStyleSheet(
                                "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                                "stop:0 rgba(40,25,0,200),stop:0.5 rgba(60,30,0,200),stop:1 rgba(40,25,0,200));"
                                "border:2px solid #bb9900;border-radius:6px;}"
                            )
                        else:
                            f.setStyleSheet("QFrame{background:rgba(20,10,0,180);border:2px solid #886600;border-radius:6px;}")
                    elif tier == "secret":
                        if is_current:
                            f.setStyleSheet(
                                "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                                "stop:0 rgba(30,0,30,220),stop:0.5 rgba(60,0,60,220),stop:1 rgba(30,0,30,220));"
                                "border:2px solid #cc00cc;border-radius:6px;}"
                            )
                        elif available:
                            f.setStyleSheet(
                                "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                                "stop:0 rgba(25,0,25,200),stop:0.5 rgba(50,0,50,200),stop:1 rgba(25,0,25,200));"
                                "border:2px solid #aa00aa;border-radius:6px;}"
                            )
                        else:
                            f.setStyleSheet("QFrame{background:rgba(10,0,10,180);border:2px dashed #440044;border-radius:6px;}")
                    elif is_current:
                        f.setStyleSheet("QFrame{background:rgba(30,10,5,200);border:2px solid #ff8800;border-radius:6px;}")
                    elif available:
                        f.setStyleSheet("QFrame{background:rgba(15,5,5,150);border:1px solid #442222;border-radius:6px;}")
                    else:
                        f.setStyleSheet("QFrame{background:rgba(5,2,2,100);border:1px solid #222;border-radius:6px;}")

                    cat_lay.addWidget(f)
                    self._theme_item_widgets.append((f, t["id"], t["name"].lower()))

            self.themes_layout.addWidget(cat_container)

        self.themes_layout.addStretch()

        # Применяем текущий фильтр поиска
        if hasattr(self, '_theme_search') and self._theme_search.text().strip():
            self._filter_themes(self._theme_search.text())

        # Восстанавливаем scroll-позицию
        if scroll_pos and hasattr(self, '_themes_scroll'):
            QTimer.singleShot(0, lambda: self._themes_scroll.verticalScrollBar().setValue(scroll_pos))

    def _toggle_theme_category(self, cat_id):
        """Свернуть/развернуть категорию тем."""
        is_collapsed = self._theme_cat_collapsed.get(cat_id, False)
        self._theme_cat_collapsed[cat_id] = not is_collapsed
        if cat_id in self._theme_cat_widgets:
            btn, container = self._theme_cat_widgets[cat_id]
            container.setVisible(is_collapsed)  # toggle
            # Обновляем стрелку
            txt = btn.text()
            if is_collapsed:
                btn.setText(txt.replace("▶", "▼"))
            else:
                btn.setText(txt.replace("▼", "▶"))

    def _filter_themes(self, text):
        """Фильтр тем по строке поиска."""
        # Emoji boom при вводе текста
        if text.strip():
            pos = self._theme_search.mapToGlobal(QPoint(self._theme_search.width() // 2, self._theme_search.height() // 2))
            self._emoji_boom_at(pos.x(), pos.y(), 6)
        query = text.strip().lower()
        for f, tid, name_lower in self._theme_item_widgets:
            if not query:
                f.setVisible(True)
            else:
                f.setVisible(query in name_lower)
        # При поиске раскрываем все категории с совпадениями
        if query:
            for cat_id, (btn, container) in self._theme_cat_widgets.items():
                container.setVisible(True)
                btn.setText(btn.text().replace("▶", "▼"))

    def _show_theme_tooltip(self, text, widget, expanded=True):
        """Показать всплывающее описание темы — кастомный виджет вместо QToolTip."""
        # Убрать предыдущий
        old = getattr(self, '_theme_info_popup', None)
        if old:
            old.close()
            old.deleteLater()
            self._theme_info_popup = None
        from PyQt6.QtWidgets import QFrame
        popup = QFrame(self, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        popup.setStyleSheet(
            "QFrame{background:#1a1a1a;border:1px solid #555;border-radius:6px;padding:8px;}"
            "QLabel{color:#cccccc;font-size:11px;}"
        )
        lay = QVBoxLayout(popup)
        lay.setContentsMargins(10, 8, 10, 8)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setMaximumWidth(340 if expanded else 260)
        lbl.setStyleSheet(f"color:#cccccc;font-size:{'11' if expanded else '10'}px;")
        lay.addWidget(lbl)
        popup.adjustSize()
        # Позиция: стараемся показать ниже виджета, если не помещается — выше
        gpos = widget.mapToGlobal(QPoint(0, 0))
        scr = QApplication.primaryScreen()
        sg = scr.availableGeometry() if scr else None
        # Предпочитаем слева от кнопки (описание не перекрывает список)
        px = gpos.x() - popup.width() - 4
        if px < (sg.x() if sg else 0):
            px = gpos.x() + widget.width() + 4
        py = gpos.y()
        # Проверяем не выходит ли за нижний край
        if sg and py + popup.height() > sg.y() + sg.height():
            py = sg.y() + sg.height() - popup.height() - 4
        popup.move(px, py)
        popup.show()
        self._theme_info_popup = popup
        # При клике (expanded) — залочить, чтобы leaveEvent не закрыл
        self._theme_popup_locked = expanded
        # Автоскрытие
        from PyQt6.QtCore import QTimer
        dur = 10000 if expanded else 3000
        QTimer.singleShot(dur, lambda: self._close_theme_popup(popup))

    def _close_theme_popup(self, popup=None):
        cur = getattr(self, '_theme_info_popup', None)
        if popup is not None and cur is not popup:
            return
        if cur:
            cur.close()
            cur.deleteLater()
            self._theme_info_popup = None
            self._theme_popup_locked = False

    def _show_theme_unlock_notification(self, theme_name):
        """Всплывающее уведомление о разблокировке темы."""
        flash = ComboFlashLabel(f"\U0001f513 НОВАЯ ТЕМА!\n{theme_name}", self, 3500)
        flash.setStyleSheet(
            f"color:#ffcc00; font-size:28px; font-weight:bold; "
            f"background:rgba(0,0,0,160); font-family:{FONT_FAMILY_DISPLAY};"
        )
        flash.setGeometry(0, 0, self.width(), self.height())
        flash.raise_(); flash.show()
        self._confetti_boom_at_center(220)

    def _get_completed_categories(self) -> set:
        """Возвращает id категорий, где все ачивки открыты."""
        achs = self.stats.get_unlocked_achievements()
        unlocked_ids = {a["id"] for a in achs if a.get("unlocked")}
        completed = set()
        for cat_id in CATEGORY_NAMES:
            cat_achs = [a for a in ACHIEVEMENTS if a.get("category") == cat_id]
            if cat_achs and all(a["id"] in unlocked_ids for a in cat_achs):
                completed.add(cat_id)
        return completed

    def _select_theme(self, theme_id):
        if getattr(self, "_cheater_theme_locked", False):
            theme_id = CHEATER_THEME_ID
        theme = get_theme_by_id(theme_id)
        if not theme:
            return
        # Emoji при выборе темы (не в режиме принудительного клоуна)
        if not getattr(self, "_cheater_theme_locked", False):
            gp = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
            self._emoji_boom_at(gp.x(), gp.y(), 20)
        self._current_theme = theme
        if not getattr(self, "_cheater_theme_locked", False):
            self.config["theme_id"] = theme_id
            from modules.config import save_config
            save_config(self.config)
        # Сброс кешей картинок и анимационных состояний
        for attr in ('_star_pixmaps', '_bg_images_pixmaps', '_center_pixmap',
                      '_sun_particles', '_villain_lasers', '_binary_digits',
                      '_retro_smiley_timer', '_retro_smiley_on',
                      '_scan_flicker', '_bin_digit', '_bin_cooldown',
                      '_bg_file_pixmap', '_eye_pixmaps', '_eye_states',
                      '_ominous_dust', '_ominous_detection_count',
                      '_wobble_phase',
                      '_charged_phase', '_charged_flash', '_charged_det_lasers', '_charged_laser_queue',
                      '_charged_waves', '_charged_awake', '_charged_detect_flash',
                      '_charged_sparks', '_jitter_fling', '_cursor_trail',
                      '_counter_ghosts', '_counter_ghost_prev', '_prev_jitter',
                      '_charged_intensity', '_charged_was_awake', '_zigzag_phase',
                      '_grid_offset', '_charged_dust', '_charged_dust_cooldown',
                      '_spiral_phase', '_spiral_particles', '_spiral_trail',
                      '_spiral_bursts', '_spiral_click_count', '_spiral_cursor_dist',
                      '_spiral_color_shift', '_spiral_color_target', '_spiral_click_threshold',
                      '_spiral_transition_tick',
                      '_hex_layers', '_hex_dust_particles',
                      '_counter_bg_pixmap', '_bubbles'):
            if hasattr(self, attr):
                delattr(self, attr)
        self._spark_overlay.set_active(False)
        if hasattr(self, '_star_overlay'):
            self._star_overlay._active = False
            self._star_overlay.hide()
        # Ширина окна и отступы зависят от формы темы
        extra = theme.get("extra_width", 0)
        self.setFixedWidth(WIN_W + extra)
        extra_w = extra // 2
        if theme.get("lightning_margin"):
            extra_w = 0  # extra_width для молний, не для контента
        border_pad = 14 if theme.get("sharp_corners") else 0
        if theme.get("shape") == "circle":
            # Круг: отступы чтобы контент не вылезал, но компактно
            side_pad = extra // 2 + 50
            top_pad = 75
            bot_pad = 45
            self._main_layout.setContentsMargins(side_pad, top_pad, side_pad, bot_pad)
        elif theme.get("shape") == "hourglass":
            side_pad = extra // 2 + 40
            self._main_layout.setContentsMargins(side_pad, 20, side_pad, 20)
        else:
            self._main_layout.setContentsMargins(12 + extra_w + border_pad, 8 + border_pad, 12 + extra_w + border_pad, 8 + border_pad)
        # Обновляем визуал
        self._fire_border.set_theme(theme)
        self._apply_style()
        # Сбросить inline-стили кнопок (заряженная тема ставит свои)
        self.btn_zone.setStyleSheet("")
        self.btn_color.setStyleSheet("")
        # Кнопки-картинки (современная тема)
        self._apply_btn_images()
        # Обновляем цвет статистических лейблов
        if hasattr(self, '_stat_labels'):
            for lb in self._stat_labels:
                lb.setStyleSheet(f"color:{theme['colors']['primary']}; font-size:13px; font-weight:bold;")
        # Обновляем кнопку сворачивания
        if hasattr(self, 'btn_expand'):
            c = theme['colors']
            self.btn_expand.setStyleSheet(
                f"QPushButton{{border:1px solid {c['secondary']};color:{c['primary']};font-size:11px;padding:3px 5px;max-height:22px;}}"
                f"QPushButton:hover{{border-color:{c['accent']};color:{c['accent']};}}"
            )
        self._update_theme_effects()
        self.update()
        self.refresh_all()
        # Уведомляем main.py для обновления overlay
        self.theme_changed.emit(theme)

    def _update_theme_effects(self):
        """Обновляет тени, свечения и все hardcoded цвета при смене темы."""
        c = self._current_theme["colors"]
        no_glow = self._current_theme.get("no_glow", False)
        # Фон контейнера счётчика
        self._counter_container.setStyleSheet("background:transparent;")
        # Сброс отступов контейнера
        cl = self._counter_container.layout()
        if cl:
            cl.setContentsMargins(0, 0, 0, 0)
        counter_font = self._current_theme.get("counter_font", FONT_FAMILY_DISPLAY)
        # Заголовок
        if self._current_theme.get("id") == "modern_windows":
            title_color = "#00ff55"
        elif self._current_theme.get("id") == "ominous":
            title_color = "#111111"
        else:
            title_color = c['primary']
        self.title_label.setStyleSheet(
            f"color: {title_color}; font-size: 16px; "
            f"font-weight: bold; font-family: {FONT_FAMILY_DISPLAY}; letter-spacing: 1px;"
        )
        if no_glow:
            self.title_label.setGraphicsEffect(None)
        else:
            tg = QGraphicsDropShadowEffect()
            tg.setColor(QColor(c["glow"]))
            tg.setBlurRadius(18); tg.setOffset(0, 0)
            self.title_label.setGraphicsEffect(tg)
        # Надпись "СЕГОДНЯ" — цвет по теме
        is_light = sum(c["bg_top"]) > 300
        if self._current_theme.get("id") == "ominous":
            today_color = "#888888"  # зловещая: серая
        elif self._current_theme.get("spiral_theme"):
            today_color = "#ffffff"  # бездонная: белый
        elif self._current_theme.get("id") == "modern_windows":
            today_color = "#00ff55"  # современная: ярко-зелёный
        elif self._current_theme.get("sharp_corners"):
            today_color = c["primary"]  # ретро: зелёная
        elif is_light:
            today_color = "#665544"
        else:
            today_color = "#552222"
        self.today_lbl.setStyleSheet(
            f"color:{today_color}; font-size:11px; font-weight:bold; letter-spacing:3px;"
        )
        # Тень счётчика
        glow_boost = self._current_theme.get("counter_glow_boost", 0)
        custom_glow = self._current_theme.get("counter_glow_color")
        if no_glow and not glow_boost and not custom_glow:
            self.counter_label.setGraphicsEffect(None)
        else:
            cg = QGraphicsDropShadowEffect()
            if self._current_theme.get("spiral_theme"):
                cg.setColor(QColor(255, 255, 255, 200))  # белое свечение
            elif custom_glow:
                cg.setColor(QColor(custom_glow))
            else:
                cg.setColor(QColor(c["glow"]))
            blur = 45 * max(1, glow_boost) if glow_boost else 45
            cg.setBlurRadius(blur); cg.setOffset(0, 0)
            self.counter_label.setGraphicsEffect(cg)
        # Стиль счётчика (с учётом шрифта темы)
        self._set_counter_style(COUNTER_FONT_PT, counter_font)
        # Лейблы "ВСЕГО" и "ПОМИЛОВАНО" — цвета по теме
        if self._current_theme.get("id") == "ominous":
            total_color = "#111111"
            mercy_color_lbl = "#111111"
        elif self._current_theme.get("spiral_theme"):
            total_color = "#ffffff"
            mercy_color_lbl = "#ffffff"
        elif self._current_theme.get("id") == "modern_windows":
            total_color = "#00aa33"
            mercy_color_lbl = "#00aa33"
        elif self._current_theme.get("sharp_corners"):
            total_color = c["primary"]
            mercy_color_lbl = c.get("accent", "#44aa66")
        else:
            total_color = c.get("secondary", "#cc4444")
            mercy_color_lbl = c.get("accent", "#44aa66")
        self.total_big.setStyleSheet(
            f"color: {total_color}; font-size: {TOTAL_FONT_PT}px; font-weight: bold; font-family: {FONT_FAMILY};"
        )
        self.mercy_big.setStyleSheet(
            f"color: {mercy_color_lbl}; font-size: {TOTAL_FONT_PT - 6}px; font-weight: bold; font-family: {FONT_FAMILY};"
        )
        # Мотивационная фраза — цвет по теме
        if self._current_theme.get("id") == "ominous":
            quote_color = "#111111"
        elif self._current_theme.get("spiral_theme"):
            quote_color = "#ffffff"
        elif self._current_theme.get("id") == "modern_windows":
            quote_color = "#00aa33"
        else:
            quote_color = c.get("accent", "#cc8844")
        self.quote_label.setStyleSheet(
            f"color:{quote_color}; font-size:13px; font-style:italic; font-weight:bold; font-family:{FONT_FAMILY}; padding:2px 8px;"
        )
        # Ранг — цвет по теме
        if self._current_theme.get("spiral_theme"):
            rank_color = "#ffffff"
            rank_next_color = "#cccccc"
        elif self._current_theme.get("id") == "modern_windows":
            rank_color = "#00ff55"
            rank_next_color = "#00bb33"
        else:
            rank_color = c.get("accent", "#ffcc00")
            rank_next_color = c.get("secondary", "#886600")
        self.rank_label.setStyleSheet(f"color:{rank_color}; font-size:13px; font-weight:bold;")
        self.rank_next_label.setStyleSheet(f"color:{rank_next_color}; font-size:13px; font-weight:bold;")
        # Стрик — базовый стиль по теме
        streak_color = c["primary"]
        self.streak_label.setStyleSheet(
            f"color: {streak_color}; font-size: {STREAK_FONT_PT}px; font-weight: bold; "
            f"font-family: {FONT_FAMILY_DISPLAY}; padding: 2px 0;"
        )
        # Тень стрика
        if no_glow:
            self.streak_label.setGraphicsEffect(None)
        else:
            sg = QGraphicsDropShadowEffect()
            sg.setColor(QColor(c["glow"]))
            sg.setBlurRadius(20); sg.setOffset(0, 0)
            self.streak_label.setGraphicsEffect(sg)
        # Бездонная тема: белое свечение-обводка на все надписи
        if self._current_theme.get("spiral_theme"):
            for lbl in (self.title_label, self.today_lbl, self.total_big, self.mercy_big,
                        self.quote_label, self.rank_label, self.rank_next_label, self.streak_label):
                eff = QGraphicsDropShadowEffect()
                eff.setColor(QColor(255, 255, 255, 180))
                eff.setBlurRadius(12)
                eff.setOffset(0, 0)
                lbl.setGraphicsEffect(eff)
        else:
            # Убираем белое свечение только если оно было (переключение С бездонной)
            if getattr(self, '_was_spiral_theme', False):
                for lbl in (self.today_lbl, self.total_big, self.mercy_big,
                            self.quote_label, self.rank_label, self.rank_next_label):
                    lbl.setGraphicsEffect(None)
        self._was_spiral_theme = bool(self._current_theme.get("spiral_theme"))
        # Rank bar
        primary = c["primary"]
        border = c["border"]
        accent = c["accent"]
        fc = c["fire_core"]
        fm = c["fire_mid"]
        ft = c["fire_tip"]
        # shadow_lord: переливающийся красно-фиолетовый бар
        if self._current_theme["id"] == "shadow_lord":
            self.rank_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid {border}; background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #0a0004,stop:1 #050002);
                    text-align: center; color: {accent}; font-size: 12px; font-weight: bold;
                    border-radius: 6px; min-height: {RANK_BAR_H}px; max-height: {RANK_BAR_H}px;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba(200,0,0,200),
                        stop:0.3 rgba(160,0,80,220),
                        stop:0.5 rgba(120,0,160,255),
                        stop:0.7 rgba(160,0,80,220),
                        stop:1.0 rgba(200,0,0,200));
                    border-radius: 5px;
                }}
            """)
        elif self._current_theme.get("shape") == "octagon":
            # Злодейская: бар в цветах темы (багряный на тёмно-зелёном)
            bar_fill = c.get("bar_fill", (180, 28, 40))
            bar_bg_c = c.get("bar_bg", (30, 38, 30))
            self.rank_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid {border};
                    background: rgba({bar_bg_c[0]},{bar_bg_c[1]},{bar_bg_c[2]},220);
                    text-align: center; color: {accent}; font-size: 12px; font-weight: bold;
                    border-radius: 6px; min-height: {RANK_BAR_H}px; max-height: {RANK_BAR_H}px;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba({bar_fill[0]},{bar_fill[1]},{bar_fill[2]},100),
                        stop:0.5 rgba({bar_fill[0]},{bar_fill[1]},{bar_fill[2]},240),
                        stop:1.0 rgba({bar_fill[0]},{bar_fill[1]},{bar_fill[2]},140));
                    border-radius: 5px;
                }}
            """)
        elif self._current_theme.get("bar_colors"):
            bc = self._current_theme["bar_colors"]
            cs, cm, ce = bc["chunk_start"], bc["chunk_mid"], bc["chunk_end"]
            is_light = sum(c["bg_top"]) > 300
            if is_light:
                bar_bg = "#ddd"
            elif self._current_theme.get("id") == "retro":
                bar_bg = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #001a00,stop:1 #000a00)"
            else:
                bar_bg = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1a0808,stop:1 #0a0000)"
            self.rank_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid {border}; background: {bar_bg};
                    text-align: center; color: {accent}; font-size: 12px; font-weight: bold;
                    border-radius: 6px; min-height: {RANK_BAR_H}px; max-height: {RANK_BAR_H}px;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba({cs[0]},{cs[1]},{cs[2]},120),
                        stop:0.4 rgba({cm[0]},{cm[1]},{cm[2]},220),
                        stop:0.7 rgba({ce[0]},{ce[1]},{ce[2]},255),
                        stop:1.0 rgba({ce[0]},{ce[1]},{ce[2]},200));
                    border-radius: 5px;
                }}
            """)
        elif self._current_theme.get("flat_bg"):
            # Серая тема — серый бар без градиента чанка
            self.rank_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {border}; background: rgba(20,20,20,200);
                    text-align: center; color: {accent}; font-size: 12px; font-weight: bold;
                    border-radius: 6px; min-height: {RANK_BAR_H}px; max-height: {RANK_BAR_H}px;
                }}
                QProgressBar::chunk {{
                    background: rgba(100,100,100,200);
                    border-radius: 5px;
                }}
            """)
        else:
            self.rank_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid {border}; background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1a0808,stop:1 #0a0000);
                    text-align: center; color: {accent}; font-size: 12px; font-weight: bold;
                    border-radius: 6px; min-height: {RANK_BAR_H}px; max-height: {RANK_BAR_H}px;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba({fc[0]},{fc[1]},{fc[2]},80),
                        stop:0.4 rgba({fm[0]},{fm[1]},{fm[2]},200),
                        stop:0.7 rgba({ft[0]},{ft[1]},{ft[2]},255),
                        stop:1.0 rgba({ft[0]},{ft[1]},{ft[2]},180));
                    border-radius: 5px;
                }}
            """)
        # Status label
        self.status_label.setStyleSheet(f"color:{border}; font-size:10px; padding:2px 0 0 0;")

    # ── Стат-снапшот для ачивок ───────────────────────────────
    def _get_stats_snapshot(self):
        s = self.stats
        return {
            "total": s.total, "today": s.get_today_count(),
            "streak": s.streak,
            "combos_today": s._cache.get("session_combos", 0),
            "max_combo": s._cache.get("max_combo", 0),
            "month": s.get_month_count(),
            "mercy_count": s.mercy_total,
            "mercy_today": s.mercy_today,
        }

    def _refresh_log(self):
        if not hasattr(self, 'log_table'):
            return
        # Обновляем лог только если окно лога открыто
        if hasattr(self, '_log_window') and self._log_window and self._log_window.isVisible():
            logs = self.stats.get_recent_log(50)
            self.log_table.setRowCount(len(logs))
            for i, e in enumerate(logs):
                self.log_table.setItem(i, 0, QTableWidgetItem(e["time"]))
                self.log_table.setItem(i, 1, QTableWidgetItem(e["date"]))
                self.log_table.setItem(i, 2, QTableWidgetItem(e["memo"]))

    # ═══════════════════════════════════════════════════════════
    #  Emoji Explosions (Адская тема)
    # ═══════════════════════════════════════════════════════════
    def _emoji_boom_at(self, screen_x=None, screen_y=None, count=18):
        """Взрыв эмодзи если тема поддерживает emoji_explosions."""
        if not self._current_theme.get("emoji_explosions"):
            return
        boom = getattr(self, '_emoji_boom', None)
        if boom:
            boom.boom(screen_x, screen_y, count)

    def _emoji_boom_from_widget(self, widget, count=18):
        """Взрыв из центра виджета (в экранных координатах)."""
        pos = widget.mapToGlobal(QPoint(widget.width() // 2, widget.height() // 2))
        self._emoji_boom_at(pos.x(), pos.y(), count)

    def _confetti_boom_from_widget(self, widget, count=160):
        """Конфетти из центра виджета (в экранных координатах)."""
        boom = getattr(self, "_confetti_boom", None)
        if not boom:
            return
        pos = widget.mapToGlobal(QPoint(widget.width() // 2, widget.height() // 2))
        boom.burst(pos.x(), pos.y(), count)

    # ═══════════════════════════════════════════════════════════
    #  Кнопки
    # ═══════════════════════════════════════════════════════════
    def _apply_btn_images(self):
        """Применить или сбросить кнопки-картинки для текущей темы."""
        import os
        from PyQt6.QtGui import QIcon
        self._btn_image_map = {}
        btn_imgs = self._current_theme.get("btn_images")
        _btn_obj_names = {
            "start": (self.btn_toggle, "imgBtnStart"),
            "zone": (self.btn_zone, "imgBtnZone"),
            "mercy": (self.btn_mercy, "imgBtnMercy"),
            "colorpicker": (self.btn_color, "imgBtnColor"),
        }
        if btn_imgs:
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
            for key, (btn, obj_name) in _btn_obj_names.items():
                img_name = btn_imgs.get(key)
                if img_name:
                    img_path = os.path.join(base, img_name)
                    pm = QPixmap(img_path)
                    if not pm.isNull():
                        btn.setObjectName(obj_name)
                        btn.setText("")
                        # mercy (голубая) — полный размер, остальные -30%
                        if key == "mercy":
                            icon_w, icon_h = 300, 60
                        else:
                            icon_w, icon_h = 206, 42
                        btn.setIcon(QIcon(pm))
                        btn.setIconSize(QSize(icon_w, icon_h))
                        self._btn_image_map[id(btn)] = pm
            self._apply_style()
        else:
            # Восстановить текст и очистить иконки при уходе с темы кнопок-картинок
            _default_texts = {
                "start": "\u25b6  СТАРТ",
                "zone": "\U0001f3af Зона казни",
                "mercy": "\U0001f54a ПОМИЛОВАНИЕ",
                "colorpicker": "\U0001f3a8 Цветпикер",
            }
            for key, (btn, _) in _btn_obj_names.items():
                btn.setObjectName(key if key == "mercy" else "")
                btn.setIcon(QIcon())
                btn.setIconSize(QSize(0, 0))
                if not btn.text():
                    btn.setText(_default_texts.get(key, ""))

    def _has_btn_images(self):
        """Есть ли кнопки-картинки у текущей темы."""
        return bool(self._current_theme.get("btn_images"))

    def _restore_btn_image(self, btn):
        """Восстановить стиль кнопки-картинки если он сохранён."""
        style = getattr(self, '_btn_image_styles', {}).get(id(btn))
        if style:
            btn.setStyleSheet(style)

    def _toggle_detection(self):
        self._emoji_boom_from_widget(self.btn_toggle, 22)
        if self._detection_active:
            self._detection_active = False
            if not self._has_btn_images():
                self.btn_toggle.setText("\u25b6  СТАРТ")
                self.btn_toggle.setStyleSheet(
                    "QPushButton{border-color:#00cc00;color:#00cc00;font-size:14px;}"
                    "QPushButton:hover{border-color:#00ff40;color:#00ff40;background:rgba(0,40,0,200);}"
                )
            self.request_stop_detection.emit()
            self.punishments.on_detection_stop()
        else:
            self._detection_active = True
            if not self._has_btn_images():
                self.btn_toggle.setText("\u23f9  ДЕТЕКЦИЯ")
                self.btn_toggle.setStyleSheet(
                    "QPushButton{border-color:#00ff00;color:#00ff00;font-size:13px;"
                    "background:rgba(0,30,0,200);}"
                    "QPushButton:hover{background:rgba(0,50,0,220);}"
                )
            self.request_start_detection.emit()
            self.punishments.on_detection_start()

    def _on_mercy(self):
        self._emoji_boom_from_widget(self.btn_mercy, 22)
        # Проверяем наказание за чрезмерное помилование
        punishment = self.punishments.on_mercy(
            self.stats.mercy_today, self.stats.get_today_count()
        )
        if punishment:
            self._show_punishment(punishment)

        self.request_mercy.emit()
        self._mercy_timer_sec = 15
        self.btn_mercy.setEnabled(False)
        self._update_mercy_button()
        self._mercy_tick_timer = QTimer(self)
        self._mercy_tick_timer.timeout.connect(self._mercy_tick)
        self._mercy_tick_timer.start(1000)

    def _mercy_tick(self):
        self._mercy_timer_sec -= 1
        if self._mercy_timer_sec <= 0:
            self._mercy_tick_timer.stop()
            if not self._has_btn_images():
                self.btn_mercy.setText("\U0001f54a ПОМИЛОВАНИЕ")
                self.btn_mercy.setStyleSheet("")
            self.btn_mercy.setEnabled(True)
            return
        self._update_mercy_button()

    def _update_mercy_button(self):
        if self._has_btn_images():
            return
        sec = self._mercy_timer_sec
        if sec <= 5 and sec % 2 == 0:
            self.btn_mercy.setStyleSheet(
                "QPushButton{border-color:#ff0000;color:#ff4444;background:rgba(50,0,0,220);font-size:13px;}"
            )
        else:
            self.btn_mercy.setStyleSheet(
                "QPushButton{border-color:#cc6600;color:#ff8800;background:rgba(30,15,0,220);font-size:13px;}"
            )
        if not self._has_btn_images():
            self.btn_mercy.setText(f"\u23f3 ПОМИЛОВАНИЕ {sec}с")

    def set_detection_active(self, a):
        self._detection_active = a
        # Заряженная: пробуждение при первом запуске детекции
        # Заряженная: пробуждение/засыпание при вкл/выкл детекции
        if self._current_theme.get("dormant_until_detection"):
            if a and hasattr(self, '_charged_awake') and not self._charged_awake:
                self._charged_awake = True
                self._charged_flash = 255  # взрыв-вспышка при пробуждении
                self._spark_overlay.set_active(True)
                # Кнопки ярко-синие
                bright_btn = (
                    "QPushButton{border:1px solid #88bbff;color:#ccdcff;font-size:13px;"
                    "background:qlineargradient(y1:0,y2:1,stop:0 rgba(30,50,100,220),stop:1 rgba(20,35,80,200));"
                    "border-radius:5px;padding:5px 0;}"
                    "QPushButton:hover{background:rgba(40,65,130,240);color:#ffffff;}"
                )
                self.btn_toggle.setStyleSheet(bright_btn)
                self.btn_color.setStyleSheet(bright_btn)
                self.btn_zone.setStyleSheet(bright_btn)
            elif not a and hasattr(self, '_charged_awake'):
                self._charged_awake = False
                self._spark_overlay.set_active(False)
                # Сбросить в спокойный стиль
                self._set_counter_style(COUNTER_FONT_PT, self._current_theme.get("counter_font"))
                self._charged_waves = []
                self._charged_detect_flash = 0
                if hasattr(self, '_charged_det_lasers'):
                    self._charged_det_lasers = []
                if hasattr(self, '_charged_laser_queue'):
                    self._charged_laser_queue = []
                # Вернуть стиль кнопок (пересоздать)
                self._apply_style()
        if not self._has_btn_images():
            if a:
                self.btn_toggle.setText("\u23f9  ДЕТЕКЦИЯ")
                self.btn_toggle.setStyleSheet(
                    "QPushButton{border-color:#00ff00;color:#00ff00;font-size:13px;"
                    "background:rgba(0,30,0,200);}"
                    "QPushButton:hover{background:rgba(0,50,0,220);}"
                )
            else:
                self.btn_toggle.setText("\u25b6  СТАРТ")
                self.btn_toggle.setStyleSheet(
                    "QPushButton{border-color:#00cc00;color:#00cc00;font-size:14px;}"
                    "QPushButton:hover{border-color:#00ff40;color:#00ff40;background:rgba(0,40,0,200);}"
                )

    # ═══════════════════════════════════════════════════════════
    #  Наказания
    # ═══════════════════════════════════════════════════════════
    def _show_punishment(self, punishment):
        """Показывает предупреждение наказания."""
        ptype = punishment["type"]
        title = punishment["title"]
        desc = punishment["desc"]
        timeout = punishment.get("timeout_sec", 0)

        # Показываем лейбл в основном окне
        self.punishment_label.setFixedHeight(60 if timeout > 0 else 40)
        self.punishment_label.setText(f"{title}\n{desc}")
        self.punishment_label.setVisible(True)

        if timeout <= 0:
            QTimer.singleShot(5000, lambda: self.punishment_label.setFixedHeight(0))

    def check_punishment_tick(self):
        """Вызывается раз в секунду из main.py для проверки challenge."""
        result = self.punishments.check_challenge_expired()
        if result is None:
            return
        if result["type"] == "mercy_spam_countdown":
            remaining = result["remaining"]
            self.punishment_label.setText(
                f"\u26a0\ufe0f ПОСТАВЬ ДВОЙКУ ЗА {remaining}с!"
            )
            if remaining <= 5:
                self.punishment_label.setStyleSheet(
                    "color:#ff0000; font-size:14px; font-weight:bold; "
                    "background:rgba(60,0,0,220); border:3px solid #ff0000; "
                    "border-radius:6px; padding:4px;"
                )
        elif result["type"] == "mercy_spam_failed":
            # Штраф: -1 двойка сегодня
            self.punishment_label.setText(f"\U0001f4a2 ПРОВАЛ! -1 двойка!")
            self.punishment_label.setStyleSheet(
                "color:#ff0000; font-size:14px; font-weight:bold; "
                "background:rgba(60,0,0,220); border:3px solid #ff0000; "
                "border-radius:6px; padding:4px;"
            )
            # Штраф: вычитаем 1 из всех счётчиков (total + daily + SQLite)
            self.stats.deduct_one()
            QTimer.singleShot(4000, lambda: self.punishment_label.setFixedHeight(0))
            self.refresh_all()

    def on_two_detected_for_punishment(self):
        """Вызывается при двойке для проверки спасения от наказания."""
        # Зловещая: прогрессивные детекции — доп. глаза и фог
        if (self._current_theme.get("progressive_detections")
                and hasattr(self, '_eye_states')):
            if not hasattr(self, '_ominous_detection_count'):
                self._ominous_detection_count = 0
            self._ominous_detection_count += 1
            dc = self._ominous_detection_count
            if dc == 1:
                if len(self._eye_states) < 4:
                    self._eye_states.append({
                        "angle_offset": 0, "state": "closed",
                        "state_timer": 2.0, "elapsed": 0.0, "vibrate": 0,
                    })
            elif dc == 2:
                if len(self._eye_states) < 5:
                    self._eye_states.append({
                        "angle_offset": 0, "state": "closed",
                        "state_timer": 2.5, "elapsed": 0.0, "vibrate": 0,
                    })
            elif dc >= 3:
                if len(self._eye_states) < 6:
                    self._eye_states.append({
                        "angle_offset": 0, "state": "closed",
                        "state_timer": 3.0, "elapsed": 0.0, "vibrate": 0,
                    })
            # Равномерно распределяем глаза
            n = len(self._eye_states)
            for i, eye in enumerate(self._eye_states):
                eye["angle_offset"] = i * (360 / n)
        # Заряженная: вспышка + тряска + 2 молнии + искры НАРУЖУ (кулдаун 3с)
        if self._current_theme.get("detection_shake") and hasattr(self, '_charged_detect_flash'):
            now = time.time()
            last_shake = getattr(self, '_last_shake_time', 0)
            if now - last_shake > 3.0:
                self._last_shake_time = now
                self._charged_detect_flash = 120
                # Молнии и искры идут через overlay (trigger)
                # Тряска окна
                geo = self.geometry()
                ox, oy = geo.x(), geo.y()
                anim_seq = [(5, 0), (-5, 3), (3, -5), (-3, 5), (0, -3), (4, 2), (-2, -4), (0, 0)]
                for i, (dx, dy) in enumerate(anim_seq):
                    QTimer.singleShot(i * 50, lambda dx=dx, dy=dy: self.move(ox + dx, oy + dy))
        saved = self.punishments.on_two_detected()
        if saved:
            self.punishment_label.setText("\u2705 СПАСЁН! Двойка засчитана!")
            self.punishment_label.setStyleSheet(
                "color:#00ff00; font-size:14px; font-weight:bold; "
                "background:rgba(0,30,0,200); border:2px solid #00ff00; "
                "border-radius:6px; padding:4px;"
            )
            QTimer.singleShot(3000, lambda: self.punishment_label.setFixedHeight(0))

    # ═══════════════════════════════════════════════════════════
    #  Комбо-таймер
    # ═══════════════════════════════════════════════════════════
    def set_combo_active(self, count, seconds_left):
        self._combo_count = count
        self._combo_timer_sec = seconds_left
        if count >= 3 and seconds_left > 0:
            self.combo_label.setText(f"\u2622\ufe0f MASS PURGE \u00d7{count} \u2014 {seconds_left}с")
            if seconds_left <= 10 and not self._combo_blink_on:
                self.combo_label.setStyleSheet(f"color:#660000;font-size:18px;font-weight:bold;font-family:{FONT_FAMILY_DISPLAY};")
            else:
                self.combo_label.setStyleSheet(f"color:#ff2200;font-size:18px;font-weight:bold;font-family:{FONT_FAMILY_DISPLAY};")
            self._combo_blink_on = not self._combo_blink_on
        elif count >= 2 and seconds_left > 0:
            self.combo_label.setText(f"\U0001f4a5 КОМБО \u00d7{count} \u2014 {seconds_left}с")
            if seconds_left <= 10 and not self._combo_blink_on:
                self.combo_label.setStyleSheet(f"color:#662200;font-size:18px;font-weight:bold;font-family:{FONT_FAMILY_DISPLAY};")
            else:
                self.combo_label.setStyleSheet(f"color:#ff4400;font-size:18px;font-weight:bold;font-family:{FONT_FAMILY_DISPLAY};")
            self._combo_blink_on = not self._combo_blink_on
        else:
            self.combo_label.setText("")

    # ═══════════════════════════════════════════════════════════
    #  Анимации
    # ═══════════════════════════════════════════════════════════
    def trigger_counter_bounce(self):
        self._bounce_step = 0
        if not hasattr(self, '_bounce_timer') or self._bounce_timer is None:
            self._bounce_timer = QTimer(self)
            self._bounce_timer.timeout.connect(self._bounce_tick)
        self._bounce_timer.start(30)

    def _bounce_tick(self):
        self._bounce_step += 1
        if self._bounce_step <= 5:
            scale = 1.0 + self._bounce_step * 0.05
        elif self._bounce_step <= 12:
            scale = 1.25 - (self._bounce_step - 5) * 0.036
        else:
            scale = 1.0; self._bounce_timer.stop()
        digits = len(self.counter_label.text())
        base = COUNTER_FONT_PT
        if digits == 3: base = int(COUNTER_FONT_PT * 0.78)
        elif digits == 4: base = int(COUNTER_FONT_PT * 0.62)
        elif digits >= 5: base = int(COUNTER_FONT_PT * 0.50)
        self._set_counter_style(int(base * scale))

    def show_combo_flash(self, combo_type):
        texts = {
            "double": ["\u26a1 ДВОЙНОЙ УДАР! \u26a1", "\U0001f480 x2 КАЗНЬ! \U0001f480", "\U0001f4a5 ПАРА ДВОЕК! \U0001f4a5"],
            "mass": ["\u2622\ufe0f ТРОЙНАЯ ЧИСТКА! \u2622\ufe0f", "\U0001f30b МЕГА КОМБО! \U0001f30b", "\U0001f525 МАССОВАЯ КАЗНЬ! \U0001f525"],
        }
        if combo_type not in texts:
            return
        flash = ComboFlashLabel(random.choice(texts[combo_type]), self, 2800)
        flash.setGeometry(0, 60, self.width(), 100)
        flash.raise_(); flash.show()

    def show_rank_flash(self, rank_name, rank_emoji):
        flash = ComboFlashLabel(f"{rank_emoji} НОВЫЙ РАНГ!\n{rank_name}", self, 3500)
        flash.setStyleSheet(
            f"color:#ffcc00; font-size:34px; font-weight:bold; "
            f"background:rgba(0,0,0,130); font-family:{FONT_FAMILY_DISPLAY};"
        )
        flash.setGeometry(0, 0, self.width(), self.height())
        flash.raise_(); flash.show()

    def _animation_tick(self):
        streak = self.stats.streak
        if streak >= 7:
            self._streak_pulse_phase += 0.15
            if self._streak_pulse_phase > 6.2832:
                self._streak_pulse_phase -= 6.2832
            pulse = 0.7 + 0.3 * math.sin(self._streak_pulse_phase)
            alpha = int(255 * pulse)
            tc = self._current_theme["colors"]
            # Цвет стрика берём из primary темы
            from PyQt6.QtGui import QColor as QC_
            qc = QC_(tc["primary"])
            streak_r, streak_g, streak_b = qc.red(), qc.green(), qc.blue()
            if streak >= 15:
                fsize = 22
            else:
                fsize = 20
            self.streak_label.setStyleSheet(
                f"color:rgba({streak_r},{streak_g},{streak_b},{alpha}); font-size:{fsize}px; font-weight:bold; "
                f"font-family:{FONT_FAMILY_DISPLAY}; padding:2px 0; letter-spacing:1px;"
            )

        # Ретро-тема: переключение счётчика на :D / >:D каждые 3.5с
        if self._current_theme.get("counter_smiley"):
            if not hasattr(self, '_retro_smiley_timer'):
                self._retro_smiley_timer = 0.0
                self._retro_smiley_on = False
            self._retro_smiley_timer += 0.08  # ~80ms тик
            if self._retro_smiley_timer >= 3.5:
                self._retro_smiley_timer = 0.0
                self._retro_smiley_on = not self._retro_smiley_on
                if self._retro_smiley_on:
                    smiley = ">:D" if self._combo_count > 0 else ":D"
                    self.counter_label.setText(smiley)
                else:
                    today = self.stats.get_today_count()
                    self.counter_label.setText(str(today))

        # Анимированная тема: shadow_lord — фиолетовые вспышки на чёрном фоне
        if self._current_theme["id"] == "shadow_lord":
            if not hasattr(self, '_shadow_phase'):
                self._shadow_phase = 0.0
            self._shadow_phase += 0.04
            if self._shadow_phase > 6.2832:
                self._shadow_phase -= 6.2832
            # Медленное, плавное мерцание с периодическими вспышками
            base = 0.5 + 0.5 * math.sin(self._shadow_phase * 0.5)
            spike = max(0, math.sin(self._shadow_phase * 2.3)) ** 4  # редкие вспышки
            purple_a = int(8 * base + 20 * spike)
            self._shadow_purple_alpha = purple_a
            self.update()

        # Анимированная тема: hysteria — эпилептическое мерцание только при детекции
        if self._current_theme["id"] == "hysteria":
            if not hasattr(self, '_hysteria_ui_phase'):
                self._hysteria_ui_phase = 0.0
            if self._detection_active:
                self._hysteria_ui_phase += 0.25
                hyst_colors = [
                    (255, 80, 80), (80, 255, 80), (80, 80, 255),
                    (255, 255, 0), (255, 0, 255), (0, 255, 255),
                    (255, 160, 0), (160, 0, 255),
                ]
                idx = int(self._hysteria_ui_phase * 2) % len(hyst_colors)
                self._hysteria_flash_color = hyst_colors[idx]
                pulse = 0.5 + 0.5 * math.sin(self._hysteria_ui_phase * 1.7)
                self._hysteria_flash_alpha = int(12 + 18 * pulse)
                self.update()
            else:
                if hasattr(self, '_hysteria_flash_alpha') and self._hysteria_flash_alpha > 0:
                    self._hysteria_flash_alpha = max(0, self._hysteria_flash_alpha - 3)
                    self.update()

        # ── Бездонная тема: спираль, частицы, шлейф, звезда ──
        if self._current_theme.get("spiral_theme"):
            if not hasattr(self, '_spiral_phase'):
                self._spiral_phase = 0.0
                self._spiral_particles = []
                self._spiral_trail = []
                self._spiral_bursts = []
                self._spiral_click_count = 0
                self._spiral_cursor_dist = 999.0
                self._spiral_color_shift = 0.0  # 0=красная, 1=фиолетовая
                self._spiral_color_target = 0.0
            # Расстояние курсора до центра окна
            g_pos = self.cursor().pos()
            local = self.mapFromGlobal(g_pos)
            wcx, wcy = self.width() / 2, self.height() / 2
            dx = local.x() - wcx
            dy = local.y() - wcy
            self._spiral_cursor_dist = math.sqrt(dx * dx + dy * dy)
            max_d = math.sqrt(wcx * wcx + wcy * wcy)
            prox = max(0.0, 1.0 - self._spiral_cursor_dist / max_d)
            # Скорость вращения спирали: 0.02 (далеко) → 0.12 (в центре)
            # Буст скорости при переходе цвета (первые 3с ×3, потом замедление)
            color_boost = 1.0
            if hasattr(self, '_spiral_color_shift') and hasattr(self, '_spiral_color_target'):
                if abs(self._spiral_color_shift - self._spiral_color_target) > 0.01:
                    if not hasattr(self, '_spiral_transition_tick'):
                        self._spiral_transition_tick = 0
                    self._spiral_transition_tick += 1
                    t_tick = self._spiral_transition_tick
                    # Первые 3с (~37 тиков) — ×6, затем плавно к ×1
                    if t_tick < 37:
                        color_boost = 6.0
                    else:
                        fade = min(1.0, (t_tick - 37) / 30.0)
                        color_boost = 6.0 - 5.0 * fade
                else:
                    self._spiral_transition_tick = 0
            self._spiral_phase += (0.02 + 0.10 * prox) * color_boost
            # Спавн чёрных частиц с краёв (больше при близости курсора)
            n_spawn = 1 + int(3 * prox)
            for _ in range(n_spawn):
                side = random.randint(0, 3)
                if side == 0: px, py = random.uniform(5, self.width()-5), 0.0
                elif side == 1: px, py = random.uniform(5, self.width()-5), float(self.height())
                elif side == 2: px, py = 0.0, random.uniform(5, self.height()-5)
                else: px, py = float(self.width()), random.uniform(5, self.height()-5)
                self._spiral_particles.append({
                    "x": px, "y": py,
                    "alpha": random.randint(80, 180),
                    "size": random.uniform(2, 5),
                    "speed": random.uniform(1.5, 4.0),
                })
            # Обновляем частицы — летят к центру
            alive_sp = []
            for dp in self._spiral_particles:
                ddx = wcx - dp["x"]
                ddy = wcy - dp["y"]
                dist = math.sqrt(ddx * ddx + ddy * ddy)
                if dist > 10:
                    spd = dp["speed"] + 2.0 * prox
                    dp["x"] += ddx / dist * spd
                    dp["y"] += ddy / dist * spd
                    dp["alpha"] -= 1
                    if dp["alpha"] > 0:
                        alive_sp.append(dp)
            self._spiral_particles = alive_sp[-200:]  # лимит
            # Малиновый шлейф курсора (только при близости < 80px)
            in_window = 0 <= local.x() <= self.width() and 0 <= local.y() <= self.height()
            if self._spiral_cursor_dist < 80 and in_window:
                for _ in range(random.randint(1, 3)):
                    self._spiral_trail.append({
                        "x": float(local.x()) + random.uniform(-5, 5),
                        "y": float(local.y()) + random.uniform(-5, 5),
                        "alpha": random.randint(140, 220),
                        "size": random.uniform(2, 5),
                    })
            alive_tr = []
            for tp in self._spiral_trail:
                tp["alpha"] -= 12
                if tp["alpha"] > 0:
                    alive_tr.append(tp)
            self._spiral_trail = alive_tr[-80:]
            # Мини-взрывы — обновляем
            alive_b = []
            for bst in self._spiral_bursts:
                alive_p = []
                for bp in bst["particles"]:
                    bp["x"] += bp["vx"]
                    bp["y"] += bp["vy"]
                    bp["vy"] += 0.1
                    bp["alpha"] -= 8
                    if bp["alpha"] > 0:
                        alive_p.append(bp)
                bst["particles"] = alive_p
                if alive_p:
                    alive_b.append(bst)
            self._spiral_bursts = alive_b
            # Плавный переход цвета (5.5с → ~69 тиков → 1/69 ≈ 0.0145)
            shift_speed = 0.0145
            old_shift = self._spiral_color_shift
            if self._spiral_color_shift < self._spiral_color_target:
                self._spiral_color_shift = min(self._spiral_color_target, self._spiral_color_shift + shift_speed)
            elif self._spiral_color_shift > self._spiral_color_target:
                self._spiral_color_shift = max(self._spiral_color_target, self._spiral_color_shift - shift_speed)
            # Обновляем цвета кнопок/надписей при смене палитры
            if abs(self._spiral_color_shift - old_shift) > 0.001:
                cs = self._spiral_color_shift
                # Интерполяция: красный (ff4444) → сине-фиолетовый (5533dd)
                pr = int(0xff * (1-cs) + 0x55 * cs)
                pg = int(0x44 * (1-cs) + 0x33 * cs)
                pb = int(0x44 * (1-cs) + 0xdd * cs)
                sr2 = int(0xaa * (1-cs) + 0x33 * cs)
                sg2 = int(0x11 * (1-cs) + 0x15 * cs)
                sb2 = int(0x11 * (1-cs) + 0x99 * cs)
                br2 = int(0x66 * (1-cs) + 0x33 * cs)
                bg2 = int(0x11 * (1-cs) + 0x11 * cs)
                bb2 = int(0x11 * (1-cs) + 0x77 * cs)
                self._current_theme["colors"]["primary"] = f"#{pr:02x}{pg:02x}{pb:02x}"
                self._current_theme["colors"]["secondary"] = f"#{sr2:02x}{sg2:02x}{sb2:02x}"
                self._current_theme["colors"]["border"] = f"#{br2:02x}{bg2:02x}{bb2:02x}"
                self._current_theme["colors"]["accent"] = f"#{min(255,pr+30):02x}{min(255,pg+30):02x}{min(255,pb+30):02x}"
                self._current_theme["colors"]["glow"] = self._current_theme["colors"]["primary"]
                self._apply_style()
                self._update_theme_effects()
            # Тик звезды-оверлея
            if hasattr(self, '_star_overlay'):
                self._star_overlay.tick()
            self.update()

        # Фоновые пылинки и звёзды (общая фаза анимации)
        if self._current_theme.get("bg_particles") or self._current_theme.get("bg_stars") or self._current_theme.get("bg_images") or self._current_theme.get("edge_glow") or self._current_theme.get("edge_glow_pulse") or self._current_theme.get("wavy_bg") or self._current_theme.get("bg_scanlines") or self._current_theme.get("orbiting_eyes") or self._current_theme.get("edge_lightning") or self._current_theme.get("hex_grid"):
            if not hasattr(self, '_gold_dust_phase'):
                self._gold_dust_phase = 0.0
            self._gold_dust_phase += 0.04
            self.update()

        # Анимация гексагональной сетки (фрактальная тема)
        if self._current_theme.get("hex_grid") and hasattr(self, '_hex_layers'):
            # Найдём текущий zooming-слой для синхронизации вращения
            zooming_layer = None
            for layer in self._hex_layers:
                if layer["state"] == "zooming":
                    zooming_layer = layer
                    break

            new_layers = []
            for layer in self._hex_layers:
                layer["age"] = layer.get("age", 0) + 1

                if layer["state"] == "idle":
                    layer["wait"] = layer.get("wait", 0) - 1
                    if layer["wait"] <= 0:
                        layer["state"] = "zooming"
                        layer["rot_target"] = random.uniform(0.012, 0.03) * random.choice([-1, 1])
                        layer["rot_speed"] = 0.0
                        layer["spawn_delay"] = 12  # ~1с задержка до появления новой

                elif layer["state"] == "zooming":
                    accel = 0.008 * (layer["scale"] ** 1.8)
                    layer["scale"] += max(0.008, accel)
                    # Плавный набор вращения
                    target = layer.get("rot_target", 0.02)
                    layer["rot_speed"] += (target - layer["rot_speed"]) * 0.04
                    layer["rot"] += layer["rot_speed"]
                    # Спавн новой сетки с задержкой после начала вращения
                    if "spawn_delay" in layer:
                        layer["spawn_delay"] -= 1
                        if layer["spawn_delay"] <= 0:
                            new_layers.append({
                                "scale": 0.58, "rot": 0.0, "rot_speed": 0.0,
                                "state": "approaching", "wait": 0,
                                "rot_target": 0.0, "age": 0,
                            })
                            del layer["spawn_delay"]
                    if layer["scale"] > 12.0:
                        layer["scale"] = -1

                elif layer["state"] == "approaching":
                    # Если верхняя сетка уже пропала — сразу финишируем
                    if not zooming_layer:
                        layer["scale"] = 1.0
                        layer["state"] = "settling"
                    else:
                        # Приближение: перспективное ускорение
                        accel = 0.006 * (layer["scale"] ** 1.6)
                        speed = max(0.004, accel)
                        if layer["scale"] > 0.93:
                            brake = 1.0 - (layer["scale"] - 0.93) / 0.07
                            speed *= max(0.3, brake)
                        layer["scale"] += speed
                        # Синхронизация вращения с zooming-слоем
                        layer["rot_speed"] = zooming_layer["rot_speed"]
                        layer["rot"] += layer["rot_speed"]
                        if layer["scale"] >= 1.0:
                            layer["scale"] = 1.0
                            layer["state"] = "settling"

                elif layer["state"] == "settling":
                    # Очень плавно гасим вращение — только по скорости
                    layer["rot_speed"] *= 0.97
                    layer["rot"] += layer["rot_speed"]
                    if abs(layer["rot_speed"]) < 0.0005:
                        layer["rot_speed"] = 0.0
                        layer["state"] = "idle"
                        layer["wait"] = random.randint(25, 50)

            self._hex_layers.extend(new_layers)
            self._hex_layers = [l for l in self._hex_layers if l["scale"] > 0]
            # Обновляем hex_dust позиции
            if hasattr(self, '_hex_dust_particles'):
                ww, wh = self.width(), self.height()
                for d in self._hex_dust_particles:
                    d["x"] += d["vx"]
                    d["y"] += d["vy"]
                    d["rot"] += d["rot_speed"]
                    # Отскок от стен
                    if d["x"] < 10 or d["x"] > ww - 10:
                        d["vx"] *= -1
                        d["x"] = max(10, min(ww - 10, d["x"]))
                        d["target_size"] = random.uniform(0.7, 1.8) * 6
                    if d["y"] < 10 or d["y"] > wh - 10:
                        d["vy"] *= -1
                        d["y"] = max(10, min(wh - 10, d["y"]))
                        d["target_size"] = random.uniform(0.7, 1.8) * 6
                    # Плавный переход размера
                    ts = d.get("target_size", d["size"])
                    d["size"] += (ts - d["size"]) * 0.08

        # Анимированная тема: villain — багровые лазерные выстрелы
        if self._current_theme.get("shape") == "octagon":
            if not hasattr(self, '_villain_lasers'):
                self._villain_lasers = []  # list of {x, y, angle, alpha, length, age}
            # Спавн нового лазера с вероятностью ~1 раз в 1.5 сек (при 80ms тике)
            if random.random() < 0.06:
                lx = random.randint(20, self.width() - 20)
                ly = random.randint(30, self.height() - 30)
                angle = random.uniform(0, 360)
                length = random.randint(1440, 2240)  # длинные лучи ×1.6, уходящие далеко за кадр
                self._villain_lasers.append({
                    "x": lx, "y": ly, "angle": angle,
                    "alpha": 0, "length": length, "age": 0,
                    "max_age": random.randint(8, 18),  # кадров жизни
                })
            # Обновление лазеров
            alive = []
            for las in self._villain_lasers:
                las["age"] += 1
                progress = las["age"] / las["max_age"]
                if progress < 0.3:
                    las["alpha"] = int(200 * (progress / 0.3))
                elif progress < 0.6:
                    las["alpha"] = 200
                else:
                    las["alpha"] = int(200 * (1.0 - (progress - 0.6) / 0.4))
                if las["age"] < las["max_age"]:
                    alive.append(las)
            self._villain_lasers = alive
            if self._villain_lasers:
                self.update()

        # Зловещая тема: обновление глаз + покачивание счётчика
        if self._current_theme.get("orbiting_eyes") and hasattr(self, '_eye_states'):
            tick_s = 0.08  # ~80ms
            for eye in self._eye_states:
                eye["elapsed"] += tick_s
                remaining = eye["state_timer"] - eye["elapsed"]
                st = eye["state"]
                opening = eye.get("_opening", False)

                if st == "open":
                    # Открыт: стоим спокойно, без вибрации
                    eye["vibrate"] = 0
                    if eye["elapsed"] >= eye["state_timer"]:
                        # open → mid_closing (начинаем закрываться)
                        eye["state"] = "mid"
                        eye["state_timer"] = random.uniform(1.4, 2.2)
                        eye["elapsed"] = 0
                        eye["_opening"] = False  # закрываемся

                elif st == "mid" and not opening:
                    # mid при ЗАКРЫТИИ: статично, без вибрации
                    eye["vibrate"] = 0
                    if eye["elapsed"] >= eye["state_timer"]:
                        eye["state"] = "closed"
                        eye["state_timer"] = random.uniform(9, 15)
                        eye["elapsed"] = 0

                elif st == "mid" and opening:
                    # mid при ОТКРЫТИИ: вибрация нарастает
                    eye["vibrate"] = 4.0 * (eye["elapsed"] / eye["state_timer"])
                    if eye["elapsed"] >= eye["state_timer"]:
                        eye["state"] = "open"
                        eye["state_timer"] = random.uniform(12, 18)
                        eye["elapsed"] = 0
                        eye.pop("_opening", None)

                elif st == "closed":
                    # Закрыт: перед открытием начинает вибрировать в последние 2с
                    if remaining < 2.0:
                        eye["vibrate"] = 3.0 * (1.0 - remaining / 2.0)
                    else:
                        eye["vibrate"] = 0
                    if eye["elapsed"] >= eye["state_timer"]:
                        # closed → mid_opening
                        eye["state"] = "mid"
                        eye["state_timer"] = random.uniform(1.4, 2.2)
                        eye["elapsed"] = 0
                        eye["_opening"] = True  # открываемся
            self.update()

        # Зловещая: инициализация состояния (счётчик и фог)
        if self._current_theme.get("progressive_detections"):
            if not hasattr(self, '_ominous_detection_count'):
                self._ominous_detection_count = 0

        # Зловещая: покачивание счётчика (фаза для paintEvent)
        if self._current_theme.get("counter_wobble"):
            if not hasattr(self, '_wobble_phase'):
                self._wobble_phase = 0.0
            self._wobble_phase += 0.06

        # Анимированная тема: sunset — солнечные лучи-пылинки из счётчика
        if self._current_theme.get("bg_particles") == "sun_rays":
            if not hasattr(self, '_sun_particles'):
                self._sun_particles = []
            # Центр счётчика — источник лучей
            cpos = self.counter_label.mapTo(self, QPoint(0, 0))
            cx = cpos.x() + self.counter_label.width() / 2
            cy = cpos.y() + self.counter_label.height() / 2
            # Спавн: до 18 частиц, ~1 каждые 6 тиков (~0.5с)
            if len(self._sun_particles) < 18 and random.random() < 0.16:
                angle = random.uniform(0, 360)
                speed = random.uniform(2.5, 6.0)
                self._sun_particles.append({
                    "ox": cx, "oy": cy,         # начальная точка (центр числа)
                    "x": cx, "y": cy,            # текущая позиция пылинки
                    "angle": angle,
                    "speed": speed,               # начальная скорость
                    "ray_len": 0,                 # текущая длина луча
                    "ray_max": random.randint(40, 90),  # макс длина луча
                    "ray_alpha": 0,               # прозрачность луча
                    "particle_alpha": 0,          # прозрачность пылинки
                    "size": random.uniform(2.5, 4.5),
                    "color_idx": random.randint(0, 3),
                    "age": 0,
                    "phase": 0,                   # 0=луч растёт, 1=луч гаснет+пылинка летит, 2=пылинка гаснет
                })
            # Обновление частиц
            alive = []
            for sp in self._sun_particles:
                sp["age"] += 1
                angle_rad = math.radians(sp["angle"])
                if sp["phase"] == 0:
                    # Луч растёт
                    sp["ray_len"] = min(sp["ray_len"] + sp["ray_max"] / 5, sp["ray_max"])
                    sp["ray_alpha"] = min(sp["ray_alpha"] + 40, 180)
                    if sp["ray_len"] >= sp["ray_max"]:
                        sp["phase"] = 1
                        # Запускаем пылинку с конца луча
                        sp["x"] = sp["ox"] + math.cos(angle_rad) * sp["ray_len"]
                        sp["y"] = sp["oy"] + math.sin(angle_rad) * sp["ray_len"]
                        sp["particle_alpha"] = 200
                elif sp["phase"] == 1:
                    # Луч гаснет, пылинка летит и замедляется
                    sp["ray_alpha"] = max(0, sp["ray_alpha"] - 20)
                    sp["x"] += math.cos(angle_rad) * sp["speed"]
                    sp["y"] += math.sin(angle_rad) * sp["speed"]
                    sp["speed"] *= 0.96  # замедление
                    if sp["speed"] < 0.3:
                        sp["phase"] = 2
                elif sp["phase"] == 2:
                    # Пылинка затухает
                    sp["particle_alpha"] = max(0, sp["particle_alpha"] - 8)
                    sp["x"] += math.cos(angle_rad) * sp["speed"]
                    sp["y"] += math.sin(angle_rad) * sp["speed"]
                    if sp["particle_alpha"] <= 0:
                        continue  # мертва
                alive.append(sp)
            self._sun_particles = alive
            self.update()

        # ── Заряженная тема: молнии-рамки, дёрганый счётчик, грозовые вспышки ──
        if self._current_theme.get("edge_lightning"):
            if not hasattr(self, '_charged_phase'):
                self._charged_phase = 0.0
                self._charged_flash = 0
                self._charged_waves = []
                self._charged_awake = False
                self._charged_detect_flash = 0
                self._charged_sparks = []
                self._charged_intensity = 0.0  # 0.0=спит, 1.0=полная мощь
            # Плавный переход интенсивности
            target = 1.0 if (self._charged_awake or not self._current_theme.get("dormant_until_detection")) else 0.0
            speed_up = 0.04    # ~2с до полной мощи (25 тиков * 80мс)
            speed_down = 0.025  # ~3.2с до затухания (40 тиков)
            if self._charged_intensity < target:
                self._charged_intensity = min(target, self._charged_intensity + speed_up)
            elif self._charged_intensity > target:
                self._charged_intensity = max(target, self._charged_intensity - speed_down)
            intensity = self._charged_intensity
            was_awake = getattr(self, '_charged_was_awake', False)
            self._charged_phase += 0.08
            # Аккумулятор фазы зигзага — скорость зависит от intensity, но не скачет
            if not hasattr(self, '_zigzag_phase'):
                self._zigzag_phase = 0.0
            self._zigzag_phase += 0.05 + 0.15 * intensity  # 0.05 покой → 0.20 актив
            # Сдвиг сетки — плывёт в левый нижний угол при активации
            if not hasattr(self, '_grid_offset'):
                self._grid_offset = [0.0, 0.0]
            self._grid_offset[0] -= 0.4 * intensity  # влево
            self._grid_offset[1] += 0.4 * intensity  # вниз
            is_awake = intensity > 0.01
            # Сброс стиля счётчика когда полностью затух
            if was_awake and not is_awake:
                self._set_counter_style(COUNTER_FONT_PT, self._current_theme.get("counter_font"))
                self._counter_ghosts = []
            self._charged_was_awake = is_awake

            # Дёрганый счётчик (масштабируется с intensity)
            if self._current_theme.get("counter_jitter") and is_awake:
                jx = int(random.randint(-8, 8) * intensity)
                jy = int(random.randint(-6, 6) * intensity)
                if not hasattr(self, '_jitter_fling'):
                    self._jitter_fling = 0
                if self._jitter_fling > 0:
                    self._jitter_fling -= 1
                    jx = int((random.choice([-40, -30, 30, 40]) + random.randint(-5, 5)) * intensity)
                    jy = int(random.randint(-15, 15) * intensity)
                elif random.random() < 0.013:
                    self._jitter_fling = 6
                if random.random() < 0.3:
                    c_hex = "#ffff88" if random.random() < 0.5 else "#ffffff"
                else:
                    c_hex = "#ffffcc"
                scale = self._current_theme.get("counter_font_scale", 1.0)
                fpt = int(COUNTER_FONT_PT * scale)
                cfont = self._current_theme.get("counter_font", "Consolas")
                self.counter_label.setStyleSheet(
                    f"color:{c_hex}; background:transparent; "
                    f"font-size:{fpt}px; font-weight:bold; font-family:{cfont}; "
                    f"margin-left:{jx}px; margin-top:{jy}px;"
                )

            # Грозовая вспышка (~раз в 20-25с)
            if is_awake and self._charged_flash <= 0 and random.random() < 0.003 * intensity:
                self._charged_flash = 200
            if self._charged_flash > 0:
                self._charged_flash = max(0, self._charged_flash - 5)  # медленно гаснет

            # Волны-дуги (голубые, гаснут быстро) — x2 частота
            if is_awake and random.random() < 0.014 * intensity:
                ww, wh = self.width(), self.height()
                edge = random.choice(["L", "R", "T", "B"])
                if edge == "L":
                    cx, cy = 0, random.randint(0, wh)
                elif edge == "R":
                    cx, cy = ww, random.randint(0, wh)
                elif edge == "T":
                    cx, cy = random.randint(0, ww), 0
                else:
                    cx, cy = random.randint(0, ww), wh
                self._charged_waves.append({
                    "cx": cx, "cy": cy, "radius": 0.0,
                    "speed": random.uniform(2.0, 4.0),
                    "alpha": random.randint(60, 120),
                    "max_radius": random.uniform(250, 500),
                    "color": random.choice([
                        (100, 160, 255), (80, 140, 255), (120, 180, 255),
                    ]),
                })
            # Белые пылинки (активный режим, пачка ~9шт, живут 2-4.6с)
            if not hasattr(self, '_charged_dust'):
                self._charged_dust = []
                self._charged_dust_cooldown = 0
            if self._charged_dust_cooldown > 0:
                self._charged_dust_cooldown -= 1
            # Спавн новой пачки только если старых нет
            if is_awake and len(self._charged_dust) == 0 and self._charged_dust_cooldown <= 0:
                ww, wh = self.width(), self.height()
                count = random.randint(7, 11)
                for _ in range(count):
                    self._charged_dust.append({
                        "x": random.uniform(10, ww - 10),
                        "y": random.uniform(10, wh - 10),
                        "vx": random.uniform(-3.5, 3.5),
                        "vy": random.uniform(-3.5, 3.5),
                        "life": random.uniform(2.0, 4.6),
                        "max_life": 0,  # заполним ниже
                        "size": random.uniform(1.5, 3.5),
                    })
                    self._charged_dust[-1]["max_life"] = self._charged_dust[-1]["life"]
                self._charged_dust_cooldown = 5  # маленький кулдаун между пачками
            # Обновление пылинок
            alive_d = []
            dt = 0.08  # ~80мс тик
            for d in self._charged_dust:
                # Пока активен — life не тикает, только при выключении затухают
                if not is_awake:
                    d["life"] -= dt
                else:
                    # Сбрасываем life на максимум чтобы при выключении был полный запас
                    d["life"] = d["max_life"]
                if d["life"] > 0:
                    # Хаотичное движение
                    d["vx"] += random.uniform(-1.0, 1.0)
                    d["vy"] += random.uniform(-1.0, 1.0)
                    d["vx"] = max(-5, min(5, d["vx"]))
                    d["vy"] = max(-5, min(5, d["vy"]))
                    d["x"] += d["vx"]
                    d["y"] += d["vy"]
                    # Отскок от краёв
                    ww, wh = self.width(), self.height()
                    if d["x"] < 5 or d["x"] > ww - 5:
                        d["vx"] *= -1
                        d["x"] = max(5, min(ww - 5, d["x"]))
                    if d["y"] < 5 or d["y"] > wh - 5:
                        d["vy"] *= -1
                        d["y"] = max(5, min(wh - 5, d["y"]))
                    alive_d.append(d)
            self._charged_dust = alive_d

            # Шлейф-призрак счётчика: предыдущий jitter как затухающий след
            if is_awake and self._current_theme.get("counter_jitter"):
                prev_jitter = getattr(self, '_prev_jitter', None)
                if prev_jitter and (prev_jitter[0] != jx or prev_jitter[1] != jy):
                    self._counter_ghosts = [{
                        "jx": prev_jitter[0], "jy": prev_jitter[1],
                        "text": self.counter_label.text(),
                        "alpha": 55,
                    }]
                elif not hasattr(self, '_counter_ghosts'):
                    self._counter_ghosts = []
                self._prev_jitter = (jx, jy)
                alive_g = []
                for g in getattr(self, '_counter_ghosts', []):
                    g["alpha"] -= 18
                    if g["alpha"] > 0:
                        alive_g.append(g)
                self._counter_ghosts = alive_g

            alive_w = []
            for wav in self._charged_waves:
                wav["radius"] += wav["speed"]
                if "alpha_base" not in wav:
                    wav["alpha_base"] = wav["alpha"]
                prog = wav["radius"] / wav["max_radius"]
                # Гаснут на 70% быстрее: (1-prog)^3.3
                wav["alpha"] = int(wav["alpha_base"] * max(0.0, 1.0 - prog) ** 3.3)
                if wav["radius"] < wav["max_radius"]:
                    alive_w.append(wav)
            self._charged_waves = alive_w

            # Детекция: красная вспышка
            if self._charged_detect_flash > 0:
                self._charged_detect_flash = max(0, self._charged_detect_flash - 4)

            # След искр курсора (на fullscreen overlay) — масштаб с intensity
            if intensity > 0.3:
                g_pos = self.cursor().pos()
                gx, gy = g_pos.x(), g_pos.y()
                local = self.mapFromGlobal(g_pos)
                in_win = 0 <= local.x() <= self.width() and 0 <= local.y() <= self.height()
                max_in = int(2 + 4 * intensity)
                max_out = int(2 * intensity)
                n_new = random.randint(1, max_in) if in_win else random.randint(0, max_out)
                if n_new > 0:
                    self._spark_overlay.spawn_at(gx, gy, n_new, in_win)
            self._spark_overlay.tick()

            self.update()

        # Валюта на главном окне больше не показывается — анимацию круассана не рисуем.

        # Проверка punishment challenge countdown
        self.check_punishment_tick()

    # ═══════════════════════════════════════════════════════════
    #  Таймеры
    # ═══════════════════════════════════════════════════════════
    def _start_timers(self):
        self._rt = QTimer(self)
        self._rt.timeout.connect(self.refresh_all)
        self._rt.start(5000)

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animation_tick)
        self._anim_timer.start(80)

        # Idle shame check — раз в минуту
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._check_idle)
        self._idle_timer.start(60000)

        self.refresh_all()

    def _check_idle(self):
        result = self.punishments.check_idle(self._detection_active)
        if result:
            self._show_punishment(result)

    def closeEvent(self, e):
        # По умолчанию "X" прячет панель (работа через tray),
        # но при полном выходе из приложения разрешаем закрыть.
        if getattr(self, "_allow_full_close", False):
            e.accept()
            return
        e.ignore()
        self.hide()
