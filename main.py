"""
Главное приложение для анализа ЭЭГ
Современный графический интерфейс на PyQt5
"""

import sys
import os
from pathlib import Path
import numpy as np
import warnings

# Подавление предупреждений macOS
warnings.filterwarnings('ignore')
os.environ['QT_MAC_WANTS_LAYER'] = '1'

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QLabel, 
                             QTextEdit, QTabWidget, QSpinBox, QDoubleSpinBox,
                             QComboBox, QGroupBox, QGridLayout, QMessageBox,
                             QProgressBar, QCheckBox, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Импорт наших модулей
from eeg_analysis.data_loader import EEGDataLoader
from eeg_analysis.preprocessing import EEGPreprocessor
from eeg_analysis.analysis import EEGAnalyzer
from eeg_analysis.visualization import EEGVisualizer


class AnalysisThread(QThread):
    """Поток для выполнения анализа в фоне"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, analyzer, analysis_type, **kwargs):
        super().__init__()
        self.analyzer = analyzer
        self.analysis_type = analysis_type
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.analysis_type == 'psd':
                result = self.analyzer.compute_psd(**self.kwargs)
            elif self.analysis_type == 'band_powers':
                result = self.analyzer.compute_all_band_powers(**self.kwargs)
            elif self.analysis_type == 'features':
                result = self.analyzer.extract_features(**self.kwargs)
            else:
                result = None
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MatplotlibWidget(QWidget):
    """Виджет для отображения графиков matplotlib"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(10, 6), facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def clear(self):
        self.figure.clear()
        self.canvas.draw()
    
    def plot_figure(self, fig):
        """Отображает фигуру matplotlib"""
        self.figure.clear()
        
        # Копируем содержимое фигуры
        for i, ax in enumerate(fig.axes):
            # Определяем тип subplot
            if len(fig.axes) == 1:
                new_ax = self.figure.add_subplot(111)
            else:
                try:
                    new_ax = self.figure.add_subplot(ax.get_subplotspec())
                except:
                    # Если не получается, создаем простой subplot
                    rows = int(np.ceil(np.sqrt(len(fig.axes))))
                    cols = int(np.ceil(len(fig.axes) / rows))
                    new_ax = self.figure.add_subplot(rows, cols, i + 1)
            
            # Копируем линии
            for line in ax.lines:
                new_ax.plot(line.get_xdata(), line.get_ydata(), 
                           color=line.get_color(), 
                           linewidth=line.get_linewidth(),
                           linestyle=line.get_linestyle(),
                           marker=line.get_marker(),
                           label=line.get_label() if line.get_label() != '_nolegend_' else None)
            
            # Копируем bar графики - извлекаем данные из patches
            bars_data = {}
            bar_labels = []
            xtick_labels = []
            for patch in ax.patches:
                if hasattr(patch, 'get_height') and hasattr(patch, 'get_x'):
                    x = patch.get_x()
                    height = patch.get_height()
                    width = patch.get_width()
                    color = patch.get_facecolor()
                    if x not in bars_data:
                        bars_data[x] = {'height': height, 'width': width, 'color': color}
            
            # Получаем метки для bar графиков из xticklabels
            if bars_data and ax.get_xticklabels():
                xtick_labels = [label.get_text() for label in ax.get_xticklabels()]
            
            if bars_data:
                x_positions = sorted(bars_data.keys())
                heights = [bars_data[x]['height'] for x in x_positions]
                widths = [bars_data[x]['width'] for x in x_positions]
                colors = [bars_data[x]['color'] for x in x_positions]
                
                # Создаем bar график с метками для легенды
                bars = new_ax.bar(x_positions, heights, width=widths[0] if widths else 0.8, 
                          color=colors, align='center', edgecolor='black', linewidth=1.2)
                
                # Устанавливаем метки на оси X
                if xtick_labels and len(xtick_labels) == len(x_positions):
                    new_ax.set_xticks(x_positions)
                    new_ax.set_xticklabels(xtick_labels, rotation=15, ha='right')
                
                # Копируем текст на bars
                for text in ax.texts:
                    pos = text.get_position()
                    new_ax.text(pos[0], pos[1], text.get_text(),
                               ha=text.get_ha(), va=text.get_va(),
                               fontsize=text.get_fontsize())
            
            # Копируем коллекции
            for collection in ax.collections:
                new_ax.add_collection(collection)
            
            new_ax.set_xlabel(ax.get_xlabel())
            new_ax.set_ylabel(ax.get_ylabel())
            new_ax.set_title(ax.get_title())
            new_ax.grid(ax.get_axisbelow(), alpha=0.3)
            
            # Копируем легенду (обрабатываем как обычные элементы, так и Patch)
            if ax.get_legend():
                legend = ax.get_legend()
                try:
                    handles = legend.legendHandles
                    labels = [t.get_text() for t in legend.get_texts()]
                except:
                    handles, labels = ax.get_legend_handles_labels()
                
                # Фильтруем пустые метки
                filtered_handles = []
                filtered_labels = []
                for h, l in zip(handles, labels):
                    if l and l != '_nolegend_' and l.strip():
                        filtered_handles.append(h)
                        filtered_labels.append(l)
                
                if filtered_handles:
                    # Получаем параметры легенды из оригинала
                    try:
                        loc = legend._loc
                    except:
                        try:
                            loc = legend.get_bbox_to_anchor()
                            if loc is None:
                                loc = 'best'
                        except:
                            loc = 'best'
                    try:
                        fontsize = legend.get_texts()[0].get_fontsize() if legend.get_texts() else 9
                    except:
                        fontsize = 9
                    try:
                        title_obj = legend.get_title()
                        title = title_obj.get_text() if title_obj else None
                    except:
                        title = None
                    
                    # Создаем легенду с теми же параметрами
                    if title:
                        new_ax.legend(filtered_handles, filtered_labels, 
                                    loc=loc, fontsize=fontsize,
                                    framealpha=0.9, shadow=True, title=title)
                    else:
                        new_ax.legend(filtered_handles, filtered_labels, 
                                    loc=loc, fontsize=fontsize,
                                    framealpha=0.9, shadow=True)
            
            # Копируем пределы осей
            try:
                new_ax.set_xlim(ax.get_xlim())
                new_ax.set_ylim(ax.get_ylim())
            except:
                pass
            
        self.figure.tight_layout()
        self.canvas.draw()


class StyledButton(QPushButton):
    """Стилизованная кнопка"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(35)
        self.setMinimumWidth(120)
        font = QFont("Arial", 10, QFont.Bold)
        self.setFont(font)
        self.setText(text)  # Убеждаемся, что текст установлен


class EEGAnalysisApp(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.data_loader = None
        self.preprocessor = None
        self.analyzer = None
        self.visualizer = None
        self.current_data = None
        self.loaded_file_paths = []  # Список загруженных файлов
        self.file_names_map = {}  # Маппинг каналов к именам файлов
        self.file_base_names_map = {}  # Маппинг каналов к базовым названиям файлов (без канала)
        self.init_ui()
        self.apply_styles()
    
    def apply_styles(self):
        """Применение стилей к интерфейсу"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QTabWidget::pane {
                border: 2px solid #dee2e6;
                background-color: white;
                border-radius: 8px;
                top: -1px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                color: #495057;
                padding: 12px 24px;
                margin-right: 3px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 11pt;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border-bottom: 3px solid #2e7d32;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #e9ecef, stop:1 #dee2e6);
            }
            QGroupBox {
                font-weight: 600;
                font-size: 11pt;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 white, stop:1 #f8f9fa);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #2e7d32;
                font-weight: 700;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 10pt;
                min-height: 35px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #45a049, stop:1 #3d8b40);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3d8b40, stop:1 #2e7d32);
                padding-top: 11px;
                padding-bottom: 9px;
            }
            QPushButton:disabled {
                background: #ced4da;
                color: #6c757d;
            }
            QLabel {
                color: #212529;
                font-size: 10pt;
            }
            QSpinBox, QDoubleSpinBox {
                border: 2px solid #ced4da;
                border-radius: 5px;
                padding: 6px 10px;
                background-color: white;
                font-size: 10pt;
                selection-background-color: #4CAF50;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #4CAF50;
            }
            QSpinBox:hover, QDoubleSpinBox:hover {
                border: 2px solid #adb5bd;
            }
            QComboBox {
                border: 2px solid #ced4da;
                border-radius: 5px;
                padding: 6px 10px;
                background-color: white;
                font-size: 10pt;
                min-width: 120px;
            }
            QComboBox:focus {
                border: 2px solid #4CAF50;
            }
            QComboBox:hover {
                border: 2px solid #adb5bd;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #495057;
                width: 0;
                height: 0;
            }
            QTextEdit {
                border: 2px solid #ced4da;
                border-radius: 6px;
                background-color: white;
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 10pt;
                padding: 10px;
                selection-background-color: #4CAF50;
            }
            QTextEdit:focus {
                border: 2px solid #4CAF50;
            }
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #e9ecef, stop:1 #dee2e6);
                color: #495057;
                border-top: 1px solid #ced4da;
                font-size: 9pt;
            }
            QFrame {
                background-color: white;
                border-radius: 8px;
            }
        """)
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle('Приложение для анализа ЭЭГ')
        self.setGeometry(100, 100, 1600, 1000)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        central_widget.setLayout(main_layout)
        
        # Панель загрузки данных
        load_group = QGroupBox("Загрузка данных")
        load_layout = QHBoxLayout()
        
        self.load_btn = StyledButton("Загрузить файл(ы) ЭЭГ")
        self.load_btn.clicked.connect(self.load_data)
        self.file_label = QLabel("Файл не загружен")
        self.file_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        
        load_layout.addWidget(self.load_btn)
        load_layout.addWidget(self.file_label)
        load_layout.addStretch()
        load_layout.setSpacing(15)
        load_layout.setContentsMargins(15, 15, 15, 15)
        
        load_group.setLayout(load_layout)
        main_layout.addWidget(load_group)
        
        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 10))
        
        # Вкладка 1: Визуализация сигналов
        self.tab_signals = QWidget()
        self.setup_signals_tab()
        self.tabs.addTab(self.tab_signals, "Сигналы")
        
        # Вкладка 2: Предобработка
        self.tab_preprocessing = QWidget()
        self.setup_preprocessing_tab()
        self.tabs.addTab(self.tab_preprocessing, "Предобработка")
        
        # Вкладка 3: Анализ
        self.tab_analysis = QWidget()
        self.setup_analysis_tab()
        self.tabs.addTab(self.tab_analysis, "Анализ")
        
        # Вкладка 4: Результаты
        self.tab_results = QWidget()
        self.setup_results_tab()
        self.tabs.addTab(self.tab_results, "Результаты")
        
        main_layout.addWidget(self.tabs)
        
        # Статусная строка
        self.statusBar().showMessage('Готово')
    
    def setup_signals_tab(self):
        """Настройка вкладки визуализации сигналов"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Панель управления
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)
        
        channel_label = QLabel("Канал:")
        channel_label.setStyleSheet("font-weight: 600;")
        control_layout.addWidget(channel_label)
        self.channel_combo = QComboBox()
        self.channel_combo.addItem("Все каналы")
        control_layout.addWidget(self.channel_combo)
        
        self.plot_signal_btn = StyledButton("Построить график")
        self.plot_signal_btn.clicked.connect(self.plot_signals)
        control_layout.addWidget(self.plot_signal_btn)
        
        control_layout.addStretch()
        control_frame.setLayout(control_layout)
        layout.addWidget(control_frame)
        
        # Виджет для графика
        self.signal_plot = MatplotlibWidget()
        layout.addWidget(self.signal_plot)
        
        self.tab_signals.setLayout(layout)
    
    def setup_preprocessing_tab(self):
        """Настройка вкладки предобработки"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Панель выбора канала
        channel_frame = QFrame()
        channel_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        channel_layout = QHBoxLayout()
        channel_layout.setSpacing(15)
        
        channel_label = QLabel("Канал для обработки:")
        channel_label.setStyleSheet("font-weight: 600;")
        channel_layout.addWidget(channel_label)
        self.preprocessing_channel_combo = QComboBox()
        self.preprocessing_channel_combo.addItem("Все каналы")
        channel_layout.addWidget(self.preprocessing_channel_combo)
        channel_layout.addStretch()
        
        channel_frame.setLayout(channel_layout)
        layout.addWidget(channel_frame)
        
        # Группа фильтрации
        filter_group = QGroupBox("Фильтрация")
        filter_layout = QGridLayout()
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(15, 20, 15, 15)
        
        # Полосовой фильтр
        bandpass_label = QLabel("Полосовой фильтр:")
        bandpass_label.setStyleSheet("font-weight: 600;")
        filter_layout.addWidget(bandpass_label, 0, 0)
        self.low_freq_spin = QDoubleSpinBox()
        self.low_freq_spin.setRange(0.1, 100.0)
        self.low_freq_spin.setValue(1.0)
        self.low_freq_spin.setSuffix(" Гц")
        filter_layout.addWidget(self.low_freq_spin, 0, 1)
        
        filter_layout.addWidget(QLabel("-"), 0, 2)
        
        self.high_freq_spin = QDoubleSpinBox()
        self.high_freq_spin.setRange(0.1, 100.0)
        self.high_freq_spin.setValue(40.0)
        self.high_freq_spin.setSuffix(" Гц")
        filter_layout.addWidget(self.high_freq_spin, 0, 3)
        
        self.apply_bandpass_btn = StyledButton("Применить")
        self.apply_bandpass_btn.clicked.connect(self.apply_bandpass_filter)
        filter_layout.addWidget(self.apply_bandpass_btn, 0, 4)
        
        # Режекторный фильтр
        notch_label = QLabel("Режекторный фильтр:")
        notch_label.setStyleSheet("font-weight: 600;")
        filter_layout.addWidget(notch_label, 1, 0)
        self.notch_freq_spin = QDoubleSpinBox()
        self.notch_freq_spin.setRange(1.0, 100.0)
        self.notch_freq_spin.setValue(50.0)
        self.notch_freq_spin.setSuffix(" Гц")
        filter_layout.addWidget(self.notch_freq_spin, 1, 1)
        
        self.apply_notch_btn = StyledButton("Применить")
        self.apply_notch_btn.clicked.connect(self.apply_notch_filter)
        filter_layout.addWidget(self.apply_notch_btn, 1, 2)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Группа удаления артефактов
        artifact_group = QGroupBox("Удаление артефактов")
        artifact_layout = QGridLayout()
        artifact_layout.setSpacing(12)
        artifact_layout.setContentsMargins(15, 20, 15, 15)
        
        threshold_label = QLabel("Порог амплитуды:")
        threshold_label.setStyleSheet("font-weight: 600;")
        artifact_layout.addWidget(threshold_label, 0, 0)
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(1.0, 1000.0)
        self.threshold_spin.setValue(100.0)
        self.threshold_spin.setSuffix(" мкВ")
        artifact_layout.addWidget(self.threshold_spin, 0, 1)
        
        self.remove_artifacts_btn = StyledButton("Удалить артефакты")
        self.remove_artifacts_btn.clicked.connect(self.remove_artifacts)
        artifact_layout.addWidget(self.remove_artifacts_btn, 0, 2)
        
        self.remove_blinks_btn = StyledButton("Удалить моргания")
        self.remove_blinks_btn.clicked.connect(self.remove_blinks)
        artifact_layout.addWidget(self.remove_blinks_btn, 0, 3)
        
        artifact_group.setLayout(artifact_layout)
        layout.addWidget(artifact_group)
        
        # График обработанных данных
        self.preprocessed_plot = MatplotlibWidget()
        layout.addWidget(self.preprocessed_plot)
        
        self.tab_preprocessing.setLayout(layout)
    
    def setup_analysis_tab(self):
        """Настройка вкладки анализа"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Панель управления
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)
        
        channel_label = QLabel("Канал:")
        channel_label.setStyleSheet("font-weight: 600;")
        control_layout.addWidget(channel_label)
        self.analysis_channel_combo = QComboBox()
        self.analysis_channel_combo.addItem("Средний по всем")
        control_layout.addWidget(self.analysis_channel_combo)
        
        self.analyze_psd_btn = StyledButton("Спектр мощности")
        self.analyze_psd_btn.clicked.connect(self.analyze_psd)
        control_layout.addWidget(self.analyze_psd_btn)
        
        self.analyze_bands_btn = StyledButton("Мощность ритмов")
        self.analyze_bands_btn.clicked.connect(self.analyze_bands)
        control_layout.addWidget(self.analyze_bands_btn)
        
        self.analyze_features_btn = StyledButton("Извлечь признаки")
        self.analyze_features_btn.clicked.connect(self.extract_features)
        control_layout.addWidget(self.analyze_features_btn)
        
        control_layout.addStretch()
        control_frame.setLayout(control_layout)
        layout.addWidget(control_frame)
        
        # Виджет для графиков анализа
        self.analysis_plot = MatplotlibWidget()
        layout.addWidget(self.analysis_plot)
        
        self.tab_analysis.setLayout(layout)
    
    def setup_results_tab(self):
        """Настройка вкладки результатов"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Текстовое поле для результатов
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.results_text)
        
        # Кнопки экспорта
        export_layout = QHBoxLayout()
        
        self.export_results_btn = StyledButton("Экспортировать результаты")
        self.export_results_btn.clicked.connect(self.export_results)
        export_layout.addWidget(self.export_results_btn)
        
        export_layout.addStretch()
        layout.addLayout(export_layout)
        
        self.tab_results.setLayout(layout)
    
    def load_data(self):
        """Загрузка данных ЭЭГ"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файл(ы) ЭЭГ (можно выбрать несколько для разных каналов)",
            "",
            "EEG Files (*.edf *.set *.csv);;EDF Files (*.edf);;EEGLAB Files (*.set);;CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_paths:
            return
        
        file_path = file_paths[0] if len(file_paths) == 1 else file_paths
        
        if file_path:
            try:
                self.statusBar().showMessage('Загрузка данных...')
                QApplication.processEvents()
                
                self.data_loader = EEGDataLoader()
                
                # Для CSV файлов можно указать дополнительные параметры
                file_ext = Path(file_paths[0]).suffix.lower() if isinstance(file_path, list) else Path(file_path).suffix.lower()
                
                if isinstance(file_path, list):
                    # Загрузка нескольких файлов
                    data_dict = self.data_loader.load_multiple_channels(file_path)
                else:
                    data_dict = self.data_loader.load_data(file_path)
                
                self.current_data = data_dict['data']
                self.sampling_rate = data_dict['sfreq']
                self.channel_names = data_dict['ch_names']
                
                # Проверка данных
                if self.current_data is None or self.current_data.size == 0:
                    raise ValueError("Загруженные данные пусты")
                
                if len(self.channel_names) == 0:
                    raise ValueError("Не найдены каналы в данных")
                
                # Сохраняем информацию о файлах и извлекаем названия
                if isinstance(file_path, list):
                    self.loaded_file_paths = file_path
                    file_names = [Path(p).name for p in file_path]
                    self.file_label.setText(f"Загружено файлов: {len(file_path)} ({', '.join(file_names[:3])}{'...' if len(file_names) > 3 else ''})")
                    
                    # Создаем маппинг каналов к именам файлов и названиям
                    self.file_names_map = {}
                    self.file_base_names_map = {}
                    
                    # Используем информацию о соответствии каналов и файлов из data_dict
                    if 'channel_file_mapping' in data_dict:
                        # Используем готовый маппинг из data_loader
                        for mapping_item in data_dict['channel_file_mapping']:
                            # Обрабатываем как старый формат (3 элемента), так и новый (4 элемента)
                            if len(mapping_item) == 4:
                                ch_name, file_path_str, file_idx, original_ch_name = mapping_item
                            else:
                                ch_name, file_path_str, file_idx = mapping_item
                                original_ch_name = ch_name
                            
                            full_file_name = Path(file_path_str).name
                            file_stem = Path(file_path_str).stem
                            
                            # Извлекаем базовое название файла (все до последнего подчеркивания)
                            if '_' in file_stem:
                                base_name = '_'.join(file_stem.split('_')[:-1])
                            else:
                                base_name = file_stem
                            
                            # Сохраняем маппинг для этого канала
                            self.file_names_map[ch_name] = full_file_name
                            self.file_base_names_map[ch_name] = base_name
                    else:
                        # Fallback: перезагружаем файлы для получения соответствия
                        channel_idx_counter = 0
                        for file_idx, single_file_path in enumerate(file_path):
                            temp_loader = EEGDataLoader()
                            if Path(single_file_path).suffix.lower() == '.csv':
                                temp_data_dict = temp_loader.load_csv(str(single_file_path))
                            else:
                                temp_data_dict = temp_loader.load_data(str(single_file_path))
                            
                            file_channels = temp_data_dict['ch_names']
                            full_file_name = Path(single_file_path).name
                            file_stem = Path(single_file_path).stem
                            
                            if '_' in file_stem:
                                base_name = '_'.join(file_stem.split('_')[:-1])
                            else:
                                base_name = file_stem
                            
                            for ch_name in file_channels:
                                if channel_idx_counter < len(self.channel_names):
                                    actual_ch_name = self.channel_names[channel_idx_counter]
                                    self.file_names_map[actual_ch_name] = full_file_name
                                    self.file_base_names_map[actual_ch_name] = base_name
                                    channel_idx_counter += 1
                    
                    # Проверяем, что все каналы сопоставлены
                    for ch_name in self.channel_names:
                        if ch_name not in self.file_names_map:
                            # Если канал не был сопоставлен, пытаемся найти его по имени в файлах
                            found = False
                            for single_file_path in file_path:
                                file_stem = Path(single_file_path).stem
                                if ch_name in file_stem:
                                    full_file_name = Path(single_file_path).name
                                    if '_' in file_stem:
                                        base_name = '_'.join(file_stem.split('_')[:-1])
                                    else:
                                        base_name = file_stem
                                    self.file_names_map[ch_name] = full_file_name
                                    self.file_base_names_map[ch_name] = base_name
                                    found = True
                                    break
                            if not found:
                                # Если не нашли, используем первый файл как fallback
                                self.file_names_map[ch_name] = file_names[0] if file_names else "Unknown"
                                if file_names and '_' in file_names[0]:
                                    base_name_from_file = file_names[0].replace('.csv', '').replace('.edf', '').replace('.set', '')
                                    if '_' in base_name_from_file:
                                        self.file_base_names_map[ch_name] = '_'.join(base_name_from_file.split('_')[:-1])
                                    else:
                                        self.file_base_names_map[ch_name] = base_name_from_file
                                else:
                                    self.file_base_names_map[ch_name] = file_names[0].replace('.csv', '').replace('.edf', '').replace('.set', '') if file_names else "Unknown"
                else:
                    self.loaded_file_paths = [file_path]
                    file_name = Path(file_path).name
                    file_stem = Path(file_path).stem
                    self.file_label.setText(f"Загружен: {file_name}")
                    # Для одного файла все каналы связаны с этим файлом
                    self.file_names_map = {ch_name: file_name for ch_name in self.channel_names}
                    # Извлекаем базовое название
                    if '_' in file_stem:
                        base_name = '_'.join(file_stem.split('_')[:-1])
                    else:
                        base_name = file_stem
                    self.file_base_names_map = {ch_name: base_name for ch_name in self.channel_names}
                
                self.update_channel_lists()
                
                # Инициализируем модули
                self.preprocessor = EEGPreprocessor(
                    self.current_data, 
                    self.sampling_rate, 
                    self.channel_names
                )
                self.analyzer = EEGAnalyzer(
                    self.current_data,
                    self.sampling_rate,
                    self.channel_names
                )
                self.visualizer = EEGVisualizer(
                    self.current_data,
                    self.sampling_rate,
                    self.channel_names
                )
                
                # Показываем информацию о данных
                summary = self.data_loader.get_data_summary()
                info_text = "Информация о загруженных данных:\n\n"
                for key, value in summary.items():
                    info_text += f"{key}: {value}\n"
                
                self.results_text.setText(info_text)
                self.statusBar().showMessage('Данные успешно загружены')
                
            except ValueError as e:
                error_msg = str(e)
                if "CSV" in error_msg or "разделитель" in error_msg.lower():
                    error_msg += "\n\nПодсказка: Убедитесь, что CSV файл использует один из разделителей: запятая (,), точка с запятой (;) или табуляция."
                QMessageBox.critical(self, "Ошибка загрузки", f"Не удалось загрузить файл:\n\n{error_msg}")
                self.statusBar().showMessage('Ошибка загрузки данных')
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                QMessageBox.critical(
                    self, 
                    "Ошибка", 
                    f"Не удалось загрузить файл:\n\n{str(e)}\n\nДетали:\n{error_details[:500]}"
                )
                self.statusBar().showMessage('Ошибка загрузки данных')
    
    def update_channel_lists(self):
        """Обновление списков каналов в интерфейсе"""
        # Формируем отображаемые названия каналов с названием файла
        display_names = []
        for ch_name in self.channel_names:
            base_name = self.file_base_names_map.get(ch_name, "")
            if base_name:
                display_name = f"{base_name} - {ch_name}"
            else:
                display_name = ch_name
            display_names.append(display_name)
        
        # Обновляем комбобокс для сигналов
        self.channel_combo.clear()
        self.channel_combo.addItem("Все каналы")
        for name in display_names:
            self.channel_combo.addItem(name)
        
        # Обновляем комбобокс для анализа
        self.analysis_channel_combo.clear()
        self.analysis_channel_combo.addItem("Средний по всем")
        for name in display_names:
            self.analysis_channel_combo.addItem(name)
        
        # Обновляем список каналов для предобработки
        if hasattr(self, 'preprocessing_channel_combo'):
            self.preprocessing_channel_combo.clear()
            self.preprocessing_channel_combo.addItem("Все каналы")
            for name in display_names:
                self.preprocessing_channel_combo.addItem(name)
    
    def plot_signals(self):
        """Построение графика сигналов"""
        if self.visualizer is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные")
            return
        
        try:
            channel_idx = self.channel_combo.currentIndex() - 1
            channels = None if channel_idx == -1 else [channel_idx]
            
            # Формируем информацию о файлах
            file_info = {}
            if channel_idx == -1:
                for i, ch_name in enumerate(self.channel_names):
                    file_info[i] = {
                        'base_name': self.file_base_names_map.get(ch_name, ""),
                        'file_name': self.file_names_map.get(ch_name, "")
                    }
            else:
                ch_name = self.channel_names[channel_idx]
                file_info[channel_idx] = {
                    'base_name': self.file_base_names_map.get(ch_name, ""),
                    'file_name': self.file_names_map.get(ch_name, "")
                }
            
            fig = self.visualizer.plot_raw_signals(channels=channels, file_info=file_info)
            self.signal_plot.plot_figure(fig)
            self.statusBar().showMessage('График построен')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при построении графика:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def apply_bandpass_filter(self):
        """Применение полосового фильтра"""
        if self.preprocessor is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные")
            return
        
        try:
            low_freq = self.low_freq_spin.value()
            high_freq = self.high_freq_spin.value()
            
            # Получаем выбранный канал для обработки
            channel_idx = self.preprocessing_channel_combo.currentIndex() - 1
            
            if channel_idx == -1:
                # Обрабатываем все каналы
                filtered_data = self.preprocessor.apply_bandpass_filter(low_freq, high_freq)
            else:
                # Обрабатываем только выбранный канал
                temp_data = self.current_data.copy()
                preprocessor_single = EEGPreprocessor(
                    temp_data[[channel_idx], :],
                    self.sampling_rate,
                    [self.channel_names[channel_idx]]
                )
                filtered_single = preprocessor_single.apply_bandpass_filter(low_freq, high_freq)
                filtered_data = self.current_data.copy()
                filtered_data[channel_idx, :] = filtered_single[0, :]
            
            self.current_data = filtered_data
            
            # Обновляем модули
            self.analyzer = EEGAnalyzer(filtered_data, self.sampling_rate, self.channel_names)
            self.visualizer = EEGVisualizer(filtered_data, self.sampling_rate, self.channel_names)
            
            # Показываем результат с информацией о файлах
            channels_to_show = None if channel_idx == -1 else [channel_idx]
            file_info = {}
            if channel_idx == -1:
                for i, ch_name in enumerate(self.channel_names):
                    file_info[i] = {
                        'base_name': self.file_base_names_map.get(ch_name, ""),
                        'file_name': self.file_names_map.get(ch_name, "")
                    }
            else:
                ch_name = self.channel_names[channel_idx]
                file_info[channel_idx] = {
                    'base_name': self.file_base_names_map.get(ch_name, ""),
                    'file_name': self.file_names_map.get(ch_name, "")
                }
            fig = self.visualizer.plot_raw_signals(channels=channels_to_show, file_info=file_info)
            self.preprocessed_plot.plot_figure(fig)
            
            channel_info = f" (канал {self.channel_names[channel_idx]})" if channel_idx != -1 else ""
            self.statusBar().showMessage(f'Применен полосовой фильтр {low_freq}-{high_freq} Гц{channel_info}')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при фильтрации:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def apply_notch_filter(self):
        """Применение режекторного фильтра"""
        if self.preprocessor is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные")
            return
        
        try:
            notch_freq = self.notch_freq_spin.value()
            
            # Получаем выбранный канал для обработки
            channel_idx = self.preprocessing_channel_combo.currentIndex() - 1
            
            if channel_idx == -1:
                # Обрабатываем все каналы
                filtered_data = self.preprocessor.apply_notch_filter(notch_freq)
            else:
                # Обрабатываем только выбранный канал
                temp_data = self.current_data.copy()
                preprocessor_single = EEGPreprocessor(
                    temp_data[[channel_idx], :],
                    self.sampling_rate,
                    [self.channel_names[channel_idx]]
                )
                filtered_single = preprocessor_single.apply_notch_filter(notch_freq)
                filtered_data = self.current_data.copy()
                filtered_data[channel_idx, :] = filtered_single[0, :]
            
            self.current_data = filtered_data
            
            # Обновляем модули
            self.analyzer = EEGAnalyzer(filtered_data, self.sampling_rate, self.channel_names)
            self.visualizer = EEGVisualizer(filtered_data, self.sampling_rate, self.channel_names)
            
            # Показываем результат на графике с информацией о файлах
            channels_to_show = None if channel_idx == -1 else [channel_idx]
            file_info = {}
            if channel_idx == -1:
                for i, ch_name in enumerate(self.channel_names):
                    file_info[i] = {
                        'base_name': self.file_base_names_map.get(ch_name, ""),
                        'file_name': self.file_names_map.get(ch_name, "")
                    }
            else:
                ch_name = self.channel_names[channel_idx]
                file_info[channel_idx] = {
                    'base_name': self.file_base_names_map.get(ch_name, ""),
                    'file_name': self.file_names_map.get(ch_name, "")
                }
            fig = self.visualizer.plot_raw_signals(channels=channels_to_show, file_info=file_info)
            self.preprocessed_plot.plot_figure(fig)
            
            channel_info = f" (канал {self.channel_names[channel_idx]})" if channel_idx != -1 else ""
            self.statusBar().showMessage(f'Применен режекторный фильтр на {notch_freq} Гц{channel_info}')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при фильтрации:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def remove_artifacts(self):
        """Удаление артефактов по порогу"""
        if self.preprocessor is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные")
            return
        
        try:
            threshold = self.threshold_spin.value()
            
            # Получаем выбранный канал для обработки
            channel_idx = self.preprocessing_channel_combo.currentIndex() - 1
            
            if channel_idx == -1:
                # Обрабатываем все каналы
                cleaned_data, _ = self.preprocessor.remove_artifacts_by_threshold(threshold)
            else:
                # Обрабатываем только выбранный канал
                temp_data = self.current_data.copy()
                preprocessor_single = EEGPreprocessor(
                    temp_data[[channel_idx], :],
                    self.sampling_rate,
                    [self.channel_names[channel_idx]]
                )
                cleaned_single, _ = preprocessor_single.remove_artifacts_by_threshold(threshold)
                cleaned_data = self.current_data.copy()
                cleaned_data[channel_idx, :] = cleaned_single[0, :]
            
            self.current_data = cleaned_data
            
            # Обновляем модули
            self.analyzer = EEGAnalyzer(cleaned_data, self.sampling_rate, self.channel_names)
            self.visualizer = EEGVisualizer(cleaned_data, self.sampling_rate, self.channel_names)
            
            # Показываем результат на графике с информацией о файлах
            channels_to_show = None if channel_idx == -1 else [channel_idx]
            file_info = {}
            if channel_idx == -1:
                for i, ch_name in enumerate(self.channel_names):
                    file_info[i] = {
                        'base_name': self.file_base_names_map.get(ch_name, ""),
                        'file_name': self.file_names_map.get(ch_name, "")
                    }
            else:
                ch_name = self.channel_names[channel_idx]
                file_info[channel_idx] = {
                    'base_name': self.file_base_names_map.get(ch_name, ""),
                    'file_name': self.file_names_map.get(ch_name, "")
                }
            fig = self.visualizer.plot_raw_signals(channels=channels_to_show, file_info=file_info)
            self.preprocessed_plot.plot_figure(fig)
            
            channel_info = f" (канал {self.channel_names[channel_idx]})" if channel_idx != -1 else ""
            self.statusBar().showMessage(f'Удалены артефакты с порогом {threshold} мкВ{channel_info}')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении артефактов:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def remove_blinks(self):
        """Удаление артефактов моргания"""
        if self.preprocessor is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные")
            return
        
        try:
            # Получаем выбранный канал для обработки
            channel_idx = self.preprocessing_channel_combo.currentIndex() - 1
            
            if channel_idx == -1:
                # Обрабатываем все каналы
                cleaned_data = self.preprocessor.remove_blink_artifacts()
            else:
                # Обрабатываем только выбранный канал
                temp_data = self.current_data.copy()
                preprocessor_single = EEGPreprocessor(
                    temp_data[[channel_idx], :],
                    self.sampling_rate,
                    [self.channel_names[channel_idx]]
                )
                cleaned_single = preprocessor_single.remove_blink_artifacts()
                cleaned_data = self.current_data.copy()
                cleaned_data[channel_idx, :] = cleaned_single[0, :]
            
            self.current_data = cleaned_data
            
            # Обновляем модули
            self.analyzer = EEGAnalyzer(cleaned_data, self.sampling_rate, self.channel_names)
            self.visualizer = EEGVisualizer(cleaned_data, self.sampling_rate, self.channel_names)
            
            # Показываем результат на графике с информацией о файлах
            channels_to_show = None if channel_idx == -1 else [channel_idx]
            file_info = {}
            if channel_idx == -1:
                for i, ch_name in enumerate(self.channel_names):
                    file_info[i] = {
                        'base_name': self.file_base_names_map.get(ch_name, ""),
                        'file_name': self.file_names_map.get(ch_name, "")
                    }
            else:
                ch_name = self.channel_names[channel_idx]
                file_info[channel_idx] = {
                    'base_name': self.file_base_names_map.get(ch_name, ""),
                    'file_name': self.file_names_map.get(ch_name, "")
                }
            fig = self.visualizer.plot_raw_signals(channels=channels_to_show, file_info=file_info)
            self.preprocessed_plot.plot_figure(fig)
            
            channel_info = f" (канал {self.channel_names[channel_idx]})" if channel_idx != -1 else ""
            self.statusBar().showMessage(f'Удалены артефакты моргания{channel_info}')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении морганий:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def analyze_psd(self):
        """Анализ спектра мощности"""
        if self.analyzer is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные")
            return
        
        try:
            channel_idx = self.analysis_channel_combo.currentIndex() - 1
            is_average = (channel_idx == -1)
            
            # Если выбран "Средний по всем", используем первый канал для визуализации
            # но анализируем средний по всем
            if is_average:
                vis_channel = 0
                # Для среднего используем первый канал для получения имени файла
                channel_name = self.channel_names[vis_channel]
                file_name = self.file_names_map.get(channel_name, "")
                # Создаем визуализатор с информацией о файле
                current_visualizer = EEGVisualizer(self.current_data, self.sampling_rate, self.channel_names)
                # Для среднего передаем None как channel_idx, но используем vis_channel для визуализации
                current_analyzer = EEGAnalyzer(self.current_data, self.sampling_rate, self.channel_names)
                freqs, psd = current_analyzer.compute_psd(None, method='welch')  # None = средний по всем
                # Создаем график вручную
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.semilogy(freqs, psd, linewidth=2.0, color='#2E7D32', label='Спектр мощности (средний)')
                ax.set_xlabel('Частота (Гц)', fontsize=12, fontweight='bold')
                ax.set_ylabel('Спектральная плотность мощности (логарифмическая шкала)', fontsize=11, fontweight='bold')
                
                # Формируем заголовок
                base_name = self.file_base_names_map.get(channel_name, "")
                if base_name:
                    title = f'Спектр мощности - Средний по всем ({base_name})'
                else:
                    title = 'Спектр мощности - Средний по всем'
                ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
                ax.grid(True, alpha=0.4, linestyle='--', linewidth=0.8)
                plt.tight_layout()
            else:
                vis_channel = channel_idx
                channel_name = self.channel_names[vis_channel]
                file_name = self.file_names_map.get(channel_name, "")
                current_visualizer = EEGVisualizer(self.current_data, self.sampling_rate, self.channel_names)
                fig = current_visualizer.plot_spectrum(vis_channel, file_name=file_name)
            
            self.analysis_plot.plot_figure(fig)
            self.statusBar().showMessage('Спектр мощности построен')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при анализе:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def analyze_bands(self):
        """Анализ мощности ритмов"""
        if self.analyzer is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные")
            return
        
        try:
            channel_idx = self.analysis_channel_combo.currentIndex() - 1
            is_average = (channel_idx == -1)
            analysis_channel_idx = None if is_average else channel_idx
            
            # Исправление: создаем новый анализатор с актуальными данными
            current_analyzer = EEGAnalyzer(self.current_data, self.sampling_rate, self.channel_names)
            current_visualizer = EEGVisualizer(self.current_data, self.sampling_rate, self.channel_names)
            
            # Для визуализации используем первый канал, если выбран "Средний по всем"
            if is_average:
                vis_channel = 0
                channel_name = self.channel_names[vis_channel]
                file_name = self.file_names_map.get(channel_name, "")
                base_name = self.file_base_names_map.get(channel_name, "")
            else:
                vis_channel = channel_idx
                channel_name = self.channel_names[vis_channel]
                file_name = self.file_names_map.get(channel_name, "")
                base_name = self.file_base_names_map.get(channel_name, "")
            
            # Передаем None для анализа среднего, но используем vis_channel для визуализации
            fig = current_visualizer.plot_relative_band_powers(analysis_channel_idx, file_name=file_name)
            self.analysis_plot.plot_figure(fig)
            
            # Выводим результаты в текстовое поле
            band_powers = current_analyzer.compute_all_band_powers(analysis_channel_idx)
            rel_powers = current_analyzer.compute_relative_band_power(analysis_channel_idx)
            
            # Формируем заголовок с информацией о файле и канале
            if is_average:
                if base_name:
                    header = f"Мощность частотных диапазонов - Средний по всем ({base_name})\n\n"
                else:
                    header = "Мощность частотных диапазонов - Средний по всем каналам\n\n"
            else:
                ch_name = self.channel_names[channel_idx]
                base_name = self.file_base_names_map.get(ch_name, "")
                if base_name:
                    header = f"Мощность частотных диапазонов - {base_name} ({ch_name})\n\n"
                else:
                    header = f"Мощность частотных диапазонов - {ch_name}\n\n"
            
            results_text = header
            results_text += "Абсолютная мощность:\n"
            band_labels = {
                'delta': 'Дельта (0.5-4 Гц)',
                'theta': 'Тета (4-8 Гц)',
                'alpha': 'Альфа (8-13 Гц)',
                'beta': 'Бета (13-30 Гц)',
                'gamma': 'Гамма (30-100 Гц)'
            }
            for band, power in band_powers.items():
                label = band_labels.get(band, band.capitalize())
                results_text += f"  {label}: {power:.4f}\n"
            
            results_text += "\nОтносительная мощность (%):\n"
            for band, power in rel_powers.items():
                label = band_labels.get(band, band.capitalize())
                results_text += f"  {label}: {power:.2f}%\n"
            
            self.results_text.setText(results_text)
            self.statusBar().showMessage('Анализ ритмов выполнен')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при анализе:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def extract_features(self):
        """Извлечение признаков"""
        if self.analyzer is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные")
            return
        
        try:
            channel_idx = self.analysis_channel_combo.currentIndex() - 1
            channel_idx = None if channel_idx == -1 else channel_idx
            
            # Исправление: используем актуальные данные
            current_analyzer = EEGAnalyzer(self.current_data, self.sampling_rate, self.channel_names)
            features = current_analyzer.extract_features(channel_idx)
            
            # Формируем заголовок с информацией о файле и канале
            if channel_idx is not None:
                ch_name = self.channel_names[channel_idx]
                base_name = self.file_base_names_map.get(ch_name, "")
                if base_name:
                    header = f"Извлеченные признаки - {base_name} ({ch_name})\n\n"
                else:
                    header = f"Извлеченные признаки - {ch_name}\n\n"
            else:
                header = "Извлеченные признаки - Средний по всем каналам\n\n"
            
            # Выводим результаты
            results_text = header
            
            # Группируем признаки по категориям
            categories = {
                'Статистические признаки': ['mean', 'std', 'variance', 'skewness', 'kurtosis'],
                'Мощность ритмов': ['delta_power', 'theta_power', 'alpha_power', 'beta_power', 'gamma_power'],
                'Относительная мощность (%)': ['delta_relative_power', 'theta_relative_power', 
                                                 'alpha_relative_power', 'beta_relative_power', 'gamma_relative_power'],
                'Спектральные признаки': ['peak_frequency', 'spectral_centroid', 'spectral_bandwidth'],
                'Прочие': ['shannon_entropy']
            }
            
            for category, keys in categories.items():
                category_features = {k: v for k, v in features.items() if k in keys}
                if category_features:
                    results_text += f"{category}:\n"
                    for key, value in category_features.items():
                        if isinstance(value, float):
                            results_text += f"  {key}: {value:.4f}\n"
                        else:
                            results_text += f"  {key}: {value}\n"
                    results_text += "\n"
            
            # Добавляем оставшиеся признаки
            remaining = {k: v for k, v in features.items() 
                         if k not in [item for sublist in categories.values() for item in sublist]}
            if remaining:
                results_text += "Прочие признаки:\n"
                for key, value in remaining.items():
                    if isinstance(value, float):
                        results_text += f"  {key}: {value:.4f}\n"
                    else:
                        results_text += f"  {key}: {value}\n"
            
            self.results_text.setText(results_text)
            
            # Автоматическое переключение на вкладку результатов
            self.tabs.setCurrentIndex(3)  # Индекс вкладки "Результаты"
            
            self.statusBar().showMessage('Признаки извлечены')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при извлечении признаков:\n{str(e)}")
    
    def export_results(self):
        """Экспорт результатов"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результаты",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.toPlainText())
                QMessageBox.information(self, "Успех", "Результаты сохранены")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    window = EEGAnalysisApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
