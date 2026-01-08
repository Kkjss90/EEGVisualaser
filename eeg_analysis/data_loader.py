"""
Модуль для загрузки данных ЭЭГ из различных форматов
Поддерживает: .edf, .set/.fdt (EEGLAB), .csv
"""

import numpy as np
import pandas as pd
import mne
from pathlib import Path
from typing import Tuple, Optional, Dict, List
import warnings

warnings.filterwarnings('ignore')


class EEGDataLoader:
    """Класс для загрузки данных ЭЭГ из различных форматов"""
    
    def __init__(self):
        self.raw_data = None
        self.sampling_rate = None
        self.channel_names = None
        self.data = None
        self.info = None
        
    def load_edf(self, file_path: str) -> Dict:
        """
        Загрузка данных из формата EDF (European Data Format)
        
        Args:
            file_path: Путь к файлу .edf
            
        Returns:
            Словарь с данными: {'data': numpy array, 'sfreq': частота дискретизации, 
                               'ch_names': имена каналов, 'info': метаданные}
        """
        try:
            raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
            self.raw_data = raw
            self.data = raw.get_data()
            self.sampling_rate = raw.info['sfreq']
            self.channel_names = raw.ch_names
            self.info = raw.info
            
            return {
                'data': self.data,
                'sfreq': self.sampling_rate,
                'ch_names': self.channel_names,
                'info': self.info,
                'raw': raw
            }
        except Exception as e:
            raise ValueError(f"Ошибка при загрузке EDF файла: {str(e)}")
    
    def load_eeglab(self, file_path: str) -> Dict:
        """
        Загрузка данных из формата EEGLAB (.set файл)
        
        Args:
            file_path: Путь к файлу .set
            
        Returns:
            Словарь с данными
        """
        try:
            raw = mne.io.read_raw_eeglab(file_path, preload=True, verbose=False)
            self.raw_data = raw
            self.data = raw.get_data()
            self.sampling_rate = raw.info['sfreq']
            self.channel_names = raw.ch_names
            self.info = raw.info
            
            return {
                'data': self.data,
                'sfreq': self.sampling_rate,
                'ch_names': self.channel_names,
                'info': self.info,
                'raw': raw
            }
        except Exception as e:
            raise ValueError(f"Ошибка при загрузке EEGLAB файла: {str(e)}")
    
    def load_csv(self, file_path: str, sampling_rate: Optional[float] = None, 
                 channel_names: Optional[List[str]] = None,
                 delimiter: Optional[str] = None, 
                 has_header: bool = True) -> Dict:
        """
        Загрузка данных из CSV файла
        
        Args:
            file_path: Путь к CSV файлу
            sampling_rate: Частота дискретизации (по умолчанию 250 Гц)
            channel_names: Список имен каналов (если не указан, берутся из заголовков)
            delimiter: Разделитель (None для автоматического определения)
            
        Returns:
            Словарь с данными
        """
        try:
            import re
            file_path_obj = Path(file_path)
            file_name = file_path_obj.stem  # Имя файла без расширения
            
            # Извлекаем название канала из имени файла (например, math_A0 -> A0)
            extracted_channel = None
            if channel_names is None:
                # Пробуем найти паттерн канала в имени файла
                # Формат: название_канал (например, math_A0, reading_A1)
                if '_' in file_name:
                    parts = file_name.split('_')
                    extracted_channel = parts[-1]  # Берем последнюю часть
                else:
                    # Пробуем найти паттерн A0, A1, Ch1 и т.д.
                    match = re.search(r'([A-Za-z]+\d+)', file_name)
                    if match:
                        extracted_channel = match.group(1)
                    else:
                        extracted_channel = file_name
            
            # Автоматическое определение разделителя
            if delimiter is None:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    # Проверяем комбинацию точка с запятой + табуляция
                    if ';\t' in first_line:
                        delimiter = ';'
                    elif '; ' in first_line:
                        delimiter = ';'
                    elif '\t' in first_line:
                        delimiter = '\t'
                    elif ';' in first_line:
                        delimiter = ';'
                    elif ',' in first_line:
                        delimiter = ','
                    else:
                        delimiter = ','  # По умолчанию
            
            # Определяем, есть ли заголовки
            # Читаем первые несколько строк для анализа
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                second_line = f.readline().strip() if f.readline() else ""
            
            # Проверяем, содержит ли первая строка числа
            has_numbers_in_first = bool(re.search(r'\d', first_line))
            has_numbers_in_second = bool(re.search(r'\d', second_line)) if second_line else False
            
            # Если первая строка не содержит чисел, а вторая содержит - вероятно есть заголовок
            if not has_numbers_in_first and has_numbers_in_second:
                header = 0
                has_header = True
            else:
                header = None
                has_header = False
            
            # Читаем CSV с определенным разделителем
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1251']
            df = None
            for encoding in encodings:
                try:
                    if has_header:
                        df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding, 
                                       skipinitialspace=True, engine='python', header=header)
                    else:
                        # Нет заголовков - читаем как данные
                        df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding, 
                                       skipinitialspace=True, engine='python', header=None)
                    break
                except Exception as e:
                    continue
            
            if df is None or df.empty:
                raise ValueError("Не удалось прочитать файл. Проверьте формат и кодировку.")
            
            # Если нет заголовков, присваиваем имена колонкам
            if not has_header:
                if len(df.columns) >= 2:
                    df.columns = ['time', 'value'] + [f'col_{i}' for i in range(2, len(df.columns))]
                else:
                    df.columns = ['value'] if len(df.columns) == 1 else ['time', 'value']
            else:
                # Очистка данных: удаляем пробелы в названиях колонок
                df.columns = df.columns.str.strip()
            
            # Обрабатываем каждую колонку
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Удаляем пробелы
                    df[col] = df[col].astype(str).str.strip()
                    # Заменяем запятые на точки в числах
                    df[col] = df[col].str.replace(',', '.', regex=False)
                    
                    # Обработка случаев, когда в ячейке несколько значений
                    def extract_first_number(value):
                        if pd.isna(value) or value == '':
                            return value
                        # Разделяем по точке с запятой или табуляции
                        parts = str(value).replace('\t', ';').split(';')
                        # Берем первую часть и пытаемся преобразовать
                        first_part = parts[0].strip()
                        try:
                            return float(first_part)
                        except:
                            return value
                    
                    df[col] = df[col].apply(extract_first_number)
                    
                    # Удаляем оставшиеся лишние символы
                    df[col] = df[col].astype(str).str.replace(';', '', regex=False)
                    df[col] = df[col].astype(str).str.replace('\t', '', regex=False)
                    
                    # Пробуем преобразовать в число
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Удаляем строки, где все значения NaN
            df = df.dropna(how='all')
            
            # Определяем колонки времени и данных
            time_col = None
            data_cols = []
            
            # Ищем колонку времени
            for col in df.columns:
                col_lower = str(col).lower()
                if col_lower in ['time', 't', 'timestamp', 'ts', '0']:
                    time_col = col
                elif col_lower not in ['index', 'idx']:
                    data_cols.append(col)
            
            # Если не нашли колонку времени, но есть числовые колонки
            if time_col is None and len(df.columns) >= 2:
                # Первая колонка - время, остальные - данные
                time_col = df.columns[0]
                data_cols = df.columns[1:].tolist()
            elif time_col is None and len(df.columns) == 1:
                # Только одна колонка - это данные, времени нет
                data_cols = df.columns.tolist()
            
            if not data_cols:
                raise ValueError("Не найдены колонки с данными ЭЭГ")
            
            # Извлекаем данные
            if time_col and time_col in df.columns:
                time_data = df[time_col].values
                eeg_data = df[data_cols].values.T
                
                # Автоматическое определение частоты дискретизации из временных меток
                if sampling_rate is None and len(time_data) > 1:
                    # Вычисляем средний интервал между отсчетами
                    time_diffs = np.diff(time_data)
                    # Убираем выбросы (слишком большие или маленькие интервалы)
                    valid_diffs = time_diffs[(time_diffs > 0) & (time_diffs < np.percentile(time_diffs, 95)) if len(time_diffs) > 0 else time_diffs > 0]
                    if len(valid_diffs) > 0:
                        mean_interval = np.mean(valid_diffs)
                        # Определяем единицы измерения времени
                        # Если значения большие (>1000), вероятно это миллисекунды
                        if mean_interval > 1:
                            sampling_rate = 1000.0 / mean_interval  # мс -> Гц
                        else:
                            sampling_rate = 1.0 / mean_interval  # сек -> Гц
                    else:
                        sampling_rate = 250.0  # По умолчанию
                elif sampling_rate is None:
                    sampling_rate = 250.0  # По умолчанию
            else:
                # Нет колонки времени, используем индекс
                eeg_data = df[data_cols].values.T
                if sampling_rate is None:
                    sampling_rate = 250.0  # По умолчанию
            
            # Если каналы не определены, используем имена из файла или генерируем
            if channel_names is None:
                if len(data_cols) == 1:
                    # Один канал - используем имя из файла
                    channel_names = [extracted_channel if extracted_channel else file_name]
                else:
                    channel_names = [str(col) for col in data_cols]
            
            data = eeg_data
            
            # Проверяем, что данные числовые
            if not np.issubdtype(data.dtype, np.number):
                raise ValueError("Данные содержат нечисловые значения. Проверьте формат файла.")
            
            # Создаем объект Info для MNE
            n_channels = len(channel_names)
            if sampling_rate is None:
                sampling_rate = 250.0
            
            info = mne.create_info(
                ch_names=channel_names,
                sfreq=sampling_rate,
                ch_types=['eeg'] * n_channels
            )
            
            # Создаем Raw объект
            raw = mne.io.RawArray(data, info, verbose=False)
            
            self.raw_data = raw
            self.data = data
            self.sampling_rate = sampling_rate
            self.channel_names = channel_names
            self.info = info
            
            return {
                'data': self.data,
                'sfreq': self.sampling_rate,
                'ch_names': self.channel_names,
                'info': self.info,
                'raw': raw
            }
        except Exception as e:
            raise ValueError(f"Ошибка при загрузке CSV файла: {str(e)}")
    
    def load_data(self, file_path: str, **kwargs) -> Dict:
        """
        Универсальный метод загрузки данных (автоматически определяет формат)
        
        Args:
            file_path: Путь к файлу (или список путей для загрузки нескольких каналов)
            **kwargs: Дополнительные параметры (sampling_rate для CSV, etc.)
            
        Returns:
            Словарь с данными
        """
        # Если передан список файлов, загружаем несколько каналов
        if isinstance(file_path, (list, tuple)):
            return self.load_multiple_channels(file_path, **kwargs)
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        if suffix == '.edf':
            return self.load_edf(str(file_path))
        elif suffix == '.set':
            return self.load_eeglab(str(file_path))
        elif suffix == '.csv':
            # Для CSV файлов автоматически определяем, есть ли заголовки
            return self.load_csv(str(file_path), **kwargs)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {suffix}")
    
    def load_multiple_channels(self, file_paths: List[str], **kwargs) -> Dict:
        """
        Загрузка нескольких файлов как отдельных каналов
        
        Args:
            file_paths: Список путей к файлам
            **kwargs: Дополнительные параметры
            
        Returns:
            Словарь с объединенными данными, включая информацию о соответствии каналов и файлов
        """
        if not file_paths:
            raise ValueError("Список файлов пуст")
        
        all_data = []
        all_channel_names = []
        sampling_rate = None
        channel_file_mapping = []  # Список кортежей (channel_name, file_path, file_index, original_ch_name)
        
        for file_idx, file_path in enumerate(file_paths):
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                continue
            
            # Загружаем каждый файл
            if file_path_obj.suffix.lower() == '.csv':
                data_dict = self.load_csv(str(file_path), **kwargs)
            else:
                data_dict = self.load_data(str(file_path), **kwargs)
            
            # Сохраняем данные
            all_data.append(data_dict['data'])
            
            # Сохраняем соответствие каналов и файлов
            # Если канал с таким именем уже существует, добавляем суффикс с индексом файла
            for ch_idx, ch_name in enumerate(data_dict['ch_names']):
                original_ch_name = ch_name
                # Проверяем, есть ли уже канал с таким именем
                if ch_name in all_channel_names:
                    # Добавляем суффикс с индексом файла для уникальности
                    ch_name = f"{ch_name}_f{file_idx}"
                all_channel_names.append(ch_name)
                channel_file_mapping.append((ch_name, str(file_path), file_idx, original_ch_name))
            
            # Используем частоту дискретизации из первого файла
            if sampling_rate is None:
                sampling_rate = data_dict['sfreq']
        
        if not all_data:
            raise ValueError("Не удалось загрузить ни один файл")
        
        # Объединяем данные
        # Проверяем, что все файлы имеют одинаковое количество отсчетов
        n_samples = all_data[0].shape[1]
        for data in all_data[1:]:
            if data.shape[1] != n_samples:
                # Обрезаем до минимальной длины
                n_samples = min(n_samples, data.shape[1])
        
        # Обрезаем все данные до одинаковой длины
        combined_data = np.vstack([data[:, :n_samples] for data in all_data])
        
        # Создаем объект Info для MNE
        info = mne.create_info(
            ch_names=all_channel_names,
            sfreq=sampling_rate,
            ch_types=['eeg'] * len(all_channel_names)
        )
        
        # Создаем Raw объект
        raw = mne.io.RawArray(combined_data, info, verbose=False)
        
        self.raw_data = raw
        self.data = combined_data
        self.sampling_rate = sampling_rate
        self.channel_names = all_channel_names
        self.info = info
        
        return {
            'data': self.data,
            'sfreq': self.sampling_rate,
            'ch_names': self.channel_names,
            'info': self.info,
            'raw': raw,
            'channel_file_mapping': channel_file_mapping  # Добавляем информацию о соответствии
        }
    
    def get_data_summary(self) -> Dict:
        """
        Получить краткую информацию о загруженных данных
        
        Returns:
            Словарь с информацией о данных
        """
        if self.data is None:
            return {"error": "Данные не загружены"}
        
        return {
            "Количество каналов": len(self.channel_names),
            "Частота дискретизации": f"{self.sampling_rate} Гц",
            "Длительность записи": f"{self.data.shape[1] / self.sampling_rate:.2f} сек",
            "Количество точек": self.data.shape[1],
            "Каналы": self.channel_names
        }

