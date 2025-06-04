# config.py
import os

# =============== КОНФИГУРАЦИЯ ===============
#можно вписывать сетевые папки, если это необходимо
# {ПУТЬ К ПАПКЕ} - менять вместе с {}

NETWORK_DIR = r'{ПУТЬ К ПАПКЕ}'                                                          #   путь, откуда берутся конфигурации для сканирования. Обрати внимание, что ведётся поиск по последней созданной папке, если файлы лежат в корне или еще что то, то надо переписать функцию find_latest_folder():
CONFIGS_DIR = r'{ПУТЬ К ПАПКЕ}'                      #   временная папка, куда будут сложены скопированные конфигурации
REPORTS_DIR = r'{ПУТЬ К ПАПКЕ}'                      #   временная папка, куда будут сложены полученные репорты
LOG_DIR = r'{ПУТЬ К ПАПКЕ}'                              #   папка с логами
FINAL_RESULTS_DIR = r'{ПУТЬ К ПАПКЕ}'          #   папка, куда будет сложен финальный отчёт
NIPPER_EXE = r'{ПУТЬ К ПАПКЕ}\nipper.exe'         #   путь к нипперу

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

# Настройка логирования
LOG_LEVEL = 'INFO'  # Изменено на строку для гибкости
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
# ============================================

# Дополнительные проверки
for dir_path in [CONFIGS_DIR, REPORTS_DIR, LOG_DIR, FINAL_RESULTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)
