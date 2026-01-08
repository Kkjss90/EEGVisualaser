#!/bin/bash
# Финальный скрипт запуска готового приложения ЭЭГ анализа

echo "Запуск приложения ЭЭГ анализа..."
echo "Путь: $(pwd)/dist/EEG_Analysis.app"

# Снимаем карантинный атрибут macOS (если есть)
xattr -rd com.apple.quarantine "$(pwd)/dist/EEG_Analysis.app" 2>/dev/null || true

# Запускаем приложение
echo "Запуск..."
open "$(pwd)/dist/EEG_Analysis.app"

echo "Приложение запущено!"
echo ""
echo "Инструкция:"
echo "1. Если окно не появилось - найдите dist/EEG_Analysis.app и кликните дважды"
echo "2. Для загрузки данных используйте файлы из папки 'данные для примера'"
echo "3. Приятного анализа ЭЭГ!"
