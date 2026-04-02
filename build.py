#!/usr/bin/env python3
"""
Inferno Grade Tracker — Nuitka Build Script

Полный пайплайн:
  1. Шифрование ассетов (encrypt_assets.py)
  2. Компиляция через Nuitka в один .exe (--onefile --standalone)

Запуск:
    python build.py                — зашифровать ассеты + собрать .exe
    python build.py --skip-encrypt — только сборка (ассеты уже зашифрованы)
    python build.py --decrypt-only — расшифровать ассеты обратно (для разработки)
"""

import argparse
import subprocess
import sys
import os


def run(cmd: list[str], label: str):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  {' '.join(cmd)}")
    print(f"{'='*60}\n")
    subprocess.check_call(cmd)


def main():
    parser = argparse.ArgumentParser(description="Build Inferno Grade Tracker .exe")
    parser.add_argument("--skip-encrypt", action="store_true", help="Skip asset encryption")
    parser.add_argument("--decrypt-only", action="store_true", help="Decrypt assets and exit")
    args = parser.parse_args()

    # ── Расшифровать ассеты (для разработки) ──
    if args.decrypt_only:
        run([sys.executable, "encrypt_assets.py", "--decrypt"], "Расшифровка ассетов...")
        return

    # ── Шаг 1: Зашифровать ассеты ──
    if not args.skip_encrypt:
        run([sys.executable, "encrypt_assets.py"], "Шаг 1/2: Шифрование ассетов...")
    else:
        print("\n[SKIP] Шифрование ассетов пропущено\n")

    # ── Шаг 2: Nuitka сборка ──
    nuitka_cmd = [
        sys.executable, "-m", "nuitka",

        # Режим сборки
        "--onefile",
        "--standalone",

        # Windows: без консольного окна
        "--windows-console-mode=disable",

        # Иконка
        *(["--windows-icon-from-ico=assets/icon.ico"] if os.path.exists("assets/icon.ico") else []),

        # Имя выходного файла
        "--output-filename=InfernoGradeTracker.exe",

        # Включаем папку assets (с .enc файлами) внутрь exe
        "--include-data-dir=assets=assets",

        # Включаем main.py для запуска из лаунчера в монолитном режиме
        "--include-data-files=main.py=main.py",

        # Плагины
        "--enable-plugin=pyqt6",

        # Пакеты Supabase (gotrue убран: в новых версиях входит в supabase / другое имя)
        "--include-package=supabase",
        "--include-package=postgrest",
        "--include-package=httpx",
        "--include-package=realtime",
        "--include-package=storage3",

        # Hidden imports (cv2 заменён на чистый numpy — экономия ~400МБ)
        "--include-module=PyQt6.QtMultimedia",
        "--include-module=mss",
        "--include-module=numpy",
        "--include-module=pynput",
        "--include-module=pynput.keyboard._win32",
        "--include-module=keyboard",

        # Оптимизация
        "--assume-yes-for-downloads",
        "--remove-output",

        # Точка входа — лаунчер (включает main.py в монолите)
        "launcher.py",
    ]

    run(nuitka_cmd, "Шаг 2/2: Сборка Nuitka (это займёт несколько минут)...")

    print()
    print("=" * 60)
    print("  ГОТОВО!")
    print("  Файл: InfernoGradeTracker.exe")
    print()
    print("  Ассеты зашифрованы и вшиты внутрь .exe.")
    print("  Для расшифровки ассетов: python build.py --decrypt-only")
    print("=" * 60)


if __name__ == "__main__":
    main()
