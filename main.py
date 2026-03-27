#!/usr/bin/env python3
"""
INFERNO GRADE TRACKER — Academic Dictator Edition
Ctrl+Shift+F2 → панель  |  F12 → паника
"""
import os, sys, random, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

# ═══ High-DPI fix — MUST be before QApplication ═══════════════════
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
os.environ.setdefault("QT_SCALE_FACTOR", "1.0")

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont

from modules.config import (
    load_config, save_config, SCREENSHOTS_DIR, get_rank,
    REACTIONS_SINGLE, REACTIONS_COMBO, REACTIONS_MASS,
    COMBO_WINDOW_SEC,
)
from modules.stats_manager import StatsManager
from modules.detector import GradeDetector
from modules.calibrator import ZoneSelector, ColorPicker
from modules.overlay import InfernoOverlay, AchievementPopup, ZoneIndicator, EmojiExplosion, ConfettiExplosion
from modules.ui_main import DictatorControlPanel
from modules.meme_manager import MemeManager
from modules.sound_manager import SoundManager
from modules.auth import AuthScreen


class InfernoApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Inferno Grade Tracker")
        self.app.setQuitOnLastWindowClosed(False)

        self.config = load_config()
        self.stats = StatsManager()
        self.memes = MemeManager()
        self.sounds = SoundManager()

        # Детектор
        self.detector = GradeDetector()
        self.detector.two_detected.connect(self._on_two)
        self.detector.debug_info.connect(self._on_debug)
        thr = self.config.get("pixel_threshold", 0.3)
        self.detector.set_pixel_threshold(thr / 100.0)

        # Оверлеи
        self.overlay = InfernoOverlay()
        # Применяем тему из конфига к overlay
        from modules.themes import get_theme_by_id, DEFAULT_THEME_ID
        init_theme = get_theme_by_id(self.config.get("theme_id", DEFAULT_THEME_ID))
        if init_theme:
            self.overlay.set_theme(init_theme)
        self.zone_ind = ZoneIndicator()
        self._zone_visible = True
        self.emoji_boom = EmojiExplosion()
        self.confetti = ConfettiExplosion()

        # Панель
        self.panel = DictatorControlPanel(self.stats, self.config)
        self.panel._emoji_boom = self.emoji_boom
        self.panel._confetti_boom = self.confetti
        self._connect()
        self._overlay_on = True
        self._ach_popups = []
        self._authed = False

        self._apply_config()
        self._setup_hotkeys()
        self._setup_tray()
        self._setup_combo_timer()
        self._setup_f12_poll()
        rn, _ = get_rank(self.stats.total)
        self._last_rank = rn

        # ═══ Экран авторизации ════════════════════════════════
        self.auth_screen = AuthScreen()
        self.auth_screen.auth_success.connect(self._on_auth_success)

    def _on_auth_success(self, fio, nickname):
        """Авторизация прошла — показываем панель."""
        print(f"[AUTH] {fio} ({nickname})")
        self.panel.set_user(fio, nickname)
        self.panel.show()
        self.panel.refresh_all()
        self._authed = True

    def _connect(self):
        p = self.panel
        p.request_calibrate_zone.connect(self._cal_zone)
        p.request_calibrate_color.connect(self._cal_color)
        p.request_start_detection.connect(self._start)
        p.request_stop_detection.connect(self._stop)
        p.request_mercy.connect(self._mercy)
        p.request_panic_stop.connect(self._panic)
        p.request_show_zone.connect(self._toggle_zone_vis)
        p.threshold_changed.connect(self._set_threshold)
        p.theme_changed.connect(self._on_theme_changed)
        p.chk_sound.stateChanged.connect(lambda s: setattr(self.sounds, 'enabled', bool(s)))
        p.chk_overlay.stateChanged.connect(lambda s: setattr(self, '_overlay_on', bool(s)))

    def _on_theme_changed(self, theme):
        """Применяет новую тему к overlay."""
        self.overlay.set_theme(theme)

    def _apply_config(self):
        c = self.config
        if c.get("zone"):
            z = c["zone"]
            self.detector.set_zone(z["x"], z["y"], z["w"], z["h"])
            self.zone_ind.update_zone(z["x"], z["y"], z["w"], z["h"])
        if c.get("target_color_hsv"):
            self.detector.set_target_color(c["target_color_hsv"], c.get("color_tolerance", 35))
        self.detector.set_interval(c.get("detection_interval_ms", 1500))

    # ═══ Хоткеи ═════════════════════════════════════════════════════
    def _setup_hotkeys(self):
        self._kb_listener = None
        try:
            from pynput import keyboard
            self._pressed = set()

            def on_press(key):
                self._pressed.add(key)
                if key == keyboard.Key.f12:
                    QTimer.singleShot(0, self._panic)
                    return
                ctrl = keyboard.Key.ctrl_l in self._pressed or keyboard.Key.ctrl_r in self._pressed
                shift = keyboard.Key.shift_l in self._pressed or keyboard.Key.shift_r in self._pressed
                if ctrl and shift and key == keyboard.Key.f2:
                    QTimer.singleShot(0, self._toggle_panel)

            def on_release(key):
                self._pressed.discard(key)

            self._kb_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self._kb_listener.daemon = True
            self._kb_listener.start()
            print("[HOTKEYS] Ctrl+Shift+F2 / F12")
        except Exception as e:
            print(f"[HOTKEYS] pynput: {e}")

    def _setup_f12_poll(self):
        self._f12_timer = QTimer()
        self._f12_timer.timeout.connect(self._poll_f12)
        self._f12_timer.start(200)

    def _poll_f12(self):
        try:
            import keyboard
            if keyboard.is_pressed('f12'):
                self._panic()
        except ImportError:
            pass
        except Exception:
            pass

    # ═══ Комбо-таймер ════════════════════════════════════════════════
    def _setup_combo_timer(self):
        self._combo_timer = QTimer()
        self._combo_timer.timeout.connect(self._update_combo)
        self._combo_timer.start(1000)

    def _update_combo(self):
        ts_list = self.stats._cache.get("recent_timestamps", [])
        now = time.time()
        recent = [t for t in ts_list if t > now - COMBO_WINDOW_SEC]
        if len(recent) >= 2:
            oldest = min(recent)
            secs_left = max(0, int(COMBO_WINDOW_SEC - (now - oldest)))
            self.panel.set_combo_active(len(recent), secs_left)
        else:
            self.panel.set_combo_active(0, 0)

    # ═══ Трей ════════════════════════════════════════════════════════
    def _setup_tray(self):
        self.tray = QSystemTrayIcon()
        pm = QPixmap(32, 32); pm.fill(QColor(0, 0, 0, 0))
        p = QPainter(pm)
        p.setBrush(QColor(200, 20, 20)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(1, 1, 30, 30, 5, 5)
        p.setPen(QColor(255, 255, 255)); p.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "2"); p.end()
        self.tray.setIcon(QIcon(pm))
        self.tray.setToolTip("Inferno Grade Tracker")
        menu = QMenu()
        menu.addAction(QAction("Панель (Ctrl+Shift+F2)", triggered=self._toggle_panel))
        menu.addAction(QAction("Паника (F12)", triggered=self._panic))
        menu.addSeparator()
        menu.addAction(QAction("Выход", triggered=self._quit))
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self._toggle_panel() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self.tray.show()

    # ═══ Панель ══════════════════════════════════════════════════════
    def _toggle_panel(self):
        if not getattr(self, "_authed", False):
            self.auth_screen.show()
            self.auth_screen.raise_()
            return
        if self.panel.isVisible():
            self.panel.hide()
        else:
            self.panel.show(); self.panel.raise_(); self.panel.activateWindow()
            self.panel.refresh_all()

    # ═══ Зона ════════════════════════════════════════════════════════
    def _toggle_zone_vis(self):
        if self.zone_ind.isVisible():
            self.zone_ind.hide(); self._zone_visible = False
        else:
            if self.config.get("zone"):
                z = self.config["zone"]
                self.zone_ind.update_zone(z["x"], z["y"], z["w"], z["h"])
            self._zone_visible = True

    def _cal_zone(self):
        self.panel.hide(); self.zone_ind.hide()
        QTimer.singleShot(400, self._show_zone_sel)

    def _show_zone_sel(self):
        self._zs = ZoneSelector()
        self._zs.zone_selected.connect(self._zone_done)

    def _zone_done(self, x, y, w, h):
        self.detector.set_zone(x, y, w, h)
        self.config["zone"] = {"x": x, "y": y, "w": w, "h": h}; save_config(self.config)
        self.zone_ind.update_zone(x, y, w, h)
        QTimer.singleShot(400, self._toggle_panel)

    def _cal_color(self):
        self.panel.hide()
        QTimer.singleShot(400, self._show_cp)

    def _show_cp(self):
        self._cp = ColorPicker()
        self._cp.color_picked.connect(self._color_done)

    def _color_done(self, hsv):
        self.detector.set_target_color(hsv, self.config.get("color_tolerance", 35))
        self.config["target_color_hsv"] = hsv; save_config(self.config)
        QTimer.singleShot(400, self._toggle_panel)

    # ═══ Порог ═══════════════════════════════════════════════════════
    def _set_threshold(self, ratio):
        self.detector.set_pixel_threshold(ratio)
        self.config["pixel_threshold"] = ratio * 100
        save_config(self.config)

    # ═══ Детекция ════════════════════════════════════════════════════
    def _start(self):
        if not self.config.get("zone"):
            print("[!] Выбери зону!"); self.panel.set_detection_active(False); return
        if not self.config.get("target_color_hsv"):
            print("[!] Выбери цвет!"); self.panel.set_detection_active(False); return
        ok = self.detector.start()
        self.panel.set_detection_active(ok); self.zone_ind.set_active(ok)

    def _stop(self):
        self.detector.stop(); self.panel.set_detection_active(False); self.zone_ind.set_active(False)

    def _mercy(self):
        self.detector.activate_mercy(self.config.get("mercy_duration_sec", 15))
        self.stats.record_mercy()
        # Если квест выполнен (или помилования дали выполнение) — активируем баф.
        try:
            activated = self.panel.daily_quests.check_and_activate_bonus_if_completed()
            if activated:
                self.panel._confetti_boom_at_center(260)
            # UI зависит и от помилований (гейтинг/цели)
            self.panel.refresh_all()
        except Exception:
            pass

    # ═══ Паника ══════════════════════════════════════════════════════
    def _panic(self):
        print("[PANIC]")
        self.detector.stop(); self.overlay.kill(); self.sounds.stop()
        self.panel.set_detection_active(False); self.zone_ind.set_active(False)
        for pp in self._ach_popups:
            try: pp.hide(); pp.deleteLater()
            except: pass
        self._ach_popups.clear()

    # ═══ Дебаг ═══════════════════════════════════════════════════════
    def _on_debug(self, total, match, ratio):
        pct = ratio * 100; thr = self.detector._pixel_threshold * 100
        self.zone_ind.set_debug_text(f"px:{match}/{total} {pct:.2f}% (>{thr:.2f}%)")
        self.panel.status_label.setText(
            f"{'🟢' if self.detector.is_running else '🔴'} {pct:.2f}% / порог {thr:.2f}%")

    # ═══ ДВОЙКА! ═════════════════════════════════════════════════════
    def _on_two(self):
        now = datetime.now().strftime("%H:%M:%S")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        scr = str(SCREENSHOTS_DIR / f"purge_{ts}.png")
        self.detector.capture_screenshot(scr)
        event = self.stats.record_two(screenshot_path=scr, memo=f"Purge {now}")
        combo, level = event["combo_type"], event["reaction_level"]

        # ── Daily quest gold bonus (+gold_per_two) ──
        try:
            activated = self.panel.daily_quests.check_and_activate_bonus_if_completed()
            bonus = self.panel.daily_quests.gold_per_two()
            if activated:
                self.panel._confetti_boom_at_center(260)
            if bonus > 0:
                self.panel.shop.add_gold(bonus)
                self.panel._update_currency_display()
        except Exception as e:
            print(f"[DAILY_QUEST] {e}")

        if combo == "mass": msg = random.choice(REACTIONS_MASS)
        elif combo == "double": msg = random.choice(REACTIONS_COMBO)
        else: msg = random.choice(REACTIONS_SINGLE)

        print(f"\n{'='*45}")
        print(f"  [{now}] {msg}")
        print(f"  {combo} lvl={level} tot={event['total']} today={event['today']} "
              f"streak={event['streak']}d {event['rank_emoji']}{event['rank']}")

        if self._overlay_on:
            self.overlay.trigger(msg, level, self.memes.get_random(), 6000 + level * 2000)
        # Emoji explosion (Адская тема) при детекции — большой взрыв
        if self.panel._current_theme.get("emoji_explosions"):
            scr_geo = QApplication.primaryScreen().geometry() if QApplication.primaryScreen() else None
            if scr_geo:
                self.emoji_boom.boom(scr_geo.width() // 2, scr_geo.height() // 2, 35 + level * 15)
        self.sounds.play_for_level(level)

        # UI animations
        self.panel.trigger_counter_bounce()
        if combo in ("double", "mass"):
            self.panel.show_combo_flash(combo)

        # Check punishment challenge (спасение от наказания двойкой)
        self.panel.on_two_detected_for_punishment()

        # Check for rank-up
        prev_rank = getattr(self, '_last_rank', None)
        cur_rank = event['rank']
        if prev_rank is not None and cur_rank != prev_rank:
            self.panel.show_rank_flash(cur_rank, event['rank_emoji'])
        self._last_rank = cur_rank

        for ach in event.get("new_achievements", []):
            print(f"  {ach['icon']} {ach['name']}")
            pp = AchievementPopup(ach); pp.show_popup(); self._ach_popups.append(pp)
        print(f"{'='*45}\n")
        self.panel.refresh_all()

    # ═══ Запуск ══════════════════════════════════════════════════════
    def run(self):
        print("\n" + "=" * 46)
        print("  INFERNO GRADE TRACKER")
        print("  Ctrl+Shift+F2 -> panel  |  F12 -> panic")
        print("=" * 46)
        rn, re = get_rank(self.stats.total)
        print(f"  Memes: {self.memes.meme_count} | Sounds: {self.sounds.sound_count}")
        print(f"  Twos: {self.stats.total} | Streak: {self.stats.streak}d | {re}{rn}")
        print(f"  Threshold: {self.config.get('pixel_threshold',0.3):.2f}%\n")

        if self.config.get("zone"):
            z = self.config["zone"]
            self.zone_ind.update_zone(z["x"], z["y"], z["w"], z["h"])

        # ═══ Авторизация перед показом панели ═══
        self.panel.hide()
        self.auth_screen.show()
        self.auth_screen.raise_()

        return self.app.exec()

    def _quit(self):
        # Гарантируем полное завершение (а не "прячем окно").
        try:
            setattr(self.panel, "_allow_full_close", True)
            self.panel.close()
        except Exception:
            pass
        try:
            self.auth_screen.close()
        except Exception:
            pass

        self._panic(); self.stats.close()
        if self._kb_listener:
            try: self._kb_listener.stop()
            except: pass
        self._f12_timer.stop()
        self.tray.hide(); self.app.quit()


def main():
    app = InfernoApp()
    sys.exit(app.run())

if __name__ == "__main__":
    main()
