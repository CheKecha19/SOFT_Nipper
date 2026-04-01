import os
import glob
import logging
import re
import time

def find_latest_folder(network_dir):
    """Поиск последней созданной папки в сетевой директории"""
    try:
        logging.info(f"{'Поиск самой свежей папки:':<50} начат")
        folders = [f for f in os.listdir(network_dir) 
                  if os.path.isdir(os.path.join(network_dir, f))]
        
        if not folders:
            logging.error(f"{'Папки не найдены:':<50} {network_dir}")
            return None
        
        # Получаем папки с информацией о времени создания
        folders_with_time = []
        for f in folders:
            folder_path = os.path.join(network_dir, f)
            folders_with_time.append((f, os.path.getctime(folder_path)))
        
        # Сортировка по времени создания (новые в конце)
        folders_with_time.sort(key=lambda x: x[1])
        latest_folder = os.path.join(network_dir, folders_with_time[-1][0])
        
        logging.info(f"{'Последняя папка найдена:':<50} {latest_folder}")
        return latest_folder
    except Exception as e:
        logging.exception(f"{'Ошибка поиска папки:':<50} {str(e)}")
        return None

def get_recent_files(network_dir, max_file_age_days):
    """Поиск свежих .cfg файлов (за последние max_file_age_days дней)"""
    try:
        logging.info(f"{'Поиск .cfg файлов за:':<50} последние {max_file_age_days} дней")
        all_files = glob.glob(os.path.join(network_dir, '*.cfg'))
        
        if not all_files:
            logging.warning(f"{'Файлы не найдены:':<50} {network_dir}")
            return []
        
        cutoff_time = time.time() - (max_file_age_days * 24 * 3600)
        recent_files = [
            f for f in all_files
            if os.path.getmtime(f) > cutoff_time
        ]
        
        logging.info(f"{'Найдено .cfg файлов:':<50} {len(recent_files)}")
        return recent_files
    except Exception as e:
        logging.exception(f"{'Ошибка поиска файлов:':<50} {str(e)}")
        return []

def get_config_files(source, configs_dir):
    """Получение списка .cfg файлов из указанного источника"""
    try:
        os.makedirs(configs_dir, exist_ok=True)
        
        if isinstance(source, list):  # Режим recent_files или both
            cfg_files = source
            logging.info(f"{'Источник (файлы):':<50} {len(cfg_files)} файлов")
        else:  # Режим latest_folder
            cfg_files = glob.glob(os.path.join(source, '*.cfg'))
            logging.info(f"{'Источник (папка):':<50} {source}")
        
        return cfg_files
    except Exception as e:
        logging.exception(f"{'Ошибка получения файлов:':<50} {str(e)}")
        return []

def rename_configs(configs_dir):
    """Переименование файлов: извлечение IP и перезапись дубликатов"""
    try:
        # Получаем файлы с информацией о времени создания
        files_with_time = []
        for f in os.listdir(configs_dir):
            if f.lower().endswith('.cfg'):
                file_path = os.path.join(configs_dir, f)
                files_with_time.append((f, os.path.getctime(file_path)))
        
        if not files_with_time:
            logging.warning(f"{'Файлы для переименования:':<50} не найдены")
            return False
            
        # Сортируем по времени создания (старые -> новые)
        files_with_time.sort(key=lambda x: x[1])
        
        ip_pattern = re.compile(r'^\d{1,3}(\.\d{1,3}){3}')  # Регулярка для поиска IP
        
        renamed_count = 0
        for filename, _ in files_with_time:
            file_path = os.path.join(configs_dir, filename)
            
            # Извлечение части с IP
            ip_match = ip_pattern.match(filename)
            new_name = ip_match.group(0) + '.txt' if ip_match else os.path.splitext(filename)[0] + '.txt'
            new_path = os.path.join(configs_dir, new_name)
            
            # Удаляем существующий файл перед переименованием
            if os.path.exists(new_path):
                os.remove(new_path)
                logging.debug(f"{'Перезапись файла:':<50} {new_name}")
            
            # Переименовываем файл
            os.rename(file_path, new_path)
            renamed_count += 1
            
        logging.info(f"{'Переименовано файлов:':<50} {renamed_count}")
        return True
    except Exception as e:
        logging.exception(f"{'Ошибка переименования:':<50} {str(e)}")
        return False