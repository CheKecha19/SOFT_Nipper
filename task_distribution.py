import os
import pandas as pd
import logging
import shutil
import re
from bs4 import BeautifulSoup
from utils import ProgressBar


def extract_vulnerability_description(html_path, issue_name):
    """Извлечение подробного описания уязвимости из HTML отчета"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        # Ищем все h3 теги (заголовки уязвимостей)
        h3_tags = soup.find_all('h3')
        
        for h3 in h3_tags:
            # Проверяем, содержит ли заголовок название уязвимости
            if issue_name in h3.get_text():
                # Находим родительский div (блок уязвимости)
                vulnerability_div = h3.find_parent('div')
                if vulnerability_div:
                    # Извлекаем весь текст блока уязвимости
                    text_elements = []
                    
                    # Добавляем заголовок
                    text_elements.append(h3.get_text(strip=True))
                    
                    # Ищем блок с рейтингами
                    ratings_div = vulnerability_div.find('div', class_='ratings')
                    if ratings_div:
                        text_elements.append(ratings_div.get_text(strip=True))
                    
                    # Ищем все подразделы (Finding, Impact, Ease, Recommendation)
                    sections = vulnerability_div.find_all(['h5', 'p', 'pre'])
                    
                    current_section = None
                    for element in sections:
                        if element.name == 'h5':
                            current_section = element.get_text(strip=True)
                            text_elements.append(f"\n{current_section}")
                        elif element.name == 'p':
                            text = element.get_text(strip=True)
                            if text:
                                if current_section and current_section in text:
                                    text_elements.append(text)
                                else:
                                    text_elements.append(f"  {text}")
                        elif element.name == 'pre':
                            text = element.get_text()
                            if text:
                                text_elements.append(f"\n  Команда:\n{text}")
                    
                    # Объединяем все элементы
                    full_text = '\n'.join(text_elements)
                    
                    # Очищаем текст от лишних пробелов и переносов
                    full_text = re.sub(r'\n\s*\n', '\n\n', full_text)
                    full_text = re.sub(r'[ \t]+', ' ', full_text)
                    
                    logging.debug(f"Извлечено описание уязвимости: {issue_name}")
                    return full_text
        
        # Если уязвимость не найдена, попробуем найти по частичному совпадению
        for h3 in h3_tags:
            h3_text = h3.get_text(strip=True)
            # Удаляем номер из начала заголовка (например, "2.3. ")
            clean_h3_text = re.sub(r'^\d+\.\d+\.\s*', '', h3_text)
            if issue_name.lower() in clean_h3_text.lower():
                # Используем тот же алгоритм извлечения
                vulnerability_div = h3.find_parent('div')
                if vulnerability_div:
                    return vulnerability_div.get_text(separator='\n', strip=True)
        
        logging.warning(f"Уязвимость не найдена в отчете: {issue_name}")
        return None
        
    except Exception as e:
        logging.error(f"Ошибка извлечения описания из {html_path}: {str(e)}")
        return None


def get_vulnerability_html_file(reports_dir, ip_address):
    """Получение пути к HTML файлу для конкретного IP"""
    try:
        # Формируем путь к HTML файлу
        html_file = os.path.join(reports_dir, f"{ip_address}_report.html")
        
        if os.path.exists(html_file):
            return html_file
        
        # Пробуем найти файл с разными вариантами именования
        alternative_patterns = [
            f"{ip_address}_report.html",
            f"{ip_address.replace('.', '_')}_report.html",
            f"report_{ip_address}.html",
        ]
        
        for pattern in alternative_patterns:
            html_file = os.path.join(reports_dir, pattern)
            if os.path.exists(html_file):
                return html_file
        
        # Ищем любой HTML файл, содержащий IP в имени
        for file in os.listdir(reports_dir):
            if file.endswith('.html') and ip_address in file:
                return os.path.join(reports_dir, file)
        
        return None
        
    except Exception as e:
        logging.error(f"Ошибка поиска HTML файла для {ip_address}: {str(e)}")
        return None


def create_task_folders(final_report_path, task_distribution_dir, reports_dir):
    """Создание структуры папок для задач на основе финального отчета"""
    try:
        # Очистка папки "отправить в задачи"
        if os.path.exists(task_distribution_dir):
            shutil.rmtree(task_distribution_dir)
            logging.info(f"{'Очищена папка:':<50} {task_distribution_dir}")
        
        # Создание папки "отправить в задачи"
        os.makedirs(task_distribution_dir, exist_ok=True)
        logging.info(f"{'Создана папка:':<50} {task_distribution_dir}")
        
        # Чтение финального отчета
        if not os.path.exists(final_report_path):
            logging.error(f"{'Финальный отчет не найден:':<50} {final_report_path}")
            return False
        
        df = pd.read_excel(final_report_path)
        
        # Определяем мета-колонки
        meta_columns = ['Issue', 'Overall', 'Impact', 'Ease', 'Fix', 'Recommendation']
        
        # Находим колонки с IP-адресами
        ip_columns = [col for col in df.columns if col not in meta_columns]
        
        if not ip_columns:
            logging.warning(f"{'IP-адреса не найдены в отчете:':<50}")
            return False
        
        # Обработка каждой уязвимости
        logging.info(f"{'Создание структуры задач:':<50} начато")
        progress = ProgressBar(len(df), "Создание папок с задачами")
        
        for _, row in df.iterrows():
            issue = row['Issue']
            recommendation = row['Recommendation']
            
            # Очистка названия папки от недопустимых символов
            safe_issue = re.sub(r'[<>:"/\\|?*]', '_', str(issue))
            
            # Создание папки для уязвимости
            issue_folder = os.path.join(task_distribution_dir, safe_issue)
            os.makedirs(issue_folder, exist_ok=True)
            
            # Поиск IP-адресов с данной уязвимостью
            vulnerable_ips = []
            for ip in ip_columns:
                if pd.notna(row[ip]) and row[ip] == 1:
                    vulnerable_ips.append(ip)
            
            # Создание Excel файла в папке
            if vulnerable_ips:
                task_df = pd.DataFrame({
                    'IP Address': vulnerable_ips,
                    'Issue': [issue] * len(vulnerable_ips),
                    'Recommendation': [recommendation] * len(vulnerable_ips),
                    'Overall': [row['Overall']] * len(vulnerable_ips),
                    'Impact': [row['Impact']] * len(vulnerable_ips),
                    'Ease': [row['Ease']] * len(vulnerable_ips),
                    'Fix': [row['Fix']] * len(vulnerable_ips)
                })
                
                # Сохранение Excel файла
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', str(issue))
                output_excel = os.path.join(issue_folder, f"{safe_filename}.xlsx")
                task_df.to_excel(output_excel, index=False)
                logging.debug(f"{'Создан Excel файл:':<50} {output_excel}")
                
                # Создание файла с подробным описанием уязвимости
                # Используем первый IP для извлечения описания
                if vulnerable_ips and reports_dir:
                    first_ip = vulnerable_ips[0]
                    html_file = get_vulnerability_html_file(reports_dir, first_ip)
                    
                    if html_file and os.path.exists(html_file):
                        description = extract_vulnerability_description(html_file, issue)
                        if description:
                            description_file = os.path.join(issue_folder, "описание.txt")
                            with open(description_file, 'w', encoding='utf-8') as f:
                                f.write(description)
                            logging.debug(f"{'Создан файл с описанием:':<50} {description_file}")
                        else:
                            # Создаем минимальное описание, если не удалось извлечь из HTML
                            minimal_description = f"{issue}\n\nРекомендация: {recommendation}"
                            description_file = os.path.join(issue_folder, "описание.txt")
                            with open(description_file, 'w', encoding='utf-8') as f:
                                f.write(minimal_description)
                            logging.debug(f"{'Создано минимальное описание:':<50} {description_file}")
                    else:
                        # Создаем минимальное описание, если HTML файл не найден
                        minimal_description = f"{issue}\n\nРекомендация: {recommendation}"
                        description_file = os.path.join(issue_folder, "описание.txt")
                        with open(description_file, 'w', encoding='utf-8') as f:
                            f.write(minimal_description)
                        logging.debug(f"{'Создано минимальное описание:':<50} {description_file}")
            else:
                logging.warning(f"{'Нет IP с уязвимостью:':<50} {issue}")
            
            progress.update(1)
        
        # Подсчет созданных папок
        created_folders = [d for d in os.listdir(task_distribution_dir) 
                          if os.path.isdir(os.path.join(task_distribution_dir, d))]
        
        logging.info(f"{'Создано папок с задачами:':<50} {len(created_folders)}")
        return True
        
    except Exception as e:
        logging.exception(f"{'Ошибка создания структуры задач:':<50} {str(e)}")
        return False


def verify_task_structure(task_distribution_dir):
    """Проверка целостности созданной структуры задач"""
    try:
        if not os.path.exists(task_distribution_dir):
            logging.error(f"{'Папка не существует:':<50} {task_distribution_dir}")
            return False
        
        folders = [d for d in os.listdir(task_distribution_dir) 
                  if os.path.isdir(os.path.join(task_distribution_dir, d))]
        
        if not folders:
            logging.warning(f"{'Папки с задачами не созданы:':<50}")
            return False
        
        total_excel_files = 0
        total_description_files = 0
        
        for folder in folders:
            folder_path = os.path.join(task_distribution_dir, folder)
            
            # Проверка Excel файлов
            excel_files = [f for f in os.listdir(folder_path) if f.endswith('.xlsx')]
            total_excel_files += len(excel_files)
            
            # Проверка файлов с описанием
            description_files = [f for f in os.listdir(folder_path) if f == "описание.txt"]
            total_description_files += len(description_files)
            
            # Проверка содержимого Excel файлов
            for file in excel_files:
                file_path = os.path.join(folder_path, file)
                try:
                    df = pd.read_excel(file_path)
                    required_columns = ['IP Address', 'Issue', 'Recommendation', 'Overall', 'Impact', 'Ease', 'Fix']
                    for col in required_columns:
                        if col not in df.columns:
                            logging.error(f"{'Отсутствует колонка в файле:':<50} {col} в {file}")
                            return False
                except Exception as e:
                    logging.error(f"{'Ошибка чтения файла:':<50} {file}\n{str(e)}")
                    return False
            
            # Проверка файлов с описанием
            for file in description_files:
                file_path = os.path.join(folder_path, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if len(content.strip()) < 10:  # Минимальная длина описания
                        logging.warning(f"{'Слишком короткое описание в файле:':<50} {file}")
                except Exception as e:
                    logging.error(f"{'Ошибка чтения файла с описанием:':<50} {file}\n{str(e)}")
                    return False
        
        logging.info(f"{'Проверка структуры задач:':<50} успешно")
        logging.info(f"{'  Создано папок:':<50} {len(folders)}")
        logging.info(f"{'  Создано Excel файлов:':<50} {total_excel_files}")
        logging.info(f"{'  Создано файлов с описанием:':<50} {total_description_files}")
        return True
        
    except Exception as e:
        logging.error(f"{'Ошибка проверки структуры задач:':<50} {str(e)}")
        return False