"""
Inferno Grade Tracker — Detector Module (v2)

Логика:
1. Скриншот выбранной зоны через mss.
2. Считаем пиксели, попадающие в HSV-диапазон целевого цвета.
3. Если доля > порога → двойка обнаружена.
4. Антиспам: сигнал только при переходе «нет → есть» + кулдаун.
"""

import time
import numpy as np
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class GradeDetector(QObject):
    two_detected = pyqtSignal()
    # Отладка: (total_pixels, matching_pixels, ratio)
    debug_info = pyqtSignal(int, int, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._zone = None
        self._target_hsv = None
        self._tolerance = 35
        self._pixel_threshold = 0.003  # 0.3% пикселей = срабатывание
        self._active = False
        self._prev_detected = False
        self._last_trigger_ts = 0
        self._cooldown_sec = 4.0
        self._mercy_until = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._interval_ms = 1000

        self._mss = None

    def _ensure_imports(self):
        if self._mss is None:
            try:
                import mss
                self._mss = mss
            except ImportError:
                print("[DETECTOR] ОШИБКА: pip install mss")

    # ═══ Настройки ═══════════════════════════════════════════════════════
    def set_zone(self, x: int, y: int, w: int, h: int):
        self._zone = {"x": x, "y": y, "w": w, "h": h}
        print(f"[DETECTOR] Зона установлена: ({x},{y}) {w}×{h}")

    def set_target_color(self, hsv: list, tolerance: int = 35):
        self._target_hsv = list(hsv)
        self._tolerance = tolerance
        print(f"[DETECTOR] Целевой цвет HSV={hsv} tol=±{tolerance}")

    def set_interval(self, ms: int):
        self._interval_ms = max(300, ms)

    def set_cooldown(self, sec: float):
        self._cooldown_sec = sec

    def set_pixel_threshold(self, ratio: float):
        self._pixel_threshold = max(0.0005, min(ratio, 0.5))

    def activate_mercy(self, sec: int = 15):
        self._mercy_until = time.time() + sec

    @property
    def zone(self):
        return self._zone

    @property
    def target_color(self):
        return self._target_hsv

    @property
    def is_running(self) -> bool:
        return self._active

    # ═══ Управление ══════════════════════════════════════════════════════
    def start(self) -> bool:
        self._ensure_imports()
        if not self._zone:
            print("[DETECTOR] Зона не задана!")
            return False
        if not self._target_hsv:
            print("[DETECTOR] Цвет не задан!")
            return False
        if not self._mss:
            print("[DETECTOR] Зависимости не установлены!")
            return False
        self._active = True
        self._prev_detected = False
        self._timer.start(self._interval_ms)
        print(f"[DETECTOR] ▶ Запущен (каждые {self._interval_ms}мс)")
        return True

    def stop(self):
        self._active = False
        self._timer.stop()

    # ═══ Тик ═════════════════════════════════════════════════════════════
    def _tick(self):
        if not self._active or not self._zone or not self._target_hsv:
            return
        if time.time() < self._mercy_until:
            return

        try:
            ratio = self._measure_color_ratio()
        except Exception as e:
            print(f"[DETECTOR] Ошибка замера: {e}")
            return

        detected = ratio >= self._pixel_threshold
        now = time.time()

        # Эмит отладки
        z = self._zone
        total = z["w"] * z["h"]
        matching = int(total * ratio)
        self.debug_info.emit(total, matching, ratio)

        # Антиспам: переход False→True + кулдаун
        if detected and not self._prev_detected:
            if now - self._last_trigger_ts >= self._cooldown_sec:
                self._last_trigger_ts = now
                print(f"[DETECTOR] 🔥 ОБНАРУЖЕНО! ratio={ratio:.4f} ({ratio*100:.2f}%)")
                self.two_detected.emit()

        self._prev_detected = detected

    # ═══ BGR→HSV на чистом numpy (без OpenCV) ════════════════════════════
    @staticmethod
    def _bgr_to_hsv(bgr: np.ndarray) -> np.ndarray:
        """Конвертация BGR→HSV (OpenCV-совместимые диапазоны: H 0-179, S/V 0-255)."""
        img = bgr.astype(np.float32) / 255.0
        b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]

        mx = np.maximum(np.maximum(r, g), b)
        mn = np.minimum(np.minimum(r, g), b)
        d = mx - mn

        # Hue
        h = np.zeros_like(mx)
        mask_r = (mx == r) & (d > 0)
        mask_g = (mx == g) & (d > 0)
        mask_b = (mx == b) & (d > 0)
        h[mask_r] = 60.0 * (((g[mask_r] - b[mask_r]) / d[mask_r]) % 6)
        h[mask_g] = 60.0 * (((b[mask_g] - r[mask_g]) / d[mask_g]) + 2)
        h[mask_b] = 60.0 * (((r[mask_b] - g[mask_b]) / d[mask_b]) + 4)

        # Saturation
        s = np.where(mx > 0, d / mx, 0)

        # Собираем HSV: H/2 (0-179), S*255, V*255
        hsv = np.stack([h / 2.0, s * 255.0, mx * 255.0], axis=-1)
        return hsv.astype(np.uint8)

    # ═══ Замер цвета ═════════════════════════════════════════════════════
    def _measure_color_ratio(self) -> float:
        z = self._zone
        monitor = {
            "left": z["x"], "top": z["y"],
            "width": z["w"], "height": z["h"],
        }

        with self._mss.mss() as sct:
            img = np.array(sct.grab(monitor))

        bgr = img[:, :, :3]
        hsv = self._bgr_to_hsv(bgr)

        h, s, v = self._target_hsv
        t = self._tolerance

        h_lo = max(0, h - max(t // 4, 5))
        h_hi = min(179, h + max(t // 4, 5))
        s_lo = max(0, s - t)
        s_hi = min(255, s + t)
        v_lo = max(0, v - t)
        v_hi = min(255, v + t)

        hc, sc, vc = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        mask = (hc >= h_lo) & (hc <= h_hi) & (sc >= s_lo) & (sc <= s_hi) & (vc >= v_lo) & (vc <= v_hi)
        matching = np.count_nonzero(mask)
        total = mask.size
        return matching / total if total > 0 else 0.0

    # ═══ Скриншот ════════════════════════════════════════════════════════
    def capture_screenshot(self, save_path: str) -> bool:
        self._ensure_imports()
        if not self._mss or not self._zone:
            return False
        z = self._zone
        monitor = {
            "left": z["x"], "top": z["y"],
            "width": z["w"], "height": z["h"],
        }
        try:
            with self._mss.mss() as sct:
                shot = sct.grab(monitor)
                from mss.tools import to_png
                to_png(shot.rgb, shot.size, output=save_path)
            return True
        except Exception as e:
            print(f"[DETECTOR] Скриншот ошибка: {e}")
            return False
