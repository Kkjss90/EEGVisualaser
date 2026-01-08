"""
Модуль визуализации данных ЭЭГ
Включает построение графиков сигналов, спектров, топографических карт
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mne.viz import plot_topomap
from mne import create_info
from typing import Optional, List, Tuple, Dict
import warnings

# Импорт для анализа (избегаем циклических импортов)
from .analysis import EEGAnalyzer

warnings.filterwarnings('ignore')

# Настройка для поддержки русского языка в matplotlib
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']


class EEGVisualizer:
    """Класс для визуализации данных ЭЭГ"""
    
    def __init__(self, data: np.ndarray, sampling_rate: float, channel_names: List[str]):
        """
        Инициализация визуализатора
        
        Args:
            data: Массив данных ЭЭГ (каналы x время)
            sampling_rate: Частота дискретизации
            channel_names: Список имен каналов
        """
        self.data = data
        self.sampling_rate = sampling_rate
        self.channel_names = channel_names
        self.n_channels = len(channel_names)
    
    def plot_raw_signals(self, channels: Optional[List[int]] = None, 
                        time_range: Optional[Tuple[float, float]] = None,
                        figsize: Tuple[int, int] = (15, 10),
                        file_info: Optional[Dict] = None) -> Figure:
        """
        Построение графика исходных сигналов ЭЭГ
        
        Args:
            channels: Список индексов каналов для отображения (None для всех)
            time_range: Диапазон времени в секундах (начало, конец)
            figsize: Размер фигуры
            file_info: Словарь с информацией о файлах {channel_idx: {'base_name': str, 'file_name': str}}
            
        Returns:
            Объект Figure matplotlib
        """
        if channels is None:
            channels = list(range(self.n_channels))
        
        # Определяем диапазон времени
        if time_range:
            start_sample = int(time_range[0] * self.sampling_rate)
            end_sample = int(time_range[1] * self.sampling_rate)
            time_data = self.data[:, start_sample:end_sample]
            time_axis = np.arange(start_sample, end_sample) / self.sampling_rate
        else:
            time_data = self.data
            time_axis = np.arange(self.data.shape[1]) / self.sampling_rate
        
        fig, axes = plt.subplots(len(channels), 1, figsize=figsize, sharex=True)
        
        if len(channels) == 1:
            axes = [axes]
        
        # Смещение для визуального разделения каналов
        offset = np.max(np.abs(time_data)) * 1.5
        
        # Цвета для разных каналов
        colors = plt.cm.tab10(np.linspace(0, 1, len(channels)))
        
        for idx, ch_idx in enumerate(channels):
            ch_name = self.channel_names[ch_idx]
            # Формируем подпись канала с названием файла
            if file_info and ch_idx in file_info:
                base_name = file_info[ch_idx].get('base_name', '')
                if base_name:
                    ylabel = f"{base_name} - {ch_name}"
                else:
                    ylabel = ch_name
            else:
                ylabel = ch_name
            
            axes[idx].plot(time_axis, time_data[ch_idx, :] + idx * offset, 
                          linewidth=1.0, color=colors[idx], label=ylabel)
            axes[idx].set_ylabel(ylabel, rotation=0, ha='right', fontsize=10, fontweight='bold')
            axes[idx].grid(True, alpha=0.3, linestyle='--')
            axes[idx].set_yticks([])
            axes[idx].legend(loc='upper right', fontsize=9)
        
        axes[-1].set_xlabel('Время (сек)', fontsize=11, fontweight='bold')
        axes[0].set_title('Сигналы ЭЭГ', fontsize=12, fontweight='bold', pad=15)
        plt.tight_layout()
        
        return fig
    
    def plot_spectrum(self, channel_idx: int, method: str = 'welch',
                     figsize: Tuple[int, int] = (10, 6), file_name: Optional[str] = None) -> Figure:
        """
        Построение спектра мощности для одного канала
        
        Args:
            channel_idx: Индекс канала
            method: Метод вычисления ('welch' или 'fft')
            figsize: Размер фигуры
            file_name: Имя файла для отображения в заголовке
            
        Returns:
            Объект Figure matplotlib
        """
        analyzer = EEGAnalyzer(self.data, self.sampling_rate, self.channel_names)
        freqs, psd = analyzer.compute_psd(channel_idx, method=method)
        
        fig, ax = plt.subplots(figsize=figsize)
        ax.semilogy(freqs, psd, linewidth=2.0, color='#2E7D32', label='Спектр мощности')
        ax.set_xlabel('Частота (Гц)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Спектральная плотность мощности (логарифмическая шкала)', fontsize=11, fontweight='bold')
        
        # Формируем заголовок с именем канала и файла
        channel_name = self.channel_names[channel_idx]
        # Извлекаем базовое название из file_name, если оно есть
        if file_name:
            # Если file_name содержит подчеркивание, берем часть до последнего
            if '_' in file_name:
                base_name = '_'.join(file_name.replace('.csv', '').replace('.edf', '').replace('.set', '').split('_')[:-1])
            else:
                base_name = file_name.replace('.csv', '').replace('.edf', '').replace('.set', '')
            title = f'Спектр мощности - {base_name} ({channel_name})'
        else:
            title = f'Спектр мощности - {channel_name}'
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.4, linestyle='--', linewidth=0.8)
        
        plt.tight_layout()
        
        return fig
    
    def plot_band_powers(self, channel_idx: Optional[int] = None,
                        figsize: Tuple[int, int] = (10, 6),
                        file_name: Optional[str] = None) -> Figure:
        """
        Построение графика мощности ритмов
        
        Args:
            channel_idx: Индекс канала (None для среднего по всем)
            figsize: Размер фигуры
            file_name: Имя файла для отображения в заголовке
            
        Returns:
            Объект Figure matplotlib
        """
        analyzer = EEGAnalyzer(self.data, self.sampling_rate, self.channel_names)
        band_powers = analyzer.compute_all_band_powers(channel_idx)
        
        bands = list(band_powers.keys())
        powers = list(band_powers.values())
        
        # Улучшенные цвета и подписи для ритмов
        band_colors = {
            'delta': '#d32f2f',    # Красный - Дельта
            'theta': '#f57c00',    # Оранжевый - Тета
            'alpha': '#388e3c',    # Зеленый - Альфа
            'beta': '#1976d2',     # Синий - Бета
            'gamma': '#7b1fa2'     # Фиолетовый - Гамма
        }
        
        band_labels = {
            'delta': 'Дельта (0.5-4 Гц)',
            'theta': 'Тета (4-8 Гц)',
            'alpha': 'Альфа (8-13 Гц)',
            'beta': 'Бета (13-30 Гц)',
            'gamma': 'Гамма (30-100 Гц)'
        }
        
        colors = [band_colors.get(band, '#666666') for band in bands]
        labels = [band_labels.get(band, band.capitalize()) for band in bands]
        
        fig, ax = plt.subplots(figsize=figsize)
        bars = ax.bar(labels, powers, color=colors, edgecolor='black', linewidth=1.2)
        ax.set_ylabel('Абсолютная мощность', fontsize=12, fontweight='bold')
        ax.set_xlabel('Частотные диапазоны', fontsize=11, fontweight='bold')
        
        # Формируем заголовок с именем канала и файла
        if channel_idx is not None:
            channel_name = self.channel_names[channel_idx]
            if file_name:
                if '_' in file_name:
                    base_name = '_'.join(file_name.replace('.csv', '').replace('.edf', '').replace('.set', '').split('_')[:-1])
                else:
                    base_name = file_name.replace('.csv', '').replace('.edf', '').replace('.set', '')
                title = f'Мощность ритмов - {base_name} ({channel_name})'
            else:
                title = f'Мощность ритмов - {channel_name}'
        else:
            if file_name:
                if '_' in file_name:
                    base_name = '_'.join(file_name.replace('.csv', '').replace('.edf', '').replace('.set', '').split('_')[:-1])
                else:
                    base_name = file_name.replace('.csv', '').replace('.edf', '').replace('.set', '')
                title = f'Мощность ритмов - Средний по всем ({base_name})'
            else:
                title = 'Мощность ритмов - Средний по всем'
        
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.4, axis='y', linestyle='--', linewidth=0.8)
        
        # Добавляем значения на столбцы
        for bar, power in zip(bars, powers):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{power:.2f}', ha='center', va='bottom', 
                   fontsize=10, fontweight='bold')
        
        # Поворачиваем подписи оси X для лучшей читаемости
        plt.setp(ax.get_xticklabels(), rotation=15, ha='right')
        plt.tight_layout()
        
        return fig
    
    def plot_relative_band_powers(self, channel_idx: Optional[int] = None,
                                 figsize: Tuple[int, int] = (10, 6), 
                                 file_name: Optional[str] = None) -> Figure:
        """
        Построение графика относительной мощности ритмов
        
        Args:
            channel_idx: Индекс канала
            figsize: Размер фигуры
            file_name: Имя файла для отображения в заголовке
            
        Returns:
            Объект Figure matplotlib
        """
        analyzer = EEGAnalyzer(self.data, self.sampling_rate, self.channel_names)
        rel_powers = analyzer.compute_relative_band_power(channel_idx)
        
        bands = list(rel_powers.keys())
        powers = list(rel_powers.values())
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Улучшенные цвета и подписи для ритмов
        band_colors = {
            'delta': '#d32f2f',    # Красный - Дельта
            'theta': '#f57c00',    # Оранжевый - Тета
            'alpha': '#388e3c',    # Зеленый - Альфа
            'beta': '#1976d2',     # Синий - Бета
            'gamma': '#7b1fa2'     # Фиолетовый - Гамма
        }
        
        band_labels = {
            'delta': 'Дельта (0.5-4 Гц)',
            'theta': 'Тета (4-8 Гц)',
            'alpha': 'Альфа (8-13 Гц)',
            'beta': 'Бета (13-30 Гц)',
            'gamma': 'Гамма (30-100 Гц)'
        }
        
        colors = [band_colors.get(band, '#666666') for band in bands]
        labels = [band_labels.get(band, band.capitalize()) for band in bands]
        
        bars = ax.bar(labels, powers, color=colors, edgecolor='black', linewidth=1.2)
        ax.set_ylabel('Относительная мощность (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Частотные диапазоны', fontsize=11, fontweight='bold')
        
        # Формируем заголовок с именем канала и файла
        if channel_idx is not None:
            channel_name = self.channel_names[channel_idx]
            if file_name:
                # Извлекаем базовое название
                if '_' in file_name:
                    base_name = '_'.join(file_name.replace('.csv', '').replace('.edf', '').replace('.set', '').split('_')[:-1])
                else:
                    base_name = file_name.replace('.csv', '').replace('.edf', '').replace('.set', '')
                title = f'Относительная мощность ритмов - {base_name} ({channel_name})'
            else:
                title = f'Относительная мощность ритмов - {channel_name}'
        else:
            # Для среднего по всем используем первый канал для получения базового имени
            if file_name:
                if '_' in file_name:
                    base_name = '_'.join(file_name.replace('.csv', '').replace('.edf', '').replace('.set', '').split('_')[:-1])
                else:
                    base_name = file_name.replace('.csv', '').replace('.edf', '').replace('.set', '')
                title = f'Относительная мощность ритмов - Средний по всем ({base_name})'
            else:
                title = 'Относительная мощность ритмов - Средний по всем'
        
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.4, axis='y', linestyle='--', linewidth=0.8)
        
        # Добавляем значения на столбцы с улучшенным форматированием
        for bar, power in zip(bars, powers):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{power:.1f}%', ha='center', va='bottom', 
                   fontsize=10, fontweight='bold')
        
        # Поворачиваем подписи оси X для лучшей читаемости
        plt.setp(ax.get_xticklabels(), rotation=15, ha='right')
        
        # Добавляем легенду с цветами ритмов
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#d32f2f', label='Дельта (0.5-4 Гц)'),
            Patch(facecolor='#f57c00', label='Тета (4-8 Гц)'),
            Patch(facecolor='#388e3c', label='Альфа (8-13 Гц)'),
            Patch(facecolor='#1976d2', label='Бета (13-30 Гц)'),
            Patch(facecolor='#7b1fa2', label='Гамма (30-100 Гц)')
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=9, 
                 framealpha=0.9, shadow=True, title='Частотные диапазоны')
        
        plt.tight_layout()
        
        return fig
    
    def plot_topographic_map(self, values: np.ndarray, title: str = 'Топографическая карта',
                            figsize: Tuple[int, int] = (8, 6)) -> Figure:
        """
        Построение топографической карты
        
        Args:
            values: Массив значений для каждого канала
            title: Заголовок графика
            figsize: Размер фигуры
            
        Returns:
            Объект Figure matplotlib
        """
        # Создаем объект Info для MNE
        info = create_info(
            ch_names=self.channel_names,
            sfreq=self.sampling_rate,
            ch_types=['eeg'] * self.n_channels
        )
        
        # Пытаемся использовать стандартные позиции каналов
        try:
            from mne.channels import make_standard_montage
            montage = make_standard_montage('standard_1020')
            info.set_montage(montage)
        except:
            # Если не удалось, используем сферическую модель
            pass
        
        fig, ax = plt.subplots(figsize=figsize)
        
        try:
            im, _ = plot_topomap(
                values,
                info,
                axes=ax,
                show=False,
                cmap='RdBu_r'
            )
            plt.colorbar(im, ax=ax)
            ax.set_title(title)
        except Exception as e:
            # Если топографическая карта не может быть построена,
            # строим простой график
            ax.bar(range(len(values)), values)
            ax.set_xticks(range(len(self.channel_names)))
            ax.set_xticklabels(self.channel_names, rotation=45, ha='right')
            ax.set_ylabel('Значение')
            ax.set_title(f'{title} (упрощенный вид)')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return fig
    
    def plot_correlation_matrix(self, figsize: Tuple[int, int] = (10, 8)) -> Figure:
        """
        Построение матрицы корреляции между каналами
        
        Args:
            figsize: Размер фигуры
            
        Returns:
            Объект Figure matplotlib
        """
        analyzer = EEGAnalyzer(self.data, self.sampling_rate, self.channel_names)
        corr_matrix = analyzer.compute_correlation_matrix()
        
        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
        
        # Добавляем значения в ячейки
        for i in range(len(self.channel_names)):
            for j in range(len(self.channel_names)):
                text = ax.text(j, i, f'{corr_matrix[i, j]:.2f}',
                             ha="center", va="center", color="black", fontsize=8)
        
        ax.set_xticks(range(len(self.channel_names)))
        ax.set_yticks(range(len(self.channel_names)))
        ax.set_xticklabels(self.channel_names, rotation=45, ha='right')
        ax.set_yticklabels(self.channel_names)
        ax.set_title('Матрица корреляции между каналами')
        
        plt.colorbar(im, ax=ax, label='Корреляция')
        plt.tight_layout()
        
        return fig
    
    def plot_time_frequency(self, channel_idx: int, figsize: Tuple[int, int] = (12, 6)) -> Figure:
        """
        Построение временно-частотного представления (спектрограмма)
        
        Args:
            channel_idx: Индекс канала
            figsize: Размер фигуры
            
        Returns:
            Объект Figure matplotlib
        """
        from scipy import signal
        
        channel_data = self.data[channel_idx, :]
        
        # Вычисление спектрограммы
        freqs, times, Sxx = signal.spectrogram(
            channel_data,
            fs=self.sampling_rate,
            nperseg=int(self.sampling_rate * 2),  # 2 секунды
            noverlap=int(self.sampling_rate * 1)   # 1 секунда перекрытия
        )
        
        fig, ax = plt.subplots(figsize=figsize)
        im = ax.pcolormesh(times, freqs, 10 * np.log10(Sxx + 1e-10), 
                          shading='gouraud', cmap='viridis')
        ax.set_ylabel('Частота (Гц)')
        ax.set_xlabel('Время (сек)')
        ax.set_title(f'Спектрограмма - {self.channel_names[channel_idx]}')
        plt.colorbar(im, ax=ax, label='Мощность (дБ)')
        plt.tight_layout()
        
        return fig
    
    def plot_all_channels_spectrum(self, figsize: Tuple[int, int] = (15, 10)) -> Figure:
        """
        Построение спектров всех каналов
        
        Args:
            figsize: Размер фигуры
            
        Returns:
            Объект Figure matplotlib
        """
        analyzer = EEGAnalyzer(self.data, self.sampling_rate, self.channel_names)
        
        n_cols = 3
        n_rows = (self.n_channels + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        axes = axes.flatten() if self.n_channels > 1 else [axes]
        
        for ch_idx in range(self.n_channels):
            freqs, psd = analyzer.compute_psd(ch_idx)
            axes[ch_idx].semilogy(freqs, psd, linewidth=1)
            axes[ch_idx].set_title(self.channel_names[ch_idx])
            axes[ch_idx].set_xlabel('Частота (Гц)')
            axes[ch_idx].set_ylabel('PSD')
            axes[ch_idx].grid(True, alpha=0.3)
        
        # Скрываем лишние subplot'ы
        for idx in range(self.n_channels, len(axes)):
            axes[idx].set_visible(False)
        
        plt.suptitle('Спектры мощности всех каналов', y=1.02)
        plt.tight_layout()
        
        return fig

