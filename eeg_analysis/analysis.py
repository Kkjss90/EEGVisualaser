"""
Модуль анализа данных ЭЭГ
Включает спектральный анализ, детекцию спайков, выделение признаков
"""

import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.stats import zscore
from scipy.integrate import trapezoid
import pywt
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')


class EEGAnalyzer:
    """Класс для анализа данных ЭЭГ"""
    
    # Определение частотных диапазонов ритмов ЭЭГ
    BAND_DELTA = (0.5, 4.0)    # Дельта
    BAND_THETA = (4.0, 8.0)    # Тета
    BAND_ALPHA = (8.0, 13.0)   # Альфа
    BAND_BETA = (13.0, 30.0)   # Бета
    BAND_GAMMA = (30.0, 100.0) # Гамма
    
    def __init__(self, data: np.ndarray, sampling_rate: float, channel_names: List[str]):
        """
        Инициализация анализатора
        
        Args:
            data: Массив данных ЭЭГ (каналы x время)
            sampling_rate: Частота дискретизации
            channel_names: Список имен каналов
        """
        self.data = data
        self.sampling_rate = sampling_rate
        self.channel_names = channel_names
        self.n_channels, self.n_samples = data.shape
    
    def compute_psd(self, channel_idx: Optional[int] = None, 
                   method: str = 'welch', nperseg: int = 256) -> Tuple[np.ndarray, np.ndarray]:
        """
        Вычисление спектральной плотности мощности (PSD)
        
        Args:
            channel_idx: Индекс канала (None для всех каналов)
            method: Метод ('welch' или 'fft')
            nperseg: Длина сегмента для метода Уэлча
            
        Returns:
            Кортеж (частоты, PSD)
        """
        if channel_idx is not None:
            signal_data = self.data[channel_idx, :]
        else:
            signal_data = np.mean(self.data, axis=0)
        
        if method == 'welch':
            freqs, psd = signal.welch(
                signal_data,
                fs=self.sampling_rate,
                nperseg=nperseg,
                noverlap=nperseg // 2
            )
        else:  # FFT
            # Применяем окно Ханна для уменьшения утечки спектра
            windowed = signal_data * signal.windows.hann(len(signal_data))
            fft_vals = fft(windowed)
            freqs = fftfreq(len(windowed), 1 / self.sampling_rate)
            
            # Берем только положительные частоты
            positive_freq_idx = freqs > 0
            freqs = freqs[positive_freq_idx]
            psd = np.abs(fft_vals[positive_freq_idx]) ** 2
        
        return freqs, psd
    
    def compute_band_power(self, channel_idx: Optional[int] = None, 
                          band: Tuple[float, float] = None) -> float:
        """
        Вычисление мощности в заданном частотном диапазоне
        
        Args:
            channel_idx: Индекс канала (None для среднего по всем)
            band: Кортеж (нижняя частота, верхняя частота)
            
        Returns:
            Мощность в диапазоне
        """
        freqs, psd = self.compute_psd(channel_idx)
        
        if band is None:
            band = self.BAND_ALPHA
        
        # Находим индексы частот в диапазоне
        freq_mask = (freqs >= band[0]) & (freqs <= band[1])
        band_power = trapezoid(psd[freq_mask], freqs[freq_mask])
        
        return band_power
    
    def compute_all_band_powers(self, channel_idx: Optional[int] = None) -> Dict[str, float]:
        """
        Вычисление мощности всех основных ритмов
        
        Args:
            channel_idx: Индекс канала
            
        Returns:
            Словарь с мощностями ритмов
        """
        bands = {
            'delta': self.BAND_DELTA,
            'theta': self.BAND_THETA,
            'alpha': self.BAND_ALPHA,
            'beta': self.BAND_BETA,
            'gamma': self.BAND_GAMMA
        }
        
        band_powers = {}
        for band_name, band_range in bands.items():
            band_powers[band_name] = self.compute_band_power(channel_idx, band_range)
        
        return band_powers
    
    def compute_relative_band_power(self, channel_idx: Optional[int] = None) -> Dict[str, float]:
        """
        Вычисление относительной мощности ритмов (в процентах от общей мощности)
        
        Args:
            channel_idx: Индекс канала
            
        Returns:
            Словарь с относительными мощностями
        """
        all_powers = self.compute_all_band_powers(channel_idx)
        total_power = sum(all_powers.values())
        
        relative_powers = {}
        for band_name, power in all_powers.items():
            relative_powers[band_name] = (power / total_power) * 100 if total_power > 0 else 0
        
        return relative_powers
    
    def detect_spikes(self, channel_idx: int, threshold: float = 3.0, 
                     min_duration_ms: float = 10.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Детекция спайков (острых всплесков активности)
        
        Args:
            channel_idx: Индекс канала
            threshold: Порог в стандартных отклонениях
            min_duration_ms: Минимальная длительность спайка в миллисекундах
            
        Returns:
            Кортеж (индексы спайков, амплитуды спайков)
        """
        channel_data = self.data[channel_idx, :]
        
        # Z-score нормализация
        z_scores = np.abs(zscore(channel_data))
        
        # Детекция превышений порога
        spike_mask = z_scores > threshold
        
        # Фильтрация по минимальной длительности
        min_duration_samples = int(min_duration_ms * self.sampling_rate / 1000)
        
        # Находим непрерывные области
        spike_indices = []
        spike_amplitudes = []
        
        i = 0
        while i < len(spike_mask):
            if spike_mask[i]:
                start = i
                while i < len(spike_mask) and spike_mask[i]:
                    i += 1
                end = i
                
                # Проверяем минимальную длительность
                if (end - start) >= min_duration_samples:
                    # Находим пик в этой области
                    region = channel_data[start:end]
                    peak_idx = start + np.argmax(np.abs(region))
                    spike_indices.append(peak_idx)
                    spike_amplitudes.append(channel_data[peak_idx])
            else:
                i += 1
        
        return np.array(spike_indices), np.array(spike_amplitudes)
    
    def compute_wavelet_transform(self, channel_idx: int, wavelet: str = 'db4', 
                                  levels: int = 5) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Вейвлет-преобразование для анализа временно-частотных характеристик
        
        Args:
            channel_idx: Индекс канала
            wavelet: Тип вейвлета ('db4', 'haar', 'coif2', etc.)
            levels: Количество уровней декомпозиции
            
        Returns:
            Кортеж (коэффициенты аппроксимации и деталей, частоты уровней)
        """
        channel_data = self.data[channel_idx, :]
        
        # Вейвлет-преобразование
        coeffs = pywt.wavedec(channel_data, wavelet, level=levels)
        
        # Вычисление частотных диапазонов для каждого уровня
        level_freqs = []
        for level in range(levels + 1):
            if level == 0:
                # Аппроксимация (низкие частоты)
                freq_range = (0, self.sampling_rate / (2 ** (levels + 1)))
            else:
                # Детали (высокие частоты)
                freq_range = (
                    self.sampling_rate / (2 ** (levels - level + 2)),
                    self.sampling_rate / (2 ** (levels - level + 1))
                )
            level_freqs.append(freq_range)
        
        return coeffs, level_freqs
    
    def extract_features(self, channel_idx: Optional[int] = None) -> Dict[str, float]:
        """
        Извлечение признаков из сигнала ЭЭГ
        
        Args:
            channel_idx: Индекс канала (None для среднего по всем)
            
        Returns:
            Словарь признаков
        """
        if channel_idx is not None:
            signal_data = self.data[channel_idx, :]
        else:
            signal_data = np.mean(self.data, axis=0)
        
        features = {}
        
        # Статистические признаки
        features['mean'] = np.mean(signal_data)
        features['std'] = np.std(signal_data)
        features['variance'] = np.var(signal_data)
        features['skewness'] = self._compute_skewness(signal_data)
        features['kurtosis'] = self._compute_kurtosis(signal_data)
        
        # Частотные признаки
        band_powers = self.compute_all_band_powers(channel_idx)
        for band, power in band_powers.items():
            features[f'{band}_power'] = power
        
        relative_powers = self.compute_relative_band_power(channel_idx)
        for band, rel_power in relative_powers.items():
            features[f'{band}_relative_power'] = rel_power
        
        # Спектральные признаки
        freqs, psd = self.compute_psd(channel_idx)
        features['peak_frequency'] = freqs[np.argmax(psd)]
        features['spectral_centroid'] = np.sum(freqs * psd) / np.sum(psd) if np.sum(psd) > 0 else 0
        features['spectral_bandwidth'] = np.sqrt(np.sum(((freqs - features['spectral_centroid']) ** 2) * psd) / np.sum(psd)) if np.sum(psd) > 0 else 0
        
        # Энтропия
        features['shannon_entropy'] = self._compute_shannon_entropy(signal_data)
        
        return features
    
    def _compute_skewness(self, data: np.ndarray) -> float:
        """Вычисление асимметрии"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std) ** 3)
    
    def _compute_kurtosis(self, data: np.ndarray) -> float:
        """Вычисление эксцесса"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std) ** 4) - 3
    
    def _compute_shannon_entropy(self, data: np.ndarray, bins: int = 50) -> float:
        """Вычисление энтропии Шеннона"""
        hist, _ = np.histogram(data, bins=bins)
        hist = hist[hist > 0]  # Убираем нули
        prob = hist / np.sum(hist)
        return -np.sum(prob * np.log2(prob))
    
    def compute_coherence(self, ch1_idx: int, ch2_idx: int, 
                         freq_range: Tuple[float, float] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Вычисление когерентности между двумя каналами
        
        Args:
            ch1_idx: Индекс первого канала
            ch2_idx: Индекс второго канала
            freq_range: Диапазон частот для анализа
            
        Returns:
            Кортеж (частоты, когерентность)
        """
        signal1 = self.data[ch1_idx, :]
        signal2 = self.data[ch2_idx, :]
        
        freqs, coherence = signal.coherence(signal1, signal2, fs=self.sampling_rate)
        
        if freq_range:
            freq_mask = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
            freqs = freqs[freq_mask]
            coherence = coherence[freq_mask]
        
        return freqs, coherence
    
    def compute_correlation_matrix(self) -> np.ndarray:
        """
        Вычисление матрицы корреляции между каналами
        
        Returns:
            Матрица корреляции (каналы x каналы)
        """
        return np.corrcoef(self.data)

