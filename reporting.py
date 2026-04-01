import os
import glob
import pandas as pd
from datetime import datetime
import logging
import re
from utils import ProgressBar
from config import EXCLUDED_ISSUES   # импортируем список исключений


def verify_report(report_path):
    """Проверка целостности сгенерированного итогового отчета"""
    try:
        if not os.path.exists(report_path):
            logging.error(f"{'Отчет не существует:':<50} {report_path}")
            return False

        df = pd.read_excel(report_path)

        required_columns = ['Issue', 'Overall', 'Impact', 'Ease', 'Fix', 'Recommendation']
        for col in required_columns:
            if col not in df.columns:
                logging.error(f"{'Отсутствует колонка:':<50} {col} в {os.path.basename(report_path)}")
                return False

        if df.empty:
            logging.error(f"{'Отчет пуст:':<50} {os.path.basename(report_path)}")
            return False

        return True
    except Exception as e:
        logging.error(f"{'Ошибка проверки отчета:':<50} {os.path.basename(report_path)}\n{str(e)}")
        return False


def verify_comparison_report(report_path):
    """Проверка целостности отчета сравнения (меньше строгая)"""
    try:
        if not os.path.exists(report_path):
            logging.error(f"Отчет сравнения не существует: {report_path}")
            return False

        xls = pd.ExcelFile(report_path)
        if not xls.sheet_names:
            logging.error(f"Отчет сравнения пуст: {report_path}")
            return False

        return True
    except Exception as e:
        logging.error(f"Ошибка проверки отчета сравнения {report_path}: {str(e)}")
        return False


def generate_final_report(reports_dir, final_results_dir, report_prefix):
    """Генерация финального отчёта с возможностью исключения правил"""
    try:
        os.makedirs(final_results_dir, exist_ok=True)
        report_files = glob.glob(os.path.join(reports_dir, '*.html'))

        if not report_files:
            logging.warning(f"{'HTML отчеты:':<50} не найдены")
            return None

        # Компилируем регулярные выражения для исключённых правил
        excluded_patterns = []
        for pattern in EXCLUDED_ISSUES:
            try:
                excluded_patterns.append(re.compile(pattern))
            except re.error:
                logging.warning(f"Некорректное регулярное выражение в EXCLUDED_ISSUES: {pattern}")

        def is_issue_excluded(issue):
            """Возвращает True, если название проблемы подлежит исключению"""
            for pattern in excluded_patterns:
                if pattern.search(issue):
                    return True
            return False

        if excluded_patterns:
            logging.info(f"{'Исключаемые правила (паттернов):':<50} {len(excluded_patterns)}")
            for p in excluded_patterns:
                logging.debug(f"  {p.pattern}")

        host_issues = {}
        issue_meta = {}
        total_recommendations = 0
        excluded_count = 0

        progress = ProgressBar(len(report_files), "Обработка отчетов")
        logging.info(f"{'Обработка отчетов:':<50} {len(report_files)} файлов")

        from nipper_processing import extract_recommendations_from_html

        for report_file in report_files:
            filename = os.path.basename(report_file)
            ip_match = re.search(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', filename)
            ip_address = ip_match.group(1) if ip_match else filename.split('_')[0]

            recommendations = extract_recommendations_from_html(report_file)

            if recommendations:
                total_recommendations += len(recommendations)

                for rec in recommendations:
                    issue = rec['Issue']
                    # Проверяем исключение
                    if is_issue_excluded(issue):
                        excluded_count += 1
                        continue

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

            progress.update(1)

        # Логируем количество исключённых записей
        if excluded_count:
            logging.info(f"{'Исключено рекомендаций (по правилам):':<50} {excluded_count}")

        if not host_issues:
            logging.warning(f"{'Данные для отчета:':<50} не найдены (возможно, все правила исключены)")
            return None

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
        output_path = os.path.join(final_results_dir, f'{report_prefix}_{timestamp}.xlsx')
        df.to_excel(output_path, index=False)

        if verify_report(output_path):
            logging.info(f"{'Финальный отчет сохранен:':<50} {output_path}")
            logging.info(f"{'Всего рекомендаций (до исключения):':<50} {total_recommendations}")
            logging.info(f"{'Рекомендаций в отчете:':<50} {len(host_issues)}")
            return output_path
        else:
            logging.error(f"{'Ошибка отчета:':<50} отчет не прошел проверку")
            if os.path.exists(output_path):
                os.remove(output_path)
            return None
    except Exception as e:
        logging.exception(f"{'Ошибка генерации:':<50} {str(e)}")
        return None


def compare_reports(new_report_path, old_report_path, comparison_dir, comparison_report_prefix):
    """Сравнение двух отчётов и генерация отчёта о различиях"""
    try:
        if not verify_report(new_report_path):
            logging.error(f"Новый отчет поврежден или некорректен: {os.path.basename(new_report_path)}")
            return None
        if not verify_report(old_report_path):
            logging.warning(f"Старый отчет поврежден/некорректен и не будет использоваться в сравнении: {os.path.basename(old_report_path)}")
            return None

        df_new = pd.read_excel(new_report_path)
        df_old = pd.read_excel(old_report_path)

        meta_columns = ['Issue', 'Overall', 'Impact', 'Ease', 'Fix', 'Recommendation']
        devices_new = [col for col in df_new.columns if col not in meta_columns]
        devices_old = [col for col in df_old.columns if col not in meta_columns]

        common_devices = sorted(set(devices_new) & set(devices_old))
        new_devices = sorted(set(devices_new) - set(devices_old))
        removed_devices = sorted(set(devices_old) - set(devices_new))

        common_issues = sorted(set(df_new['Issue']) & set(df_old['Issue']))
        new_issues = sorted(set(df_new['Issue']) - set(df_old['Issue']))
        fixed_issues = sorted(set(df_old['Issue']) - set(df_new['Issue']))

        fixed_vulnerabilities = []
        new_vulnerabilities = []

        for issue in common_issues:
            for device in common_devices:
                status_old = df_old.loc[df_old['Issue'] == issue, device].values[0]
                status_new = df_new.loc[df_new['Issue'] == issue, device].values[0]

                if status_old == 1 and status_new == 0:
                    fixed_vulnerabilities.append({
                        'Issue': issue,
                        'Device': device,
                        'Статус': 'Исправлено'
                    })
                elif status_old == 0 and status_new == 1:
                    new_vulnerabilities.append({
                        'Issue': issue,
                        'Device': device,
                        'Статус': 'Появилось'
                    })

        comparison_data = {
            'Изменения': [
                f"Новые устройства ({len(new_devices)})",
                f"Удаленные устройства ({len(removed_devices)})",
                f"Новые уязвимости ({len(new_issues)})",
                f"Исправленные уязвимости ({len(fixed_issues)})",
                f"Исправленные проблемы ({len(fixed_vulnerabilities)})",
                f"Новые проблемы ({len(new_vulnerabilities)})"
            ],
            'Количество': [
                len(new_devices),
                len(removed_devices),
                len(new_issues),
                len(fixed_issues),
                len(fixed_vulnerabilities),
                len(new_vulnerabilities)
            ]
        }

        df_comparison = pd.DataFrame(comparison_data)
        df_new_devices = pd.DataFrame(new_devices, columns=['Новые устройства'])
        df_removed_devices = pd.DataFrame(removed_devices, columns=['Удаленные устройства'])
        df_new_issues = pd.DataFrame(new_issues, columns=['Новые уязвимости'])
        df_fixed_issues = pd.DataFrame(fixed_issues, columns=['Исправленные уязвимости'])
        df_status_changes = pd.DataFrame(fixed_vulnerabilities + new_vulnerabilities)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(comparison_dir, f'{comparison_report_prefix}_{timestamp}.xlsx')

        with pd.ExcelWriter(output_path) as writer:
            df_comparison.to_excel(writer, sheet_name='Сводка', index=False)
            if not df_new_devices.empty:
                df_new_devices.to_excel(writer, sheet_name='Новые устройства', index=False)
            if not df_removed_devices.empty:
                df_removed_devices.to_excel(writer, sheet_name='Удаленные устройства', index=False)
            if not df_new_issues.empty:
                df_new_issues.to_excel(writer, sheet_name='Новые уязвимости', index=False)
            if not df_fixed_issues.empty:
                df_fixed_issues.to_excel(writer, sheet_name='Исправленные уязвимости', index=False)
            if not df_status_changes.empty:
                df_status_changes.to_excel(writer, sheet_name='Изменения статуса', index=False)

        from reporting import verify_comparison_report

        if verify_comparison_report(output_path):
            logging.info(f"{'Отчет сравнения сохранен:':<50} {output_path}")
            return output_path
        else:
            logging.error(f"{'Ошибка отчета сравнения:':<50} не прошел проверку")
            if os.path.exists(output_path):
                os.remove(output_path)
            return None

    except Exception as e:
        logging.exception(f"{'Ошибка сравнения:':<50} {str(e)}")
        return None


def get_latest_report(final_results_dir, report_prefix, exclude_path=None):
    """Получение пути к последнему валидному отчёту, исключая текущий"""
    try:
        reports = sorted(
            glob.glob(os.path.join(final_results_dir, f'{report_prefix}_*.xlsx')),
            key=os.path.getctime,
            reverse=True
        )

        if exclude_path and exclude_path in reports:
            reports.remove(exclude_path)

        for report in reports:
            if verify_report(report):
                return report

        return None
    except Exception as e:
        logging.error(f"{'Ошибка поиска отчета:':<50} {str(e)}")
        return None