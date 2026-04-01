import os
import logging
import time
import shutil
import logging.handlers
import sys

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

def setup_logging(log_dir, log_level, log_format, log_date_format, max_size=10*1024*1024, backup_count=5):
    """Настройка системы логирования с ротацией"""
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"nipper_log_{time.strftime('%Y%m%d_%H%M%S')}.txt")
        
        # Создаем ротирующий обработчик
        handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_size,
            backupCount=backup_count
        )
        
        # Форматирование
        formatter = logging.Formatter(log_format, log_date_format)
        handler.setFormatter(formatter)
        
        # Уровень логирования
        log_level_value = getattr(logging, log_level.upper(), logging.INFO)
        
        # Настройка базовой конфигурации
        logging.basicConfig(
            level=log_level_value,
            handlers=[handler, logging.StreamHandler()],
            format=log_format,
            datefmt=log_date_format
        )
        
        logging.info("="*80)
        logging.info(f"{'Логирование запущено':^80}")
        logging.info("="*80)
        logging.info(f"{'Уровень логирования:':<30} {log_level}")
        logging.info(f"{'Макс. размер лога:':<30} {max_size/1024/1024:.1f} MB")
        logging.info(f"{'Количество бэкапов:':<30} {backup_count}")
        return True
    except Exception as e:
        print(f"CRITICAL: Не удалось настроить логирование: {str(e)}")
        sys.exit(1)

def cleanup_directories(configs_dir, reports_dir):
    """Удаление временных папок"""
    try:
        if os.path.exists(configs_dir):
            shutil.rmtree(configs_dir)
            logging.info(f"{'Удалена папка:':<50} {configs_dir}")
        
        if os.path.exists(reports_dir):
            shutil.rmtree(reports_dir)
            logging.info(f"{'Удалена папка:':<50} {reports_dir}")
            
        return True
    except Exception as e:
        logging.exception(f"{'Ошибка удаления:':<50} {str(e)}")
        return False

def cleanup_task_distribution_dir(task_distribution_dir):
    """Очистка папки с задачами"""
    try:
        if os.path.exists(task_distribution_dir):
            shutil.rmtree(task_distribution_dir)
            logging.info(f"{'Очищена папка задач:':<50} {task_distribution_dir}")
            return True
        return False
    except Exception as e:
        logging.exception(f"{'Ошибка очистки папки задач:':<50} {str(e)}")
        return False