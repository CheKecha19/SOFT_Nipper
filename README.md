
# SOFT Nipper :shield:  
**Утилита для автоматизированного анализа конфигураций сетевого оборудования**

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)  
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## :mag_right: Что это?
SOFT Nipper — инструмент для автоматизированной обработки конфигураций сетевых устройств (Cisco, Juniper и др.). Анализирует настройки безопасности, генерирует отчеты в формате HTML/PDF и выявляет уязвимости.

**Ключевые функции:**
- :file_folder: Пакетная обработка конфигураций
- :bar_chart: Генерация детализированных отчетов
- :warning: Обнаружение уязвимостей (открытые порты, слабые пароли)
- :gear: Поддержка шаблонов отчетов
- :floppy_disk: Экспорт в HTML/PDF/CSV
- :books: **Создание структуры задач** – автоматическое формирование папок с описанием каждой уязвимости и списком затронутых устройств
- :x: **Исключение ненужных правил** – возможность гибкой настройки фильтрации результатов

**Список поддерживаемых устройств:**
```
📦 Nipper Supported Devices
├── 🔹 Cisco
│   ├── IOS (--ios)
│   ├── IOS-XE (--ios-xe)
│   ├── ASA/PIX (--asa)
│   └── CatOS (--catos)
│
├── 🔹 Juniper
│   ├── JunOS (--junos)
│   └── ScreenOS (--screenos)
│
├── 🔹 HP/Aruba
│   └── ProCurve (--procurve)  # Используется в вашем конфиге
│
├── 🔹 Check Point
│   └(--checkpoint)
│
├── 🔹 Fortinet
│   └(--fortinet)
│
├── 🔹 Palo Alto
│   └(--paloalto)
│
└── 🔹 Другие
    ├── 3Com (--3com)
    ├── Alcatel (--alcatel)
    ├── Dell (--dell)
    └── Foundry (--foundry)
```

# Установка и использование _для хлебушков_
1. `git clone https://github.com/CheKecha19/SOFT_Nipper`
2. `pip install -r requirements.txt`
3. распаковываем `nipper.zip` - архив с основным .exe

Структура будет выглядеть примерно так:

```
📦 Nipper
├── 📂 folders
│   ├── 📂 configs               # Хранит конфигурационные файлы устройств (.cfg/.txt)
│   ├── 📂 final_results         # Финальные отчеты в формате Excel
│   ├── 📂 comparison_results    # Отчеты сравнения (при включённом COMPARE_WITH_PREVIOUS)
│   ├── 📂 log                   # Лог-файлы работы скрипта
│   ├── 📂 nipper_exe            # Директория с исполняемым файлом nipper.exe из Nipper.zip
│   ├── 📂 reports               # HTML-отчеты, сгенерированные nipper
│   └── 📂 отправить в задачи    # Папки с задачами для каждой уязвимости (если включено)
├── 📜 config.py                 # Конфигурационный файл (пути, настройки)
├── 📜 nipper.py                 # Основной скрипт
└── 📜 requirements.txt          # Зависимости Python
```

4. идём в `config.py` и меняем пути в переменных, откуда и куда будут отправляться данные. В моём случае это выглядит так:

```python
BASIC_PATH = r'C:\Users\cu-nazarov-na\Desktop\Nipper__доработка'   # базовый путь

NETWORK_DIR         = r'\\uni-imc\cfgbak$'
CONFIGS_DIR         = os.path.join(BASIC_PATH, 'folders', 'configs')
REPORTS_DIR         = os.path.join(BASIC_PATH, 'folders', 'reports')
LOG_DIR             = os.path.join(BASIC_PATH, 'folders', 'log')
FINAL_RESULTS_DIR   = os.path.join(BASIC_PATH, 'folders', 'final_results')
COMPARISON_DIR      = os.path.join(BASIC_PATH, 'folders', 'comparison_results')
TASK_DISTRIBUTION_DIR = os.path.join(BASIC_PATH, 'folders', 'отправить в задачи')
NIPPER_EXE          = os.path.join(BASIC_PATH, 'folders', 'nipper_exe', 'nipper.exe')
```

5. не забываем изменить сетевое устройство в `config.py`, по дефолту стоит `--procurve`
```python
SCANNED_DEVICE = '--procurve' 
```
6. в cmd запускаем наш скрипт `python nipper.py`
7. финальный отчёт, со всеми собранными миссконфигами, будет сохранён в папку `final_results`. Отладочные сообщения, если будут возникать ошибки, можно забрать из `log`.


# Особенности

### Режимы получения конфигураций
Скрипт может забирать `.cfg` файлы тремя способами (настраивается в `config.py` через переменную `FILE_SOURCE_MODE`):
- `latest_folder` – из самой свежей папки (по времени создания)
- `recent_files` – файлы, изменённые за последние `MAX_FILE_AGE_DAYS` дней
- `both` – объединение двух предыдущих вариантов (уникальные файлы)

### Исключение ненужных правил
В `config.py` добавлен список `EXCLUDED_ISSUES`, в котором можно указать регулярные выражения для фильтрации уязвимостей. Все проблемы, чьи названия совпадут с любым из паттернов, будут исключены из финального отчёта и, соответственно, из структуры задач.

Пример:
```python
EXCLUDED_ISSUES = [
    r"^SNMP Community",    # исключить все, начинающиеся с "SNMP Community"
    r"Telnet",             # исключить любые, содержащие "Telnet"
    r"Unencrypted\s+Protocol"  # более сложная регулярка
]
```

Если список пуст, фильтрация не применяется.

### Создание структуры задач (новая функция)
Если в `config.py` установить `CREATE_TASK_STRUCTURE = True`, после генерации сводного отчёта скрипт создаст папку `отправить в задачи`, внутри которой для каждой уязвимости будет создана отдельная папка с именем проблемы. Внутри папки:
- **Excel-файл** со списком IP-адресов устройств, на которых обнаружена данная уязвимость, а также полями `Overall`, `Impact`, `Ease`, `Fix`, `Recommendation`.
- **Текстовый файл `описание.txt`** с подробным описанием уязвимости, извлечённым из HTML-отчёта Nipper.

Эта структура предназначена для удобной раздачи задач ответственным инженерам.

### Сравнение с предыдущим отчётом
При `COMPARE_WITH_PREVIOUS = True` создаётся дополнительный Excel-отчёт в папке `comparison_results`, показывающий изменения между текущим и предыдущим сканированием: новые/удалённые устройства, новые/исправленные уязвимости, изменения статуса проблем на отдельных устройствах.

### Очистка временных файлов
Переменная `CLEANUP_AFTER_SUCCESS` управляет удалением папок `configs` и `reports` после успешного выполнения скрипта.

---

### Полный список настраиваемых параметров (config.py)

| Переменная | Назначение |
|------------|------------|
| `BASIC_PATH` | Базовый путь, от которого строятся остальные папки |
| `NETWORK_DIR` | Сетевая папка с исходными `.cfg` файлами |
| `CONFIGS_DIR` | Временная папка для скопированных конфигураций |
| `REPORTS_DIR` | Временная папка для HTML-отчётов Nipper |
| `LOG_DIR` | Папка для логов |
| `FINAL_RESULTS_DIR` | Папка для итоговых Excel-отчётов |
| `COMPARISON_DIR` | Папка для отчётов сравнения |
| `TASK_DISTRIBUTION_DIR` | Папка для структуры задач (если включена) |
| `NIPPER_EXE` | Путь к исполняемому файлу Nipper |
| `SCANNED_DEVICE` | Тип устройства (например, `--procurve`) |
| `LOG_LEVEL` | Уровень логирования (DEBUG, INFO, WARNING, ERROR) |
| `LOG_MAX_SIZE` | Максимальный размер лог-файла в байтах |
| `LOG_BACKUP_COUNT` | Количество хранимых ротированных логов |
| `CLEANUP_AFTER_SUCCESS` | Удалять временные папки после успешного выполнения |
| `CREATE_TASK_STRUCTURE` | Создавать структуру задач |
| `FILE_SOURCE_MODE` | Режим выбора файлов (`latest_folder`, `recent_files`, `both`) |
| `MAX_FILE_AGE_DAYS` | Максимальный возраст файлов (для режима recent_files) |
| `COMPARE_WITH_PREVIOUS` | Включать сравнение с предыдущим отчётом |
| `COMPARISON_REPORT_PREFIX` | Префикс для имён отчётов сравнения |
| `REPORT_PREFIX` | Префикс для имён итоговых отчётов |
| `MAX_WORKERS` | Количество потоков для параллельной обработки Nipper |
| `EXCLUDED_ISSUES` | Список регулярных выражений для исключения правил |

