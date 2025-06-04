

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
        LOG_DATE_FORMAT
    )
except ImportError:
    logging.error("Ошибка импорта конфигурации! Убедитесь в наличии файла config.py")
    exit(1)

class ProgressBar:
    """Класс для отображения прогресс-бара в консоли"""
    def __init__(self, total, description="Processing", width=50):
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
            print(f"\n{self.description} completed in {elapsed:.1f} seconds")

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
    logging.info(f"Network source: {NETWORK_DIR}")
    logging.info(f"Configs target: {CONFIGS_DIR}")
    logging.info(f"Reports target: {REPORTS_DIR}")

def find_latest_folder():
    """Поиск последней созданной папки в сетевой директории"""
    logging.info("Searching for latest folder...")
    try:
        folders = [f for f in os.listdir(NETWORK_DIR) 
                  if os.path.isdir(os.path.join(NETWORK_DIR, f))]
        
        if not folders:
            logging.error("No folders found in network directory")
            return None
        
        # Сортировка по времени создания
        folders.sort(key=lambda f: os.path.getctime(os.path.join(NETWORK_DIR, f)), reverse=True)
        latest_folder = os.path.join(NETWORK_DIR, folders[0])
        logging.info(f"Latest folder found: {latest_folder}")
        return latest_folder
    except Exception as e:
        logging.exception(f"Error finding latest folder: {str(e)}")
        return None

def copy_configs(source_dir):
    """Копирование .cfg файлов в локальную директорию"""
    try:
        os.makedirs(CONFIGS_DIR, exist_ok=True)
        cfg_files = glob.glob(os.path.join(source_dir, '*.cfg'))
        
        if not cfg_files:
            logging.warning("No .cfg files found in source directory")
            return False
        
        total = len(cfg_files)
        logging.info(f"Copying {total} config files...")
        progress = ProgressBar(total, "Copying configs")
        
        for file_path in cfg_files:
            shutil.copy2(file_path, CONFIGS_DIR)
            progress.update(1)
            time.sleep(0.01)  # Для визуализации прогресса
            
        logging.info(f"Successfully copied {total} files")
        return True
    except Exception as e:
        logging.exception(f"Error copying files: {str(e)}")
        return False

def process_with_nipper():
    """Обработка файлов утилитой nipper"""
    try:
        files = [f for f in os.listdir(CONFIGS_DIR) if f.lower().endswith('.txt')]
        
        if not files:
            logging.warning("No .txt files found for processing")
            return False
            
        total = len(files)
        logging.info(f"Processing {total} files with nipper...")
        progress = ProgressBar(total, "Running nipper")
        
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
                logging.error(f"Nipper error for {filename}: {str(e)}")
                progress.update(1)
                
        logging.info(f"Successfully processed {total} files")
        return True
    except Exception as e:
        logging.exception(f"Error processing files: {str(e)}")
        return False

def rename_configs():
    """Переименование файлов: извлечение IP и перезапись дубликатов"""
    try:
        # Сортируем файлы для обработки в алфавитном порядке
        files = sorted([f for f in os.listdir(CONFIGS_DIR) if f.lower().endswith('.cfg')])
        if not files:
            logging.warning("No .cfg files found for renaming")
            return False
            
        total = len(files)
        logging.info(f"Renaming {total} files...")
        progress = ProgressBar(total, "Renaming files")
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
                logging.debug(f"Overwritten existing file: {new_name}")
            
            # Переименовываем файл
            os.rename(file_path, new_path)
            progress.update(1)
            time.sleep(0.01)
            
        logging.info(f"Successfully renamed {total} files")
        return True
    except Exception as e:
        logging.exception(f"Error renaming files: {str(e)}")
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
                overall = cols[2].get_text(strip=True)
                impact = cols[3].get_text(strip=True)
                ease = cols[4].get_text(strip=True)
                fix = cols[5].get_text(strip=True)
                recommendation = cols[6].get_text(strip=True)

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

def main():
    """Основная функция выполнения скрипта"""
    setup_logging()
    
    try:
        # Шаг 1: Поиск и копирование конфигураций
        latest_folder = find_latest_folder()
        if not latest_folder:
            return
            
        if not copy_configs(latest_folder):
            return
            
        # Шаг 2: Переименование файлов
        if not rename_configs():
            return
            
        # Шаг 3: Обработка nipper
        process_with_nipper()
        
        # Шаг 4: Генерация финального отчёта (ИСПРАВЛЕНО ИМЯ)
        generate_final_report()
        
        logging.info("=== Operation completed successfully ===")
    except Exception as e:
        logging.exception("Critical error in main execution")
    finally:
        logging.info("=== Script execution finished ===")

if __name__ == "__main__":
    main()
