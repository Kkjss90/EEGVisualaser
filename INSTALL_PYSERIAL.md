# Установка PySerial для лайв-сбора данных ЭЭГ

## Зачем нужен PySerial?

PySerial - это библиотека Python для работы с последовательными портами (COM портами). Она необходима для:
- Подключения к Arduino
- Сбора данных в реальном времени
- Управления последовательной коммуникацией

Без PySerial функция лайв-сбора данных будет недоступна.

## Установка PySerial

### Способ 1: Установка из requirements.txt (рекомендуется)
```bash
cd /path/to/eeg_project
pip install -r requirements.txt
```

### Способ 2: Прямая установка PySerial
```bash
pip install pyserial
```

### Способ 3: Установка для текущего пользователя (если нет прав администратора)
```bash
pip install --user pyserial
```

### Способ 4: Установка в виртуальное окружение
```bash
# Создание виртуального окружения
python -m venv eeg_env

# Активация (Windows)
eeg_env\Scripts\activate

# Активация (macOS/Linux)
source eeg_env/bin/activate

# Установка
pip install pyserial
```

## Проверка установки

После установки проверьте, что PySerial работает:

```bash
python -c "import serial; print('PySerial version:', serial.__version__)"
```

Если команда выполнится без ошибок - установка успешна.

## Устранение проблем

### Ошибка "Permission denied"
Если получаете ошибку прав доступа, используйте:
```bash
pip install --user pyserial
```

### Ошибка "pip command not found"
Установите pip или используйте системный менеджер пакетов:

**Ubuntu/Debian:**
```bash
sudo apt install python3-pip
pip3 install pyserial
```

**macOS (с Homebrew):**
```bash
brew install python
pip3 install pyserial
```

**Windows:**
Скачайте и установите Python с официального сайта python.org

### Ошибка в виртуальном окружении
Если используете conda:
```bash
conda install pyserial
```

## После установки

1. Перезапустите приложение ЭЭГ анализа
2. Перейдите на вкладку "Лайв-сбор"
3. Нажмите "Сканировать" - теперь должно работать без ошибок
4. Подключите Arduino с загруженной прошивкой
5. Наслаждайтесь лайв-анализом ЭЭГ!</content>
</xai:function_call="write">
<parameter name="file_path">INSTALL_PYSERIAL.md