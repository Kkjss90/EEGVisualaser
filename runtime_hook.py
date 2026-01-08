# Runtime hook для настройки среды перед запуском приложения

import sys
import os
import tempfile

# Создаем временную директорию для matplotlib кэша
temp_dir = tempfile.mkdtemp()
os.environ['MPLCONFIGDIR'] = temp_dir

# Настройка matplotlib backend перед импортом matplotlib
os.environ['MPLBACKEND'] = 'Qt5Agg'

# Настройка Qt для macOS
if sys.platform == 'darwin':
    os.environ['QT_MAC_WANTS_LAYER'] = '1'
    # Отключаем некоторые сервисы macOS, которые могут вызывать проблемы
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
    os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

# Настройка для корректной работы с Qt
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'

# Отключаем некоторые предупреждения
os.environ['PYTHONWARNINGS'] = 'ignore'

# Подавление предупреждений
import warnings
warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Настройка matplotlib
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    matplotlib.rcParams['backend'] = 'Qt5Agg'
    matplotlib.rcParams['figure.dpi'] = 100
    matplotlib.rcParams['savefig.dpi'] = 100
    # Отключаем интерактивный режим
    matplotlib.interactive(False)

    # Предварительная инициализация matplotlib
    import matplotlib.pyplot as plt
    plt.ioff()  # Отключаем интерактивный режим

except ImportError:
    pass

# Инициализация Qt после настройки matplotlib
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication, Qt

    # Настройки Qt приложения
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

except ImportError:
    pass
