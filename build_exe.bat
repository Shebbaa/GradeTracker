@echo off
REM ═══════════════════════════════════════════════════
REM  Сборка Inferno Grade Tracker в .exe
REM  Запускай из корня проекта: build_exe.bat
REM ═══════════════════════════════════════════════════

echo [1/3] Установка PyInstaller...
pip install pyinstaller

echo [2/3] Сборка exe...
pyinstaller ^
    --name "InfernoGradeTracker" ^
    --onefile ^
    --windowed ^
    --icon=assets\icon.ico ^
    --add-data "assets;assets" ^
    --hidden-import=PyQt6.QtMultimedia ^
    --hidden-import=pynput.keyboard._win32 ^
    --hidden-import=pynput.mouse._win32 ^
    --hidden-import=pytesseract ^
    --hidden-import=cv2 ^
    --hidden-import=mss ^
    --hidden-import=numpy ^
    main.py

echo [3/3] Готово!
echo Exe файл: dist\InfernoGradeTracker.exe
echo.
echo ВАЖНО: рядом с exe положи папку assets\ с мемами и звуками
pause
