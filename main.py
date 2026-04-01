import os
import glob
import time
import logging
import shutil
import argparse

from config import *
from file_operations import find_latest_folder, get_recent_files, get_config_files, rename_configs
from nipper_processing import process_with_nipper
from reporting import generate_final_report, compare_reports, get_latest_report, verify_report
from task_distribution import create_task_folders, verify_task_structure  # НОВЫЙ ИМПОРТ
from utils import ProgressBar, setup_logging, cleanup_directories


def main():
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description='Nipper Report Generator')
    parser.add_argument('--force', action='store_true', help='Продолжать выполнение при ошибках')
    args = parser.parse_args()

    # Настройка логирования
    setup_logging(LOG_DIR, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT, LOG_MAX_SIZE, LOG_BACKUP_COUNT)

    # Стартовая информация
    logging.info("="*80)
    logging.info(f"{'ЗАПУСК СКРИПТА':^80}")
    logging.info("="*80)
    logging.info(f"{'Профиль сканирования:':<50} {SCANNED_DEVICE}")
    logging.info(f"{'Источник .cfg файлов:':<50} {NETWORK_DIR}")
    logging.info(f"{'Папка конфигураций:':<50} {CONFIGS_DIR}")
    logging.info(f"{'Папка отчетов:':<50} {REPORTS_DIR}")
    logging.info(f"{'Папка финальных отчетов:':<50} {FINAL_RESULTS_DIR}")
    logging.info(f"{'Папка отчетов сравнения:':<50} {COMPARISON_DIR}")
    logging.info(f"{'Папка задач:':<50} {TASK_DISTRIBUTION_DIR}")  # НОВАЯ СТРОКА
    logging.info(f"{'Режим работы:':<50} {FILE_SOURCE_MODE}")
    logging.info(f"{'Макс. потоков:':<50} {MAX_WORKERS}")
    logging.info(f"{'Создание структуры задач:':<50} {'включено' if CREATE_TASK_STRUCTURE else 'выключено'}")  # НОВАЯ СТРОКА
    logging.info(f"{'Сравнение отчетов:':<50} {'включено' if COMPARE_WITH_PREVIOUS else 'выключено'}")
    logging.info(f"{'Очистка временных файлов:':<50} {'включена' if CLEANUP_AFTER_SUCCESS else 'выключена'}")
    logging.info("-"*80)

    # Замер времени выполнения
    start_time = time.time()
    start_step = time.time()

    try:
        # ========================================================================
        # Шаг 1: Выбор источника конфигураций
        # ========================================================================
        logging.info(f"{'Выбор источника:':<50} начат")
        source = None

        if FILE_SOURCE_MODE == 'latest_folder':
            logging.info(f"{'Режим:':<50} последняя папка")
            source = find_latest_folder(NETWORK_DIR)
            if not source and not args.force:
                return

        elif FILE_SOURCE_MODE == 'recent_files':
            logging.info(f"{'Режим:':<50} последние файлы")
            source = get_recent_files(NETWORK_DIR, MAX_FILE_AGE_DAYS)
            if not source and not args.force:
                return

        elif FILE_SOURCE_MODE == 'both':
            logging.info(f"{'Режим:':<50} комбинированный")
            folder = find_latest_folder(NETWORK_DIR)
            folder_files = glob.glob(os.path.join(folder, '*.cfg')) if folder else []
            recent_files = get_recent_files(NETWORK_DIR, MAX_FILE_AGE_DAYS)
            source = list(set(folder_files + recent_files))
            if not source and not args.force:
                return

        else:
            logging.error(f"{'Ошибка режима:':<50} {FILE_SOURCE_MODE}")
            return

        step_time = time.time() - start_step
        logging.info(f"{'Выбор источника завершен:':<50} {step_time:.2f} сек")
        start_step = time.time()

        # ========================================================================
        # Шаг 2: Получение и копирование файлов конфигураций
        # ========================================================================
        logging.info(f"{'Получение файлов:':<50} начато")
        cfg_files = get_config_files(source, CONFIGS_DIR)
        if not cfg_files:
            if args.force:
                logging.warning(f"{'Продолжаем без файлов:':<50} (--force)")
            else:
                logging.error(f"{'Остановка:':<50} файлы не найдены")
                return

        logging.info(f"{'Копирование файлов...':<50}")
        progress_copy = ProgressBar(len(cfg_files), "Копирование файлов")
        for file_path in cfg_files:
            try:
                shutil.copy2(file_path, CONFIGS_DIR)
            except Exception as e:
                logging.error(f"{'Ошибка копирования:':<50} {file_path}\n{str(e)}")
            progress_copy.update(1)
            time.sleep(0.01)

        step_time = time.time() - start_step
        logging.info(f"{'Файлов скопировано:':<50} {len(cfg_files)}")
        logging.info(f"{'Копирование завершено:':<50} {step_time:.2f} сек")
        start_step = time.time()

        # ========================================================================
        # Шаг 3: Переименование файлов
        # ========================================================================
        logging.info(f"{'Переименование файлов:':<50} начато")
        if not rename_configs(CONFIGS_DIR):
            if args.force:
                logging.warning(f"{'Продолжаем:':<50} ошибка переименования (--force)")
            else:
                logging.error(f"{'Остановка:':<50} ошибка переименования")
                return

        step_time = time.time() - start_step
        logging.info(f"{'Переименование завершено:':<50} {step_time:.2f} сек")
        start_step = time.time()

        # ========================================================================
        # Шаг 4: Обработка nipper
        # ========================================================================
        logging.info(f"{'Обработка nipper:':<50} начата")
        if not process_with_nipper(CONFIGS_DIR, REPORTS_DIR, NIPPER_EXE, SCANNED_DEVICE, MAX_WORKERS):
            if args.force:
                logging.warning(f"{'Продолжаем:':<50} ошибки обработки (--force)")
            else:
                logging.error(f"{'Остановка:':<50} ошибки обработки")
                return

        step_time = time.time() - start_step
        logging.info(f"{'Обработка nipper завершена:':<50} {step_time:.2f} сек")
        start_step = time.time()

        # ========================================================================
        # Шаг 5: Генерация финального отчёта
        # ========================================================================
        logging.info(f"{'Генерация отчета:':<50} начата")
        new_report_path = generate_final_report(REPORTS_DIR, FINAL_RESULTS_DIR, REPORT_PREFIX)
        if not new_report_path:
            if args.force:
                logging.warning(f"{'Продолжаем:':<50} ошибка генерации (--force)")
            else:
                logging.error(f"{'Остановка:':<50} ошибка генерации отчета")
                return

        step_time = time.time() - start_step
        logging.info(f"{'Генерация отчета завершена:':<50} {step_time:.2f} сек")
        start_step = time.time()

        # ========================================================================
        # Шаг 6: Создание структуры задач
        # ========================================================================
        if CREATE_TASK_STRUCTURE and new_report_path:
            logging.info(f"{'Создание структуры задач:':<50} начато")
            # Передаем REPORTS_DIR для извлечения описаний из HTML отчетов
            if not create_task_folders(new_report_path, TASK_DISTRIBUTION_DIR, REPORTS_DIR):
                if args.force:
                    logging.warning(f"{'Продолжаем:':<50} ошибка создания структуры задач (--force)")
                else:
                    logging.error(f"{'Остановка:':<50} ошибка создания структуры задач")
                    return
            
            # Проверка созданной структуры
            if not verify_task_structure(TASK_DISTRIBUTION_DIR):
                logging.warning(f"{'Проверка структуры задач:':<50} обнаружены проблемы")
            
            step_time = time.time() - start_step
            logging.info(f"{'Создание структуры задач завершено:':<50} {step_time:.2f} сек")
            start_step = time.time()

        # ========================================================================
        # Шаг 7: Сравнение с предыдущим отчётом
        # ========================================================================
        if COMPARE_WITH_PREVIOUS and new_report_path:
            logging.info(f"{'Сравнение отчетов:':<50} начато")
            old_report_path = get_latest_report(FINAL_RESULTS_DIR, REPORT_PREFIX, exclude_path=new_report_path)
            if old_report_path:
                logging.info(f"{'Сравнение с:':<50} {os.path.basename(old_report_path)}")
                compare_reports(new_report_path, old_report_path, COMPARISON_DIR, COMPARISON_REPORT_PREFIX)
            else:
                logging.info(f"{'Предыдущий отчет для сравнения не найден':<50}")
            step_time = time.time() - start_step
            logging.info(f"{'Сравнение отчетов завершено:':<50} {step_time:.2f} сек")
            start_step = time.time()

        # ========================================================================
        # Шаг 8: Очистка временных данных
        # ========================================================================
        if CLEANUP_AFTER_SUCCESS:
            logging.info(f"{'Очистка временных файлов:':<50} начата")
            cleanup_directories(CONFIGS_DIR, REPORTS_DIR)
            step_time = time.time() - start_step
            logging.info(f"{'Очистка завершена:':<50} {step_time:.2f} сек")

        elapsed = time.time() - start_time
        logging.info("="*80)
        logging.info(f"{'ВЫПОЛНЕНИЕ ЗАВЕРШЕНО УСПЕШНО':^80}")
        logging.info(f"{'Общее время выполнения:':<50} {elapsed:.2f} сек")
        logging.info("="*80)

    except Exception as e:
        logging.exception(f"{'КРИТИЧЕСКАЯ ОШИБКА':<50}")
        elapsed = time.time() - start_time
        logging.error("="*80)
        logging.error(f"{'ВЫПОЛНЕНИЕ ПРЕРВАНО':^80}")
        logging.error(f"{'Прошло времени:':<50} {elapsed:.2f} сек")
        logging.error("="*80)

    finally:
        logging.info(f"{'Работа скрипта завершена':^80}")


if __name__ == "__main__":
    main()