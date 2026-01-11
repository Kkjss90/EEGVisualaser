# Приложение для анализа данных ЭЭГ

Программное приложение для сбора и анализа данных электроэнцефалографии (ЭЭГ) с графическим интерфейсом.

## Быстрый старт

### Запуск готового приложения
В корне проекта находится готовое приложение (для MacOs) `EEG_Analysis.app`. Для запуска дважды кликните по этому файлу. Для остальных платформ потребуется сборка или запуск из исходного кода.

### Запуск из исходного кода
```bash
pip install -r requirements.txt
python3 main.py
```
Если не работает python3, то нужно использовать python
```bash
pip install -r requirements.txt
python main.py
```

## Возможности

### Загрузка данных
- Поддержка форматов: .edf, .set/.fdt (EEGLAB), .csv
- Автоматическое определение формата файла
- Загрузка нескольких файлов одновременно
- Извлечение названий каналов из имен файлов

### Предобработка
- Полосовой фильтр (1-40 Гц)
- Режекторный фильтр (удаление сетевых помех 50/60 Гц)
- Удаление артефактов по порогу амплитуды
- Детекция и удаление артефактов моргания
- Выбор канала для обработки

### Анализ
- Спектральный анализ (метод Уэлча)
- Вычисление мощности ритмов (дельта, тета, альфа, бета, гамма)
- Извлечение статистических признаков
- Энтропия Шеннона

### Визуализация
- Графики исходных сигналов
- Спектры мощности
- Графики мощности ритмов
- Топографические карты
- Матрицы корреляции

## Установка

### Требования
- Python 3.8 или выше
- pip
- Поддерживаемые ОС: macOS 10.15+, Windows 10+, Linux (Ubuntu 18.04+)

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Основные зависимости
- numpy - работа с массивами
- scipy - научные вычисления
- mne - анализ ЭЭГ
- matplotlib - визуализация
- PyQt5 - графический интерфейс
- pandas - работа с данными

## Сборка standalone приложения

Для создания исполняемого файла без установки Python:

### Общие шаги

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Соберите приложение с помощью скрипта:
```bash
python3 build_app.py
```
Если не работает python3, то нужно использовать python
```bash
python build_app.py
```

Скрипт автоматически:
- Проверит наличие всех зависимостей
- Очистит старые сборки
- Соберет приложение с правильной конфигурацией

3. Запустите готовое приложение из папки dist/

### Инструкции для разных платформ

#### macOS
- Требуется: Xcode Command Line Tools (`xcode-select --install`)
- Запуск: `./launch_final_app.sh` или двойной клик по `EEG_Analysis.app`
- При проблемах: `xattr -rd com.apple.quarantine dist/EEG_Analysis.app`

#### Windows
- Требуется: Microsoft Visual C++ Redistributable (если запрошено)
- Запуск: двойной клик по `EEG_Analysis.exe` в папке dist
- Или из командной строки: `dist\\EEG_Analysis.exe`

#### Linux
- Системные зависимости:
```bash
sudo apt-get update
sudo apt-get install python3-dev python3-pip libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0
```
- Запуск: `chmod +x dist/EEG_Analysis && ./dist/EEG_Analysis`

## Использование

### Работа с приложением

1. **Загрузка данных**: Нажмите "Загрузить файл(ы) ЭЭГ" и выберите файлы в формате .edf, .set или .csv

2. **Визуализация**: Перейдите на вкладку "Сигналы" для просмотра графиков ЭЭГ

3. **Предобработка**: Вкладка "Предобработка" содержит фильтры и инструменты удаления артефактов

4. **Анализ**: Вкладка "Анализ" позволяет выполнить спектральный анализ и извлечь признаки

5. **Результаты**: Вкладка "Результаты" показывает численные результаты анализа

## Структура проекта

```
.
├── eeg_analysis/              # Основные модули
│   ├── data_loader.py         # Загрузка данных
│   ├── preprocessing.py       # Предобработка
│   ├── analysis.py            # Анализ
│   └── visualization.py       # Визуализация
├── main.py                    # Главное приложение
├── build_app.py               # Скрипт сборки приложения
├── EEG_Analysis.app           # Готовое приложение
├── launch_final_app.sh        # Скрипт запуска
├── simple_app.spec            # Конфигурация PyInstaller
├── runtime_hook.py            # Настройки среды
├── requirements.txt           # Зависимости
├── README.md                  # Эта документация
└── данные для примера/        # Тестовые данные
```

## Программное использование

```python
from eeg_analysis.data_loader import EEGDataLoader
from eeg_analysis.preprocessing import EEGPreprocessor
from eeg_analysis.analysis import EEGAnalyzer

# Загрузка данных
loader = EEGDataLoader()
data = loader.load_data('file.csv')

# Предобработка
preprocessor = EEGPreprocessor(data['data'], data['sfreq'], data['ch_names'])
filtered_data = preprocessor.apply_bandpass_filter(1.0, 40.0)

# Анализ
analyzer = EEGAnalyzer(filtered_data, data['sfreq'], data['ch_names'])
band_powers = analyzer.compute_all_band_powers(channel_idx=0)
```

## Автор

Разработано в рамках курсовой работы по предмету "Нейротехнологии"

