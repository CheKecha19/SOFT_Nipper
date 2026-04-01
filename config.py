import os

# =============== БАЗОВЫЙ ПУТЬ ===============
BASIC_PATH = r'C:\Users\cu-nazarov-na\Desktop\Nipper__доработка'

# =============== КОНФИГУРАЦИЯ ===============
NETWORK_DIR             = r'\\uni-imc\cfgbak$'
CONFIGS_DIR             = os.path.join(BASIC_PATH, 'folders', 'configs')
REPORTS_DIR             = os.path.join(BASIC_PATH, 'folders', 'reports')
LOG_DIR                 = os.path.join(BASIC_PATH, 'folders', 'log')
FINAL_RESULTS_DIR       = os.path.join(BASIC_PATH, 'folders', 'final_results')
COMPARISON_DIR          = os.path.join(BASIC_PATH, 'folders', 'comparison_results')
TASK_DISTRIBUTION_DIR   = os.path.join(BASIC_PATH, 'folders', 'отправить в задачи')
NIPPER_EXE              = os.path.join(BASIC_PATH, 'folders', 'nipper_exe', 'nipper.exe')

# Выбор девайса
SCANNED_DEVICE = '--procurve' 

"""
    CMD Option       Device Type 
    ==================================================== 
    --auto           Auto-Detect Device (Default)
    --3com-firewall  3Com SuperStack 3 Firewall
    --accelar        Bay Networks Accelar
    --cp-firewall    CheckPoint Firewall Module
    --cp-management  CheckPoint Management Module
    --ios-router     Cisco IOS-based Router
    --ios-catalyst   Cisco IOS-based Catalyst Switch
    --pix            Cisco PIX-based Firewall
    --asa            Cisco ASA-based Firewall
    --fwsm           Cisco FWSM-based Router
    --catos          Cisco CatOS-based Catalyst
    --nmp            Cisco NMP-based Catalyst
    --css            Cisco Content Services Switch
    --procurve       HP ProCurve Switches
    --screenos       Juniper NetScreen Firewall
    --nokiaip        Nokia IP Firewall
    --passport       Nortel Passport Device
    --nortel-switch  Nortel Ethernet Routing Switch 8300
    --sonicos        SonicWall SonicOS Firewall
"""
# ============================================
# Настройка логирования
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# ============================================
# Удаление лишних папок после выполнения скрипта
CLEANUP_AFTER_SUCCESS = False

# ============================================
# Создание структуры задач
CREATE_TASK_STRUCTURE = True

# ============================================
# Настройка режима работы
FILE_SOURCE_MODE = 'recent_files'
MAX_FILE_AGE_DAYS = 60

VALID_MODES = ['latest_folder', 'recent_files', 'both']
if FILE_SOURCE_MODE not in VALID_MODES:
    raise ValueError(f"Invalid FILE_SOURCE_MODE. Must be one of: {', '.join(VALID_MODES)}")

# ============================================
# Настройка сравнения отчётов
COMPARE_WITH_PREVIOUS = True
COMPARISON_REPORT_PREFIX = 'comparison_report'
REPORT_PREFIX = 'scan_summary'

# ============================================
# Параллельная обработка
MAX_WORKERS = 1

# ============================================
# Исключение правил из финального отчёта
# Каждая строка интерпретируется как регулярное выражение (Python re).
# Если правило начинается с '^' и заканчивается '$', будет точное совпадение.
# Можно использовать просто подстроку – тогда будут исключены все правила,
# содержащие её.
EXCLUDED_ISSUES = [
    # Примеры:
    # r"^SNMP Community",        # все, начинающиеся с "SNMP Community"
    # r"Telnet",                 # любые, содержащие "Telnet"
    # r"Unencrypted\s+Protocol", # более сложная регулярка

    r"A User Was Configured With No Password",      # Не получилось воспользоваться учетной записью оператора без проля. Не подтвердилось.
    r"No Pre-Logon Banner Message",                 # не является уязвимостью
    r"Users Were Configured With No Password",      # Не получилось воспользоваться учетной записью оператора без проля. Не подтвердилось.
    r"Clear Text Telnet Service Enabled",           # Отработано
    r"No Connection Timeout",                       # Не верные данные сканера. Коммутаторы Comware по-умолчанию завершают неактивные сессии через 20 минут
    r"Weak Administrative Host Access Restrictions" 
]

# ============================================
# Дополнительные проверки
for dir_path in [CONFIGS_DIR, REPORTS_DIR, LOG_DIR, FINAL_RESULTS_DIR,
                 COMPARISON_DIR, TASK_DISTRIBUTION_DIR]:
    os.makedirs(dir_path, exist_ok=True)