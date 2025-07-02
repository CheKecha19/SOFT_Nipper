import os
import shutil
import glob
import logging
import subprocess
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# Импорт конфигурации
try:
    from config import (
        NETWORK_DIR,
        CONFIGS_DIR,
        REPORTS_DIR,
        LOG_DIR,
        FINAL_RESULTS_DIR,
        NIPPER_EXE,
        SCANNED_DEVICE,
        LOG_LEVEL,
        LOG_FORMAT,
        LOG_DATE_FORMAT,
        CLEANUP_AFTER_SUCCESS,
        MAX_FILE_AGE_DAYS,
        FILE_SOURCE_MODE
    )
except ImportError:
    logging.error("Ошибка импорта конфигурации! Убедитесь в наличии файла config.py")
    exit(1)

class ProgressBar:
    """Класс для отображения прогресс-бара в консоли"""
    def __init__(self, total, description="Прогресс", width=50):
        self.total = total
        self.description = description
        self.width = width
        self.start_time = time.time()
        self.completed = 0
        
    def update(self, n=1):
        """Обновить прогресс"""
        self.completed += n
        elapsed = time.time() - self.start_time
        percent = self.completed / self.total
        bar_length = int(self.width * percent)
        bar = '█' * bar_length + '-' * (self.width - bar_length)
        
        # Расчет оставшегося времени
        if percent > 0:
            eta = elapsed * (1 - percent) / percent
            eta_str = f"ETA: {eta:.1f}s"
        else:
            eta_str = "ETA: ?"
        
        # Форматирование вывода
        print(f"\r{self.description}: [{bar}] {percent:.0%} ({self.completed}/{self.total}) {eta_str}", end='')
        
        if self.completed == self.total:
            print(f"\n{self.description} выполнено за {elapsed:.1f} секунд")

def setup_logging():
    """Настройка системы логирования с учетом конфига"""
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    log_file = os.path.join(LOG_DIR, f"nipper_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    logging.basicConfig(
        filename=log_file,
        level=log_level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT
    )
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.info("=== Logging started ===")
    logging.info(f"Источник .cfg файлов:             {NETWORK_DIR}")
    logging.info(f"Временная папка для конфигураций: {CONFIGS_DIR}")
    logging.info(f"Временная папка для отчётов:      {REPORTS_DIR}")

def find_latest_folder():
    """Поиск последней созданной папки в сетевой директории"""
    logging.info("Поиск самой свежей папки...")
    try:
        folders = [f for f in os.listdir(NETWORK_DIR) 
                  if os.path.isdir(os.path.join(NETWORK_DIR, f))]
        
        if not folders:
            logging.error("Папка с конфигурациями в  {NETWORK_DIR} не найдена")
            return None
        
        # Сортировка по времени создания
        folders.sort(key=lambda f: os.path.getctime(os.path.join(NETWORK_DIR, f)), reverse=True)
        latest_folder = os.path.join(NETWORK_DIR, folders[0])
        logging.info(f"Последняя папка найдена:          {latest_folder}")
        return latest_folder
    except Exception as e:
        logging.exception(f"Ошибка при поиске последней папки: {str(e)}")
        return None

def get_recent_files():
    """Поиск свежих .cfg файлов (за последние MAX_FILE_AGE_DAYS дней)"""
    try:
        logging.info(f"Searching for .cfg files modified in last {MAX_FILE_AGE_DAYS} days...")
        all_files = glob.glob(os.path.join(NETWORK_DIR, '*.cfg'))
        
        if not all_files:
            logging.warning("No .cfg files found in network directory")
            return []
        
        cutoff_time = time.time() - (MAX_FILE_AGE_DAYS * 24 * 3600)
        recent_files = [
            f for f in all_files
            if os.path.getmtime(f) > cutoff_time
        ]
        
        logging.info(f"Found {len(recent_files)} recent .cfg files")
        return recent_files
    except Exception as e:
        logging.exception(f"Error finding recent files: {str(e)}")
        return []

def copy_configs(source):
    """Копирование .cfg файлов из указанного источника"""
    try:
        os.makedirs(CONFIGS_DIR, exist_ok=True)
        
        # Определяем тип источника
        if isinstance(source, list):  # Режим recent_files или both
            cfg_files = source
            logging.info(f"Источник: список из {len(cfg_files)} файлов")
        else:  # Режим latest_folder
            cfg_files = glob.glob(os.path.join(source, '*.cfg'))
            logging.info(f"Источник: папка {source}")
        
        if not cfg_files:
            logging.warning("Не найдено .cfg файлов для копирования")
            return False
            
        total = len(cfg_files)
        logging.info(f"Копирование {total} конфигурационных файлов...")
        progress = ProgressBar(total, "Копирование файлов")
        
        for file_path in cfg_files:
            # Для режима recent_files file_path - полный путь
            # Для режима latest_folder - относительный путь в папке
            shutil.copy2(file_path, CONFIGS_DIR)
            progress.update(1)
            time.sleep(0.01)
            
        logging.info(f"Успешно копировано {total} файлов")
        return True
    except Exception as e:
        logging.exception(f"Ошибка копирования файлов: {str(e)}")
        return False

def process_with_nipper():
    """Обработка файлов утилитой nipper"""
    try:
        files = [f for f in os.listdir(CONFIGS_DIR) if f.lower().endswith('.txt')]
        
        if not files:
            logging.warning(".txt файлы не были найдены")
            return False
            
        total = len(files)
        logging.info(f"Обработка {total} файлов nipper'ом...")
        progress = ProgressBar(total, "Обработка файлов")
        
        for filename in files:
            input_path = os.path.join(CONFIGS_DIR, filename)
            report_name = os.path.splitext(filename)[0] + '_report.html'
            output_path = os.path.join(REPORTS_DIR, report_name)
            
            # ИСПРАВЛЕННАЯ КОМАНДА
            command = [
                NIPPER_EXE,
                f'--input={input_path}',
                f'--output={output_path}',
                SCANNED_DEVICE  # Без фигурных скобок!
            ]
            
            try:
                subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                progress.update(1)
                time.sleep(0.05)
            except subprocess.CalledProcessError as e:
                logging.error(f"Nipper не отработал по {filename}: {str(e)}")
                progress.update(1)
                
        logging.info(f"Успешно обработано {total} файлов")
        return True
    except Exception as e:
        logging.exception(f"Ошибка обработки файла: {str(e)}")
        return False

def rename_configs():
    """Переименование файлов: извлечение IP и перезапись дубликатов"""
    try:
        # Сортируем файлы для обработки в алфавитном порядке
        files = sorted([f for f in os.listdir(CONFIGS_DIR) if f.lower().endswith('.cfg')])
        if not files:
            logging.warning(".cfg файл не найден для переименования")
            return False
            
        total = len(files)
        logging.info(f"Переименование {total} файлов...")
        progress = ProgressBar(total, "Переименование")
        ip_pattern = re.compile(r'^\d{1,3}(\.\d{1,3}){3}')  # Регулярка для поиска IP
        
        for filename in files:
            file_path = os.path.join(CONFIGS_DIR, filename)
            
            # Извлечение части с IP
            ip_match = ip_pattern.match(filename)
            new_name = ip_match.group(0) + '.txt' if ip_match else os.path.splitext(filename)[0] + '.txt'
            
            new_path = os.path.join(CONFIGS_DIR, new_name)
            
            # Удаляем существующий файл перед переименованием
            if os.path.exists(new_path):
                os.remove(new_path)
                logging.debug(f"Перезаписываем файл: {new_name}")
            
            # Переименовываем файл
            os.rename(file_path, new_path)
            progress.update(1)
            time.sleep(0.01)
            
        logging.info(f"Успешно перезаписано {total} файлов")
        return True
    except Exception as e:
        logging.exception(f"Ошибка перезаписи файла: {str(e)}")
        return False

def extract_recommendations_from_html(html_path):
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        recommendations = []

        recommendations_header = soup.find(lambda tag: tag.name.startswith('h') and 
                                           'Recommendations' in tag.text and
                                           tag.find_previous('h2') and 'Security Audit' in tag.find_previous('h2').text)

        if not recommendations_header:
            return []

        table = recommendations_header.find_next('table')
        if not table:
            return []

        rows = table.find_all('tr')[1:]

        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 7:
                issue = cols[0].get_text(strip=True)
                overall = cols[1].get_text(strip=True)
                impact = cols[2].get_text(strip=True)
                ease = cols[3].get_text(strip=True)
                fix = cols[4].get_text(strip=True)
                recommendation = cols[5].get_text(strip=True)

                recommendations.append({
                    'Issue': issue,
                    'Overall': overall,
                    'Impact': impact,
                    'Ease': ease,
                    'Fix': fix,
                    'Recommendation': recommendation
                })

        return recommendations

    except Exception as e:
        print(f"Error: {html_path} — {e}")
        return []

def generate_final_report():
    os.makedirs(FINAL_RESULTS_DIR, exist_ok=True)
    report_files = glob.glob(os.path.join(REPORTS_DIR, '*.html'))

    host_issues = {}
    issue_meta = {}

    for report_file in report_files:
        ip_address = os.path.basename(report_file).split('_')[0]
        recommendations = extract_recommendations_from_html(report_file)

        for rec in recommendations:
            issue = rec['Issue']
            if issue not in host_issues:
                host_issues[issue] = {}
            host_issues[issue][ip_address] = 1
            if issue not in issue_meta:
                issue_meta[issue] = {
                    'Overall': rec['Overall'],
                    'Impact': rec['Impact'],
                    'Ease': rec['Ease'],
                    'Fix': rec['Fix'],
                    'Recommendation': rec['Recommendation']
                }

    if not host_issues:
        print("Нет данных для отчёта.")
        return

    all_hosts = sorted({host for hosts in host_issues.values() for host in hosts})
    rows = []

    for issue, hosts in host_issues.items():
        row = {
            'Issue': issue,
            **{host: 1 if host in hosts else 0 for host in all_hosts},
            **issue_meta[issue]
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.fillna(0, inplace=True)

    ordered_columns = ['Issue'] + all_hosts + ['Overall', 'Impact', 'Ease', 'Fix', 'Recommendation']
    df = df[ordered_columns]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(FINAL_RESULTS_DIR, f'scan_summary_{timestamp}.xlsx')
    df.to_excel(output_path, index=False)
    print(f"Файл сохранён: {output_path}")

def cleanup_directories():
    """Удаление временных папок после генерации отчёта"""
    try:
        # Удаление папки configs
        if os.path.exists(CONFIGS_DIR):
            shutil.rmtree(CONFIGS_DIR)
            logging.info(f"Удалена папка configs: {CONFIGS_DIR}")
        
        # Удаление папки reports
        if os.path.exists(REPORTS_DIR):
            shutil.rmtree(REPORTS_DIR)
            logging.info(f"Удалена папка reports: {REPORTS_DIR}")
            
        return True
    except Exception as e:
        logging.exception(f"Ошибка при удалении временных папок: {str(e)}")
        return False

def main():
    setup_logging()
    
    try:
        # Шаг 1: Выбор источника конфигураций
        if FILE_SOURCE_MODE == 'latest_folder':
            logging.info("Режим: 'последняя папка'")
            source = find_latest_folder()
            if not source:
                return
                
        elif FILE_SOURCE_MODE == 'recent_files':
            logging.info("Режим: 'последние файлы'")
            source = get_recent_files()
            if not source:
                logging.error("Не найдено свежих файлов")
                return
                
        elif FILE_SOURCE_MODE == 'both':
            logging.info("Режим: 'комбинированный'")
            
            # Получаем последнюю папку
            folder = find_latest_folder()
            folder_files = glob.glob(os.path.join(folder, '*.cfg')) if folder else []
            
            # Получаем свежие файлы
            recent_files = get_recent_files()
            
            # Объединяем, убирая дубликаты
            source = list(set(folder_files + recent_files))
            
            if not source:
                logging.error("Не найдено файлов ни в последней папке, ни среди свежих файлов")
                return
                
        else:
            logging.error(f"Недопустимый режим FILE_SOURCE_MODE: {FILE_SOURCE_MODE}")
            return
            
        # Шаг 2: Копирование конфигураций
        if not copy_configs(source):
            return
            
        # Шаг 3: Переименование файлов
        if not rename_configs():
            return
            
        # Шаг 4: Обработка nipper
        process_with_nipper()
        
        # Шаг 5: Генерация финального отчёта
        generate_final_report()
        
        # Шаг 6: Очистка временных данных
        if CLEANUP_AFTER_SUCCESS:
            cleanup_directories()
        
        logging.info("=== Операция успешно завершена ===")
    except Exception as e:
        logging.exception("Критическая ошибка выполнения")
    finally:
        logging.info("=== Выполнение скрипта завершено ===")

if __name__ == "__main__":
    main()
