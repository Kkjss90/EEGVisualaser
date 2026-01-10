#!/usr/bin/env python3
"""
Скрипт сборки standalone приложения ЭЭГ анализа
Поддерживает сборку на macOS, Windows и Linux

ПОСЛЕДОВАТЕЛЬНОСТЬ ДЕЙСТВИЙ:

ОБЩИЕ ШАГИ (для всех платформ):
1. Установите Python 3.8+ с официального сайта python.org
2. Установите зависимости: pip install -r requirements.txt
3. Запустите сборку: python build_app.py


ПЛАТФОРМОСПЕЦИФИЧНЫЕ ДОПОЛНЕНИЯ:

MACOS:
- Убедитесь, что установлен Xcode Command Line Tools:
  xcode-select --install
- Для запуска: ./launch_final_app.sh или двойной клик по EEG_Analysis.app

WINDOWS:
- Установите Microsoft Visual C++ Redistributable (если требуется)
- Для запуска используйте команду: start dist\\EEG_Analysis.exe
- Или двойной клик по EEG_Analysis.exe в папке dist
- Или из командной строки: dist\\EEG_Analysis.exe

LINUX:
- Установите системные зависимости:
  sudo apt-get update
  sudo apt-get install python3-dev python3-pip libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0
- Для запуска: chmod +x dist/EEG_Analysis && ./dist/EEG_Analysis

ВОЗМОЖНЫЕ ПРОБЛЕМЫ:
- Если сборка падает на импорте модулей - проверьте requirements.txt
- На macOS может потребоваться снятие карантина: xattr -rd com.apple.quarantine dist/EEG_Analysis.app
- На Windows может потребоваться разрешение запуска от неизвестного издателя
- На Linux проверьте наличие всех системных библиотек Qt5/PyQt5
"""

import os
import sys
import subprocess
import shutil
import platform

def get_platform_info():
    """Получить информацию о платформе"""
    system = platform.system().lower()
    if system == "darwin":
        return "macos", "EEG_Analysis.app"
    elif system == "windows":
        return "windows", "EEG_Analysis.exe"
    elif system == "linux":
        return "linux", "EEG_Analysis"
    else:
        return system, "EEG_Analysis"

def get_platform_instructions(platform_name):
    """Получить инструкции для запуска в зависимости от платформы"""
    if platform_name == "macos":
        return [
            "./launch_final_app.sh",
            "# или",
            "open dist/EEG_Analysis.app"
        ]
    elif platform_name == "windows":
        return [
            "start dist\\EEG_Analysis.exe",
            "# или",
            "dist\\EEG_Analysis.exe",
            "# или двойной клик по файлу EEG_Analysis.exe в папке dist"
        ]
    elif platform_name == "linux":
        return [
            "./dist/EEG_Analysis",
            "# или",
            "chmod +x dist/EEG_Analysis && ./dist/EEG_Analysis"
        ]
    else:
        return ["./dist/EEG_Analysis"]

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

    platform_name, _ = get_platform_info()

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

    # Платформоспецифичные проверки
    if platform_name == "macos":
        print("[INFO] Проверка macOS-специфичных зависимостей...")
        try:
            import PyQt5.QtCore
            print("[OK] PyQt5 macOS интеграция")
        except ImportError:
            print("[WARNING] Проблемы с PyQt5 на macOS")
            return False

    elif platform_name == "windows":
        print("[INFO] Проверка Windows-специфичных зависимостей...")
        # На Windows matplotlib может требовать дополнительных зависимостей
        try:
            import matplotlib
            matplotlib.use('Qt5Agg')  # Проверить, что бэкенд работает
            print("[OK] matplotlib Windows интеграция")
        except Exception as e:
            print(f"[WARNING] Проблемы с matplotlib на Windows: {e}")
            return False

    elif platform_name == "linux":
        print("[INFO] Проверка Linux-специфичных зависимостей...")
        # Проверить системные зависимости для Qt
        try:
            import PyQt5.QtWidgets
            print("[OK] PyQt5 Linux интеграция")
        except ImportError:
            print("[WARNING] PyQt5 не настроен правильно на Linux")
            print("[HINT] Установите системные зависимости:")
            print("sudo apt-get install python3-pyqt5 python3-pyqt5.qtwidgets")
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
    platform_name, app_name = get_platform_info()

    print("СБОРКА ПРИЛОЖЕНИЯ ЭЭГ АНАЛИЗА")
    print("=" * 50)
    print(f"[INFO] Платформа: {platform_name.upper()}")

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
        print(f"\nГотовое приложение находится в папке dist/:")
        print(f"- {app_name}")

        print(f"\nЗапуск на {platform_name.upper()}:")
        for instruction in get_platform_instructions(platform_name):
            print(instruction)

        # Дополнительные инструкции для разных платформ
        if platform_name == "macos":
            print("\n[INFO] Для macOS:")
            print("- Если приложение не запускается, снимите карантин:")
            print("  xattr -rd com.apple.quarantine dist/EEG_Analysis.app")
        elif platform_name == "windows":
            print("\n[INFO] Для Windows:")
            print("- При первом запуске Windows может показать предупреждение безопасности")
            print("- Разрешите запуск, если появится запрос")
            print("- Если команда 'start' не работает, попробуйте двойной клик по файлу")
            print("- Или запустите напрямую: dist\\EEG_Analysis.exe")
        elif platform_name == "linux":
            print("\n[INFO] Для Linux:")
            print("- Убедитесь, что установлены системные зависимости:")
            print("  sudo apt-get install libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0")

        return 0
    else:
        print("\n[ERROR] СБОРКА НЕ УДАЛАСЬ")
        return 1

if __name__ == "__main__":
    sys.exit(main())
