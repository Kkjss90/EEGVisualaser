#!/bin/bash
# Простой скрипт запуска готового приложения ЭЭГ анализа

echo "Запуск приложения ЭЭГ анализа..."
echo "Путь: $(pwd)/dist/EEG_Analysis.app"

# Убираем карантинный атрибут macOS
xattr -rd com.apple.quarantine "$(pwd)/dist/EEG_Analysis.app" 2>/dev/null || true

# Запускаем приложение
open "$(pwd)/dist/EEG_Analysis.app"

echo "Приложение запущено!"
echo "Если окно не появилось, попробуйте двойной клик по файлу dist/EEG_Analysis.app"
