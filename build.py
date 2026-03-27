#!/usr/bin/env python3
"""
Скрипт сборки Inferno Grade Tracker → exe / бинарник.
Запуск: python build.py
"""

import subprocess
import sys
import os

def main():
    # 1. Устанавливаем PyInstaller
    print("[1/3] Установка PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Определяем разделитель для --add-data (Windows: ;  Linux/Mac: :)
    sep = ";" if sys.platform == "win32" else ":"

    # 3. Собираем аргументы
    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", "InfernoGradeTracker",
        "--onefile",          # Один exe
        "--windowed",         # Без консоли (GUI)
        f"--add-data=assets{sep}assets",
        "--hidden-import=PyQt6.QtMultimedia",
        "--hidden-import=pytesseract",
        "--hidden-import=cv2",
        "--hidden-import=mss",
        "--hidden-import=numpy",
    ]

    # Платформо-зависимые модули pynput
    if sys.platform == "win32":
        args += [
            "--hidden-import=pynput.keyboard._win32",
            "--hidden-import=pynput.mouse._win32",
        ]
    elif sys.platform == "linux":
        args += [
            "--hidden-import=pynput.keyboard._xorg",
            "--hidden-import=pynput.mouse._xorg",
        ]
    elif sys.platform == "darwin":
        args += [
            "--hidden-import=pynput.keyboard._darwin",
            "--hidden-import=pynput.mouse._darwin",
        ]

    # Иконка (если есть)
    if os.path.exists("assets/icon.ico"):
        args.append("--icon=assets/icon.ico")

    args.append("main.py")

    # 4. Запуск сборки
    print("[2/3] Сборка...")
    print(f"  Команда: {' '.join(args)}")
    subprocess.check_call(args)

    print()
    print("=" * 50)
    print("[3/3] ГОТОВО!")
    print(f"  Файл: dist/InfernoGradeTracker{'.exe' if sys.platform == 'win32' else ''}")
    print()
    print("  ВАЖНО после сборки:")
    print("  1. Скопируй папку assets/ рядом с exe")
    print("     (или в ту же папку dist/)")
    print("  2. Tesseract OCR должен быть установлен в системе")
    print("=" * 50)


if __name__ == "__main__":
    main()
