# config.py
import os

# =============== КОНФИГУРАЦИЯ ===============
NETWORK_DIR 		= r'{net_folder}'                                                          #   путь, откуда берутся конфигурации для сканирования. Обрати внимание, что ведётся поиск по последней созданной папке, если файлы лежат в корне или еще что то, то надо переписать функцию find_latest_folder():
CONFIGS_DIR 		= r'{folder}\configs'                      	#   временная папка, куда будут сложены скопированные конфигурации
REPORTS_DIR 		= r'{folder}\reports'                      	#   временная папка, куда будут сложены полученные репорты
LOG_DIR 		    = r'{folder}\log'                           #   папка с логами
FINAL_RESULTS_DIR 	= r'{folder}\final_results'          	#   папка, куда будет сложен финальный отчёт
NIPPER_EXE 		    = r'{folder}\scanner\nipper.exe'         	#   путь к нипперу
# ============================================
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
LOG_LEVEL = 'INFO'  # Изменено на строку для гибкости
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
# ============================================
# Удаление лишних папок после выполнения скрипта, если необходимо
CLEANUP_AFTER_SUCCESS = True  # Флаг для управления очисткой
# ============================================
# Дополнительные проверки, создание папок, если их нет.
for dir_path in [CONFIGS_DIR, REPORTS_DIR, LOG_DIR, FINAL_RESULTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)
# ============================================
# Настройка режима работы
FILE_SOURCE_MODE = 'recent_files'  # Варианты: 'latest_folder', 'recent_files', 'both'
MAX_FILE_AGE_DAYS = 60     # Используется в режимах 'recent_files' и 'both'

VALID_MODES = ['latest_folder', 'recent_files', 'both']
if FILE_SOURCE_MODE not in VALID_MODES:
    raise ValueError(f"Invalid FILE_SOURCE_MODE. Must be one of: {', '.join(VALID_MODES)}")
# ============================================
