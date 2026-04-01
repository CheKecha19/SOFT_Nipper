import os
import subprocess
import logging
from bs4 import BeautifulSoup
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed


def process_single_file(args):
    """Обработка одного файла утилитой nipper с выводом полного лога при ошибках"""
    filename, configs_dir, reports_dir, nipper_exe, scanned_device = args
    try:
        input_path = os.path.join(configs_dir, filename)
        report_name = os.path.splitext(filename)[0] + '_report.html'
        output_path = os.path.join(reports_dir, report_name)

        command = [
            nipper_exe,
            f'--input={input_path}',
            f'--output={output_path}',
            scanned_device
        ]

        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        logging.debug(f"{'Успешно обработан:':<50} {filename}")
        if result.stdout.strip():
            logging.debug(f"stdout:\n{result.stdout}")
        if result.stderr.strip():
            logging.debug(f"stderr:\n{result.stderr}")

        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Nipper ошибка при обработке файла {filename}:\n"
                      f"stdout:\n{e.stdout}\nstderr:\n{e.stderr}\nОшибка: {str(e)}")

        # Вывод в консоль для удобства немедленной диагностики
        print(f"\n----- Ошибка nipper.exe для файла {filename} -----")
        if e.stdout:
            print("stdout:")
            print(e.stdout)
        if e.stderr:
            print("stderr:")
            print(e.stderr)
        print("--------------------------------------------------\n")

        return False
    except Exception as e:
        logging.error(f"Ошибка обработки файла {filename}: {str(e)}")
        print(f"Ошибка обработки файла {filename}: {str(e)}")
        return False


def process_with_nipper(configs_dir, reports_dir, nipper_exe, scanned_device, max_workers=4):
    """Обработка файлов утилитой nipper с использованием пула потоков"""
    try:
        files = [f for f in os.listdir(configs_dir) if f.lower().endswith('.txt')]

        if not files:
            logging.warning(f"{'Файлы для обработки:':<50} не найдены")
            return False

        logging.info(f"{'Обработка файлов:':<50} {len(files)} файлов в {max_workers} потоках")

        task_args = [
            (f, configs_dir, reports_dir, nipper_exe, scanned_device)
            for f in files
        ]

        success_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_single_file, args) for args in task_args]
            for future in as_completed(futures):
                if future.result():
                    success_count += 1

        logging.info(f"{'Успешно обработано:':<50} {success_count}/{len(files)} файлов")
        return success_count > 0
    except Exception as e:
        logging.exception(f"{'Ошибка обработки:':<50} {str(e)}")
        return False


@lru_cache(maxsize=100)
def parse_html(html_path):
    """Кэшированный парсинг HTML с BeautifulSoup"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            return BeautifulSoup(f, 'html.parser')
    except Exception as e:
        logging.error(f"{'Ошибка чтения HTML:':<50} {html_path}\n{str(e)}")
        return None


def extract_recommendations_from_html(html_path):
    """Извлечение рекомендаций из HTML-отчета"""
    try:
        soup = parse_html(html_path)
        if not soup:
            return []

        recommendations = []
        for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if 'Recommendations' in header.text:
                table = header.find_next('table')
                if table:
                    for row in table.find_all('tr')[1:]:
                        cols = row.find_all('td')
                        if len(cols) >= 6:
                            recommendations.append({
                                'Issue':          cols[0].get_text(strip=True),
                                'Overall':        cols[1].get_text(strip=True),
                                'Impact':         cols[2].get_text(strip=True),
                                'Ease':           cols[3].get_text(strip=True),
                                'Fix':            cols[4].get_text(strip=True),
                                'Recommendation': cols[5].get_text(strip=True),
                            })
                break

        logging.debug(f"{'Извлечено рекомендаций:':<50} {len(recommendations)} из {html_path}")
        return recommendations
    except Exception as e:
        logging.error(f"{'Ошибка обработки HTML:':<50} {html_path}\n{str(e)}")
        return []
