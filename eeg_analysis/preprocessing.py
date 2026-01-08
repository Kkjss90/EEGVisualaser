"""
Модуль предобработки данных ЭЭГ
Включает фильтрацию и удаление артефактов
"""

import numpy as np
import mne
from scipy import signal
from scipy.signal import butter, filtfilt, iirnotch
from typing import Tuple, Optional, List
import warnings

warnings.filterwarnings('ignore')


class EEGPreprocessor:
    """Класс для предобработки данных ЭЭГ"""
    
    def __init__(self, data: np.ndarray, sampling_rate: float, channel_names: List[str]):
        """
        Инициализация препроцессора
        
        Args:
            data: Массив данных ЭЭГ (каналы x время)
            sampling_rate: Частота дискретизации
            channel_names: Список имен каналов
        """
        self.data = data.copy()
        self.sampling_rate = sampling_rate
        self.channel_names = channel_names
        self.processed_data = None
        
    def apply_bandpass_filter(self, low_freq: float = 1.0, high_freq: float = 40.0, 
                              order: int = 4) -> np.ndarray:
        """
        Применение полосового фильтра (ФНЧ + ФВЧ)
        
        Args:
            low_freq: Нижняя частота среза (Гц)
            high_freq: Верхняя частота среза (Гц)
            order: Порядок фильтра
            
        Returns:
            Отфильтрованные данные
        """
        nyquist = self.sampling_rate / 2.0
        
        # Проверка частот Найквиста
        if high_freq >= nyquist:
            high_freq = nyquist - 1
        
        # Создание полосового фильтра Баттерворта
        b, a = butter(order, [low_freq / nyquist, high_freq / nyquist], btype='band')
        
        # Применение фильтра к каждому каналу
        filtered_data = np.zeros_like(self.data)
        for i in range(self.data.shape[0]):
            filtered_data[i, :] = filtfilt(b, a, self.data[i, :])
        
        self.processed_data = filtered_data
        return filtered_data
    
    def apply_lowpass_filter(self, cutoff_freq: float = 40.0, order: int = 4) -> np.ndarray:
        """
        Применение ФНЧ (фильтр низких частот)
        
        Args:
            cutoff_freq: Частота среза (Гц)
            order: Порядок фильтра
            
        Returns:
            Отфильтрованные данные
        """
        nyquist = self.sampling_rate / 2.0
        
        if cutoff_freq >= nyquist:
            cutoff_freq = nyquist - 1
        
        b, a = butter(order, cutoff_freq / nyquist, btype='low')
        
        filtered_data = np.zeros_like(self.data)
        for i in range(self.data.shape[0]):
            filtered_data[i, :] = filtfilt(b, a, self.data[i, :])
        
        self.processed_data = filtered_data
        return filtered_data
    
    def apply_highpass_filter(self, cutoff_freq: float = 1.0, order: int = 4) -> np.ndarray:
        """
        Применение ФВЧ (фильтр высоких частот)
        
        Args:
            cutoff_freq: Частота среза (Гц)
            order: Порядок фильтра
            
        Returns:
            Отфильтрованные данные
        """
        nyquist = self.sampling_rate / 2.0
        
        b, a = butter(order, cutoff_freq / nyquist, btype='high')
        
        filtered_data = np.zeros_like(self.data)
        for i in range(self.data.shape[0]):
            filtered_data[i, :] = filtfilt(b, a, self.data[i, :])
        
        self.processed_data = filtered_data
        return filtered_data
    
    def apply_notch_filter(self, notch_freq: float = 50.0, quality: float = 30.0) -> np.ndarray:
        """
        Применение режекторного фильтра (для удаления сетевых помех 50/60 Гц)
        
        Args:
            notch_freq: Частота помехи (50 Гц для Европы, 60 Гц для США)
            quality: Добротность фильтра
            
        Returns:
            Отфильтрованные данные
        """
        nyquist = self.sampling_rate / 2.0
        
        if notch_freq >= nyquist:
            return self.data
        
        # Создание режекторного фильтра
        b, a = iirnotch(notch_freq, quality, self.sampling_rate)
        
        filtered_data = np.zeros_like(self.data)
        for i in range(self.data.shape[0]):
            filtered_data[i, :] = filtfilt(b, a, self.data[i, :])
        
        self.processed_data = filtered_data
        return filtered_data
    
    def remove_artifacts_by_threshold(self, threshold: float = 100.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Удаление артефактов по порогу амплитуды
        
        Args:
            threshold: Порог амплитуды (мкВ)
            
        Returns:
            Кортеж (очищенные данные, маска артефактов)
        """
        artifact_mask = np.abs(self.data) > threshold
        cleaned_data = self.data.copy()
        cleaned_data[artifact_mask] = 0
        
        self.processed_data = cleaned_data
        return cleaned_data, artifact_mask
    
    def detect_blink_artifacts(self, eog_channel: Optional[str] = None, 
                               threshold: float = 3.0) -> np.ndarray:
        """
        Детекция артефактов моргания
        
        Args:
            eog_channel: Имя канала ЭОГ (если есть)
            threshold: Порог стандартных отклонений
            
        Returns:
            Маска артефактов моргания
        """
        if eog_channel and eog_channel in self.channel_names:
            ch_idx = self.channel_names.index(eog_channel)
            channel_data = self.data[ch_idx, :]
        else:
            # Используем фронтальные каналы для детекции
            frontal_channels = [i for i, ch in enumerate(self.channel_names) 
                              if any(x in ch.lower() for x in ['fp', 'fz', 'f1', 'f2'])]
            if frontal_channels:
                channel_data = np.mean(self.data[frontal_channels, :], axis=0)
            else:
                channel_data = self.data[0, :]
        
        # Вычисление порога
        mean_val = np.mean(channel_data)
        std_val = np.std(channel_data)
        threshold_val = mean_val + threshold * std_val
        
        # Детекция превышений порога
        blink_mask = np.abs(channel_data) > threshold_val
        
        return blink_mask
    
    def remove_blink_artifacts(self, eog_channel: Optional[str] = None, 
                              threshold: float = 3.0, window_ms: int = 200) -> np.ndarray:
        """
        Удаление артефактов моргания
        
        Args:
            eog_channel: Имя канала ЭОГ
            threshold: Порог стандартных отклонений
            window_ms: Окно удаления в миллисекундах
            
        Returns:
            Очищенные данные
        """
        blink_mask = self.detect_blink_artifacts(eog_channel, threshold)
        
        # Расширение маски на окно вокруг детектированных артефактов
        window_samples = int(window_ms * self.sampling_rate / 1000)
        expanded_mask = np.zeros_like(blink_mask, dtype=bool)
        
        for i in range(len(blink_mask)):
            if blink_mask[i]:
                start = max(0, i - window_samples)
                end = min(len(blink_mask), i + window_samples)
                expanded_mask[start:end] = True
        
        # Интерполяция артефактов
        cleaned_data = self.data.copy()
        for ch_idx in range(self.data.shape[0]):
            channel_data = cleaned_data[ch_idx, :]
            if np.any(expanded_mask):
                # Линейная интерполяция
                valid_indices = np.where(~expanded_mask)[0]
                if len(valid_indices) > 0:
                    channel_data[expanded_mask] = np.interp(
                        np.where(expanded_mask)[0],
                        valid_indices,
                        channel_data[valid_indices]
                    )
            cleaned_data[ch_idx, :] = channel_data
        
        self.processed_data = cleaned_data
        return cleaned_data
    
    def apply_mne_preprocessing(self, raw: mne.io.Raw) -> mne.io.Raw:
        """
        Применение стандартных методов предобработки MNE
        
        Args:
            raw: Raw объект MNE
            
        Returns:
            Обработанный Raw объект
        """
        # Копируем данные
        raw_filtered = raw.copy()
        
        # Применяем фильтрацию
        raw_filtered.filter(l_freq=1.0, h_freq=40.0, verbose=False)
        
        # Удаление сетевых помех
        raw_filtered.notch_filter(freqs=50.0, verbose=False)
        
        return raw_filtered
    
    def get_processed_data(self) -> Optional[np.ndarray]:
        """Получить обработанные данные"""
        return self.processed_data if self.processed_data is not None else self.data

