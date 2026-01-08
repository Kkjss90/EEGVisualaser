#!/bin/bash

# Скрипт для запуска приложения ЭЭГ с обходом ограничений macOS

echo "Запуск приложения ЭЭГ..."

# Путь к приложению
APP_PATH="dist/EEGAnalysis_minimal.app"
EXE_PATH="$APP_PATH/Contents/MacOS/EEGAnalysis_minimal"

# Проверяем существование
if [ ! -f "$EXE_PATH" ]; then
    echo "Исполняемый файл не найден: $EXE_PATH"
    exit 1
fi

# Устанавливаем права
chmod +x "$EXE_PATH"

# Снимаем флаг карантина
echo "Снимаем ограничения безопасности..."
xattr -rd com.apple.quarantine "$APP_PATH" 2>/dev/null || true

# Запускаем приложение
echo "Запуск приложения..."
exec "$EXE_PATH" "$@"
