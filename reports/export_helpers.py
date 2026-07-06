import io
import os
import json
import csv
import zipfile
import base64
from datetime import datetime
from django.conf import settings
from experiments.visualization import (
    generate_comparison_chart, generate_radar_chart,
    generate_privacy_breakdown, generate_scatter_chart,
)


def generate_xlsx_report(report):
    """Generate multi-sheet XLSX report using openpyxl."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    experiments = list(report.experiments.all())
    wb = Workbook()

    header_font = Font(bold=True, color='FFFFFF', size=11)
    header_fill = PatternFill(start_color='8B5CF6', end_color='8B5CF6', fill_type='solid')
    header_align = Alignment(horizontal='center', vertical='center')
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0'),
    )

    def style_header(ws, num_cols):
        for col in range(1, num_cols + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            cell.border = thin_border

    def add_data_rows(ws, rows, start_row=2):
        for r_idx, row in enumerate(rows, start_row):
            for c_idx, val in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                cell.border = thin_border

    # Sheet 1: Summary
    ws_summary = wb.active
    ws_summary.title = 'Summary'
    summary_headers = [
        'Report Title', 'Report Type', 'Generated', 'Total Experiments',
        'Avg Privacy Score', 'Avg Accuracy', 'Avg Execution Time',
    ]
    ws_summary.append(summary_headers)
    style_header(ws_summary, len(summary_headers))

    scores = [e.privacy_score or 0 for e in experiments if e.privacy_score is not None]
    accuracies = [e.accuracy or 0 for e in experiments if e.accuracy is not None]
    exec_times = [e.execution_time or 0 for e in experiments if e.execution_time is not None]

    ws_summary.append([
        report.title,
        report.get_report_type_display(),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        len(experiments),
        round(sum(scores) / len(scores), 2) if scores else 0,
        round((sum(accuracies) / len(accuracies)) * 100, 2) if accuracies else 0,
        round(sum(exec_times) / len(exec_times), 3) if exec_times else 0,
    ])
    add_data_rows(ws_summary, [])
    ws_summary.column_dimensions['A'].width = 30
    ws_summary.column_dimensions['B'].width = 20
    ws_summary.column_dimensions['C'].width = 22
    for col in ['D', 'E', 'F', 'G']:
        ws_summary.column_dimensions[col].width = 18

    # Sheet 2: Details
    ws_details = wb.create_sheet('Details')
    detail_headers = [
        'Name', 'Technique', 'Technique Type', 'Dataset', 'Status',
        'Privacy Score', 'Accuracy (%)', 'Throughput (tps)', 'Execution Time (s)',
        'Anonymity Set Size', 'Security Level', 'Complexity',
        'Created At', 'Completed At',
    ]
    ws_details.append(detail_headers)
    style_header(ws_details, len(detail_headers))

    for exp in experiments:
        ws_details.append([
            exp.name,
            exp.privacy_technique.name,
            exp.privacy_technique.get_technique_type_display(),
            exp.dataset.name,
            exp.get_status_display(),
            round(exp.privacy_score, 2) if exp.privacy_score else 'N/A',
            round(exp.accuracy * 100, 2) if exp.accuracy else 'N/A',
            round(exp.throughput, 2) if exp.throughput else 'N/A',
            round(exp.execution_time, 3) if exp.execution_time else 'N/A',
            exp.anonymity_set_size or 'N/A',
            exp.privacy_technique.security_level,
            exp.privacy_technique.complexity or 'N/A',
            exp.created_at.strftime('%Y-%m-%d %H:%M:%S') if exp.created_at else '',
            exp.completed_at.strftime('%Y-%m-%d %H:%M:%S') if exp.completed_at else '',
        ])
    add_data_rows(ws_details, [])

    ws_details.column_dimensions['A'].width = 25
    ws_details.column_dimensions['B'].width = 18
    ws_details.column_dimensions['C'].width = 16
    ws_details.column_dimensions['D'].width = 18
    for col in ['E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']:
        ws_details.column_dimensions[col].width = 14
    ws_details.column_dimensions['M'].width = 22
    ws_details.column_dimensions['N'].width = 22

    # Sheet 3: Raw Data
    ws_raw = wb.create_sheet('Raw Data')
    raw_headers = [
        'name', 'technique', 'dataset', 'privacy_score',
        'execution_time', 'accuracy', 'throughput', 'anonymity_set_size',
        'configuration', 'metrics',
    ]
    ws_raw.append(raw_headers)
    style_header(ws_raw, len(raw_headers))

    for exp in experiments:
        ws_raw.append([
            exp.name,
            exp.privacy_technique.name,
            exp.dataset.name,
            exp.privacy_score or 0,
            exp.execution_time or 0,
            exp.accuracy or 0,
            exp.throughput or 0,
            exp.anonymity_set_size or 0,
            json.dumps(exp.configuration) if exp.configuration else '',
            json.dumps(exp.metrics) if exp.metrics else '',
        ])
    add_data_rows(ws_raw, [])

    ws_raw.column_dimensions['A'].width = 25
    ws_raw.column_dimensions['B'].width = 18
    ws_raw.column_dimensions['C'].width = 18
    for col in ['D', 'E', 'F', 'G', 'H']:
        ws_raw.column_dimensions[col].width = 14
    ws_raw.column_dimensions['I'].width = 30
    ws_raw.column_dimensions['J'].width = 30

    filename = f"report_{report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)

    report.file = f'reports/{filename}'
    report.save()
    return filepath


def generate_zip_report(report):
    """Generate a ZIP file containing PDF, CSV, and JSON exports of the report."""
    experiments = list(report.experiments.all())
    base_name = f"report_{report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    filename = f"{base_name}.zip"
    filepath = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    csv_buf = io.StringIO()
    fieldnames = [
        'name', 'technique', 'technique_type', 'dataset', 'status',
        'privacy_score', 'execution_time', 'accuracy', 'throughput',
        'anonymity_set_size', 'security_level', 'complexity',
    ]
    writer = csv.DictWriter(csv_buf, fieldnames=fieldnames)
    writer.writeheader()
    for exp in experiments:
        writer.writerow({
            'name': exp.name,
            'technique': exp.privacy_technique.name,
            'technique_type': exp.privacy_technique.get_technique_type_display(),
            'dataset': exp.dataset.name,
            'status': exp.get_status_display(),
            'privacy_score': exp.privacy_score or 0,
            'execution_time': exp.execution_time or 0,
            'accuracy': exp.accuracy or 0,
            'throughput': exp.throughput or 0,
            'anonymity_set_size': exp.anonymity_set_size or 0,
            'security_level': exp.privacy_technique.security_level,
            'complexity': exp.privacy_technique.complexity or '',
        })

    json_data = []
    for exp in experiments:
        json_data.append({
            'name': exp.name,
            'technique': exp.privacy_technique.name,
            'technique_type': exp.privacy_technique.get_technique_type_display(),
            'dataset': exp.dataset.name,
            'status': exp.status,
            'privacy_score': exp.privacy_score,
            'execution_time': exp.execution_time,
            'accuracy': exp.accuracy,
            'throughput': exp.throughput,
            'anonymity_set_size': exp.anonymity_set_size,
            'configuration': exp.configuration,
            'metrics': exp.metrics,
            'created_at': exp.created_at.isoformat() if exp.created_at else None,
            'completed_at': exp.completed_at.isoformat() if exp.completed_at else None,
            'error_message': exp.error_message if exp.status == 'failed' else None,
        })

    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f'{base_name}.csv', csv_buf.getvalue())
        zf.writestr(f'{base_name}.json', json.dumps(json_data, indent=2))

        # Check if PDF was already generated
        if report.file and report.file_format == 'pdf':
            pdf_path = report.file.path
            if os.path.isfile(pdf_path):
                zf.write(pdf_path, f'{base_name}.pdf')

        # Check for chart images and include if available
        charts_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'charts', f'report_{report.id}')
        if os.path.isdir(charts_dir):
            for chart_file in sorted(os.listdir(charts_dir)):
                chart_path = os.path.join(charts_dir, chart_file)
                if os.path.isfile(chart_path):
                    zf.write(chart_path, f'charts/{chart_file}')

    report.file = f'reports/{filename}'
    report.save()
    return filepath


def export_chart_images(report):
    """Generate chart images for a report and return list of file paths."""
    experiments = list(report.experiments.all())
    if not experiments:
        return []

    charts_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'charts', f'report_{report.id}')
    os.makedirs(charts_dir, exist_ok=True)
    generated = []

    chart_generators = [
        ('comparison_bar', lambda: generate_comparison_chart(experiments, 'bar')),
        ('radar', lambda: generate_radar_chart(experiments)),
        ('scatter', lambda: generate_scatter_chart(experiments)),
    ]

    for chart_name, gen_func in chart_generators:
        try:
            b64_data = gen_func()
            if b64_data:
                img_bytes = base64.b64decode(b64_data)
                ext = 'png'
                chart_path = os.path.join(charts_dir, f'{chart_name}.{ext}')
                with open(chart_path, 'wb') as f:
                    f.write(img_bytes)
                generated.append(chart_path)
        except Exception:
            pass

    # Per-experiment breakdown charts
    for exp in experiments:
        try:
            b64_data = generate_privacy_breakdown(exp)
            if b64_data:
                img_bytes = base64.b64decode(b64_data)
                safe_name = f"breakdown_{exp.id}"
                chart_path = os.path.join(charts_dir, f'{safe_name}.png')
                with open(chart_path, 'wb') as f:
                    f.write(img_bytes)
                generated.append(chart_path)
        except Exception:
            pass

    return generated
