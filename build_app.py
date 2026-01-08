#!/usr/bin/env python3
"""
Скрипт сборки standalone приложения ЭЭГ анализа
"""

import os
import sys
import subprocess
import shutil

def run_command(cmd, description):
    """Выполнить команду с выводом статуса"""
    print(f"[BUILD] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"[OK] {description} - успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} - ошибка:")
        print(e.stderr)
        return False

def check_dependencies():
    """Проверить наличие зависимостей"""
    print("[INFO] Проверка зависимостей...")

    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("[WARNING] PyInstaller не найден, устанавливаю...")
        if not run_command("pip install pyinstaller", "Установка PyInstaller"):
            return False

    # Проверить основные зависимости
    required_modules = ['numpy', 'scipy', 'mne', 'matplotlib', 'PyQt5', 'pandas']
    for module in required_modules:
        try:
            __import__(module)
            print(f"[OK] {module}")
        except ImportError:
            print(f"[WARNING] {module} не найден")
            return False

    return True

def clean_old_builds():
    """Очистить старые сборки"""
    print("[INFO] Очистка старых сборок...")
    dirs_to_clean = ['dist', 'build']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"[OK] Удалена папка {dir_name}")

def build_app():
    """Собрать приложение"""
    spec_file = 'simple_app.spec'

    if not os.path.exists(spec_file):
        print(f"[ERROR] Файл {spec_file} не найден")
        return False

    cmd = f"python3 -m PyInstaller --clean --noconfirm {spec_file}"
    return run_command(cmd, "Сборка приложения")

def main():
    """Главная функция"""
    print("СБОРКА ПРИЛОЖЕНИЯ ЭЭГ АНАЛИЗА")
    print("=" * 50)

    # Проверить зависимости
    if not check_dependencies():
        print("[ERROR] Ошибка зависимостей. Установите зависимости командой:")
        print("pip install -r requirements.txt")
        return 1

    # Очистить старые сборки
    clean_old_builds()

    # Собрать приложение
    if build_app():
        print("\n" + "=" * 50)
        print("[SUCCESS] СБОРКА ЗАВЕРШЕНА УСПЕШНО!")
        print("\nГотовые приложения находятся в папке dist/:")
        print("- EEG_Analysis.app (macOS приложение)")
        print("- EEG_Analysis (исполняемый файл)")

        print("\nЗапуск:")
        print("./launch_final_app.sh")
        print("# или")
        print("open dist/EEG_Analysis.app")

        return 0
    else:
        print("\n[ERROR] СБОРКА НЕ УДАЛАСЬ")
        return 1

if __name__ == "__main__":
    sys.exit(main())
