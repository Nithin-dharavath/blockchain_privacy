import io
import os
import json
import base64
from datetime import datetime
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from experiments.visualization import (
    generate_comparison_chart, generate_radar_chart,
    generate_trend_chart, generate_privacy_breakdown, generate_scatter_chart
)


class PDFReportGenerator:
    """Generate professional PDF reports from experiment data."""
    
    def __init__(self, report):
        self.report = report
        self.experiments = list(report.experiments.all())
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Define custom paragraph styles for the report."""
        self.styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=self.styles['Title'],
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#1E293B'),
        ))
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=12,
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=24,
            spaceAfter=12,
            borderWidth=0,
            borderColor=colors.HexColor('#8B5CF6'),
            borderPadding=4,
        ))
        self.styles.add(ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading2'],
            fontSize=14,
            leading=17,
            textColor=colors.HexColor('#334155'),
            spaceBefore=16,
            spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            name='BodyText2',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#94A3B8'),
        ))
    
    def generate(self):
        """Generate the complete PDF report and return the file path."""
        filename = f"report_{self.report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=60,
            bottomMargin=60,
        )
        
        story = []
        self._add_cover_page(story)
        self._add_toc(story)
        self._add_executive_summary(story)
        self._add_methodology(story)
        self._add_results(story)
        if len(self.experiments) > 1:
            self._add_comparison(story)
        self._add_recommendations(story)
        self._add_raw_data_appendix(story)
        
        doc.build(story, onFirstPage=self._footer, onLaterPages=self._footer)
        
        self.report.file = f'reports/{filename}'
        self.report.save()
        return filepath
    
    def _footer(self, canvas, doc):
        """Draw footer on each page with page number and branding."""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#94A3B8'))
        
        # Left: platform branding
        canvas.drawString(
            50, 30,
            "Blockchain Privacy Platform — Confidential Report"
        )
        
        # Right: page number
        canvas.drawRightString(
            letter[0] - 50, 30,
            f"Page {doc.page}"
        )
        
        # Center: generation timestamp
        canvas.drawCentredString(
            letter[0] / 2, 30,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        # Top accent line
        canvas.setStrokeColor(colors.HexColor('#8B5CF6'))
        canvas.setLineWidth(2)
        canvas.line(50, letter[1] - 45, letter[0] - 50, letter[1] - 45)
        
        canvas.restoreState()
    
    def _add_cover_page(self, story):
        """Add cover page with title, user, organization, date, report type."""
        story.append(Spacer(1, 2 * inch))
        
        # Title
        story.append(Paragraph(
            self.report.title,
            self.styles['CoverTitle']
        ))
        
        # Report type badge
        type_display = self.report.get_report_type_display()
        story.append(Paragraph(
            f"<b>Report Type:</b> {type_display}",
            self.styles['CoverSubtitle']
        ))
        
        story.append(Spacer(1, 0.5 * inch))
        
        # Metadata table
        meta_data = [
            ['Author', self.report.user.get_full_name() or self.report.user.username],
            ['Organization', self.report.user.organization or 'N/A'],
            ['Date', self.report.created_at.strftime('%B %d, %Y')],
            ['Experiments', str(len(self.experiments))],
            ['Format', 'PDF'],
        ]
        
        meta_table = Table(meta_data, colWidths=[1.5 * inch, 3 * inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748B')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1E293B')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        story.append(meta_table)
        
        story.append(PageBreak())
    
    def _add_toc(self, story):
        """Add table of contents."""
        story.append(Paragraph("Table of Contents", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2 * inch))
        
        toc_items = [
            ("1.", "Executive Summary"),
            ("2.", "Methodology"),
            ("3.", "Results"),
        ]
        if len(self.experiments) > 1:
            toc_items.append(("4.", "Comparison Analysis"))
            toc_items.append(("5.", "Recommendations"))
        else:
            toc_items.append(("4.", "Recommendations"))
        toc_items.append(("6.", "Raw Data Appendix"))
        
        for num, title in toc_items:
            story.append(Paragraph(
                f"<b>{num}</b>&nbsp;&nbsp;{title}",
                self.styles['BodyText2']
            ))
        
        story.append(PageBreak())
    
    def _add_executive_summary(self, story):
        """Add executive summary section."""
        story.append(Paragraph("1. Executive Summary", self.styles['SectionHeader']))
        
        if not self.experiments:
            story.append(Paragraph(
                "No experiments were included in this report.",
                self.styles['BodyText2']
            ))
            story.append(PageBreak())
            return
        
        total = len(self.experiments)
        completed = sum(1 for e in self.experiments if e.status == 'completed')
        failed = sum(1 for e in self.experiments if e.status == 'failed')
        
        scores = [e.privacy_score or 0 for e in self.experiments if e.privacy_score is not None]
        avg_privacy = sum(scores) / len(scores) if scores else 0
        
        accuracies = [e.accuracy or 0 for e in self.experiments if e.accuracy is not None]
        avg_accuracy = (sum(accuracies) / len(accuracies)) * 100 if accuracies else 0
        
        exec_times = [e.execution_time or 0 for e in self.experiments if e.execution_time is not None]
        avg_time = sum(exec_times) / len(exec_times) if exec_times else 0
        
        techniques = list(set(e.privacy_technique.name for e in self.experiments))
        
        summary_lines = [
            f"This report presents the results of <b>{total}</b> privacy experiment(s) "
            f"conducted on the Blockchain Privacy Platform.",
            "",
            f"<b>Key Findings:</b>",
            f"• {completed} of {total} experiments completed successfully"
            + (f" ({failed} failed)" if failed else ""),
            f"• Average Privacy Score: <b>{avg_privacy:.2f}</b>/100",
            f"• Average Accuracy: <b>{avg_accuracy:.2f}%</b>",
            f"• Average Execution Time: <b>{avg_time:.3f}s</b>",
            f"• Techniques Evaluated: {', '.join(techniques)}",
        ]
        
        for line in summary_lines:
            if line:
                story.append(Paragraph(line, self.styles['BodyText2']))
            else:
                story.append(Spacer(1, 6))
        
        # Summary chart
        chart_b64 = generate_comparison_chart(self.experiments)
        if chart_b64:
            story.append(Spacer(1, 0.3 * inch))
            img_data = base64.b64decode(chart_b64)
            img = Image(io.BytesIO(img_data), width=6 * inch, height=3 * inch)
            story.append(img)
        
        story.append(PageBreak())
    
    def _add_methodology(self, story):
        """Add methodology section with technique descriptions."""
        story.append(Paragraph("2. Methodology", self.styles['SectionHeader']))
        
        # Group experiments by technique
        technique_groups = {}
        for exp in self.experiments:
            tech_name = exp.privacy_technique.name
            if tech_name not in technique_groups:
                technique_groups[tech_name] = {
                    'technique': exp.privacy_technique,
                    'experiments': [],
                    'configs': set(),
                }
            technique_groups[tech_name]['experiments'].append(exp)
            if exp.configuration:
                technique_groups[tech_name]['configs'].add(
                    json.dumps(exp.configuration, sort_keys=True)
                )
        
        for tech_name, group in technique_groups.items():
            tech = group['technique']
            
            story.append(Paragraph(tech.name, self.styles['SubSection']))
            story.append(Paragraph(
                f"<b>Type:</b> {tech.get_technique_type_display()}<br/>"
                f"<b>Security Level:</b> {tech.security_level}/10<br/>"
                f"<b>Complexity:</b> {tech.complexity or 'N/A'}",
                self.styles['BodyText2']
            ))
            story.append(Paragraph(
                f"<b>Description:</b> {tech.description}",
                self.styles['BodyText2']
            ))
            story.append(Paragraph(
                f"<b>Algorithm:</b> {tech.algorithm_details}",
                self.styles['BodyText2']
            ))
            
            # Configuration parameters
            if tech.parameters:
                story.append(Paragraph(
                    "<b>Default Parameters:</b>",
                    self.styles['BodyText2']
                ))
                param_data = [['Parameter', 'Value']]
                for k, v in tech.parameters.items():
                    param_data.append([str(k), str(v)])
                
                param_table = Table(param_data, colWidths=[2.5 * inch, 3 * inch])
                param_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(param_table)
            
            story.append(Spacer(1, 0.15 * inch))
        
        story.append(PageBreak())
    
    def _add_results(self, story):
        """Add detailed results for each experiment."""
        story.append(Paragraph("3. Results", self.styles['SectionHeader']))
        
        for idx, exp in enumerate(self.experiments, 1):
            story.append(Paragraph(
                f"3.{idx} {exp.name}",
                self.styles['SubSection']
            ))
            
            # Experiment metadata
            story.append(Paragraph(
                f"<b>Dataset:</b> {exp.dataset.name}<br/>"
                f"<b>Technique:</b> {exp.privacy_technique.name}<br/>"
                f"<b>Status:</b> {exp.get_status_display()}<br/>"
                f"<b>Created:</b> {exp.created_at.strftime('%Y-%m-%d %H:%M')}<br/>"
                + (f"<b>Completed:</b> {exp.completed_at.strftime('%Y-%m-%d %H:%M')}<br/>"
                   if exp.completed_at else ""),
                self.styles['BodyText2']
            ))
            
            # Metrics table
            metrics_data = [['Metric', 'Value']]
            metrics_data.append(['Privacy Score', f"{exp.privacy_score:.2f}" if exp.privacy_score else 'N/A'])
            metrics_data.append(['Accuracy', f"{exp.accuracy*100:.2f}%" if exp.accuracy else 'N/A'])
            metrics_data.append(['Throughput', f"{exp.throughput:.2f} tps" if exp.throughput else 'N/A'])
            metrics_data.append(['Execution Time', f"{exp.execution_time:.3f}s" if exp.execution_time else 'N/A'])
            metrics_data.append(['Anonymity Set Size', str(exp.anonymity_set_size) if exp.anonymity_set_size else 'N/A'])
            
            metrics_table = Table(metrics_data, colWidths=[2.5 * inch, 2 * inch])
            metrics_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ]))
            story.append(metrics_table)
            story.append(Spacer(1, 0.15 * inch))
            
            # Privacy breakdown chart
            breakdown_b64 = generate_privacy_breakdown(exp)
            if breakdown_b64:
                story.append(Paragraph(
                    "<b>Privacy Metric Breakdown:</b>",
                    self.styles['BodyText2']
                ))
                img_data = base64.b64decode(breakdown_b64)
                img = Image(io.BytesIO(img_data), width=5 * inch, height=2.5 * inch)
                story.append(img)
                story.append(Spacer(1, 0.15 * inch))
            
            # Error message if failed
            if exp.status == 'failed' and exp.error_message:
                story.append(Paragraph(
                    f"<b>Error:</b> {exp.error_message[:500]}",
                    self.styles['BodyText2']
                ))
            
            story.append(Spacer(1, 0.1 * inch))
        
        story.append(PageBreak())
    
    def _add_comparison(self, story):
        """Add side-by-side comparison section (only for multi-experiment reports)."""
        story.append(Paragraph("4. Comparison Analysis", self.styles['SectionHeader']))
        
        # Comparison bar chart
        chart_b64 = generate_comparison_chart(self.experiments)
        if chart_b64:
            story.append(Paragraph(
                "<b>Experiment Comparison:</b>",
                self.styles['BodyText2']
            ))
            img_data = base64.b64decode(chart_b64)
            img = Image(io.BytesIO(img_data), width=6 * inch, height=3 * inch)
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))
        
        # Radar chart
        radar_b64 = generate_radar_chart(self.experiments)
        if radar_b64:
            story.append(Paragraph(
                "<b>Multi-Axis Radar Comparison:</b>",
                self.styles['BodyText2']
            ))
            img_data = base64.b64decode(radar_b64)
            img = Image(io.BytesIO(img_data), width=5 * inch, height=5 * inch)
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))
        
        # Scatter chart
        scatter_b64 = generate_scatter_chart(self.experiments)
        if scatter_b64:
            story.append(Paragraph(
                "<b>Performance Scatter (Exec Time vs Throughput):</b>",
                self.styles['BodyText2']
            ))
            img_data = base64.b64decode(scatter_b64)
            img = Image(io.BytesIO(img_data), width=5 * inch, height=3 * inch)
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))
        
        # Ranking table
        story.append(Paragraph(
            "<b>Ranking Table:</b>",
            self.styles['BodyText2']
        ))
        
        ranked = sorted(self.experiments, key=lambda e: e.privacy_score or 0, reverse=True)
        rank_data = [['Rank', 'Experiment', 'Technique', 'Privacy', 'Accuracy', 'Throughput', 'Time']]
        for i, exp in enumerate(ranked, 1):
            rank_data.append([
                str(i),
                exp.name[:30],
                exp.privacy_technique.name[:20],
                f"{exp.privacy_score:.2f}" if exp.privacy_score else 'N/A',
                f"{exp.accuracy*100:.1f}%" if exp.accuracy else 'N/A',
                f"{exp.throughput:.1f}" if exp.throughput else 'N/A',
                f"{exp.execution_time:.3f}s" if exp.execution_time else 'N/A',
            ])
        
        rank_table = Table(
            rank_data,
            colWidths=[0.4*inch, 1.6*inch, 1.2*inch, 0.7*inch, 0.7*inch, 0.8*inch, 0.7*inch]
        )
        rank_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ]))
        story.append(rank_table)
        story.append(PageBreak())
    
    def _add_recommendations(self, story):
        """Add data-driven recommendations."""
        story.append(Paragraph(
            f"{'5' if len(self.experiments) > 1 else '4'}. Recommendations",
            self.styles['SectionHeader']
        ))
        
        if not self.experiments:
            story.append(Paragraph(
                "No data available for recommendations.",
                self.styles['BodyText2']
            ))
            story.append(PageBreak())
            return
        
        # Best for privacy
        best_privacy = max(
            [e for e in self.experiments if e.privacy_score is not None],
            key=lambda e: e.privacy_score,
            default=None
        )
        # Best for performance (throughput)
        best_perf = max(
            [e for e in self.experiments if e.throughput is not None],
            key=lambda e: e.throughput,
            default=None
        )
        # Fastest
        fastest = min(
            [e for e in self.experiments if e.execution_time is not None],
            key=lambda e: e.execution_time,
            default=None
        )
        # Best accuracy
        best_accuracy = max(
            [e for e in self.experiments if e.accuracy is not None],
            key=lambda e: e.accuracy,
            default=None
        )
        
        recs = []
        if best_privacy:
            recs.append(
                f"<b>Best for Privacy:</b> {best_privacy.name} "
                f"({best_privacy.privacy_technique.name}) — "
                f"Privacy Score: {best_privacy.privacy_score:.2f}"
            )
        if best_perf:
            recs.append(
                f"<b>Best for Performance:</b> {best_perf.name} "
                f"({best_perf.privacy_technique.name}) — "
                f"Throughput: {best_perf.throughput:.2f} tps"
            )
        if fastest:
            recs.append(
                f"<b>Fastest Execution:</b> {fastest.name} "
                f"({fastest.privacy_technique.name}) — "
                f"Time: {fastest.execution_time:.3f}s"
            )
        if best_accuracy:
            recs.append(
                f"<b>Best Accuracy:</b> {best_accuracy.name} "
                f"({best_accuracy.privacy_technique.name}) — "
                f"Accuracy: {best_accuracy.accuracy*100:.2f}%"
            )
        
        if recs:
            story.append(Paragraph(
                "Based on the experimental results, the following recommendations are made:",
                self.styles['BodyText2']
            ))
            for rec in recs:
                story.append(Paragraph(rec, self.styles['BodyText2']))
                story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(
                "Insufficient data to generate specific recommendations.",
                self.styles['BodyText2']
            ))
        
        # Trade-off analysis
        if len(self.experiments) > 1:
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(
                "<b>Trade-off Analysis:</b>",
                self.styles['SubSection']
            ))
            story.append(Paragraph(
                "Different privacy techniques offer varying trade-offs between privacy protection, "
                "performance, and accuracy. Consider your specific requirements when selecting "
                "a technique. Ring signatures and ZKPs provide strong privacy guarantees but "
                "may have higher computational overhead. Secure MPC distributes trust but "
                "requires multiple parties. Trusted execution environments offer hardware-level "
                "isolation but depend on specific hardware.",
                self.styles['BodyText2']
            ))
        
        story.append(PageBreak())
    
    def _add_raw_data_appendix(self, story):
        """Add raw data appendix with full experiment details."""
        story.append(Paragraph(
            f"{'6' if len(self.experiments) > 1 else '5'}. Raw Data Appendix",
            self.styles['SectionHeader']
        ))
        
        for idx, exp in enumerate(self.experiments, 1):
            story.append(Paragraph(
                f"A.{idx} {exp.name}",
                self.styles['SubSection']
            ))
            
            # Full data as table
            data_rows = [
                ['Field', 'Value'],
                ['ID', str(exp.id)],
                ['Name', exp.name],
                ['Description', exp.description[:200] if exp.description else 'N/A'],
                ['Dataset', exp.dataset.name],
                ['Technique', exp.privacy_technique.name],
                ['Technique Type', exp.privacy_technique.get_technique_type_display()],
                ['Status', exp.get_status_display()],
                ['Privacy Score', str(exp.privacy_score) if exp.privacy_score else 'N/A'],
                ['Accuracy', str(exp.accuracy) if exp.accuracy else 'N/A'],
                ['Throughput', str(exp.throughput) if exp.throughput else 'N/A'],
                ['Execution Time', str(exp.execution_time) if exp.execution_time else 'N/A'],
                ['Anonymity Set Size', str(exp.anonymity_set_size) if exp.anonymity_set_size else 'N/A'],
                ['Created At', exp.created_at.isoformat()],
                ['Completed At', exp.completed_at.isoformat() if exp.completed_at else 'N/A'],
            ]
            
            # Add configuration
            if exp.configuration:
                data_rows.append(['Configuration', json.dumps(exp.configuration, indent=2)[:500]])
            
            # Add metrics
            if exp.metrics:
                data_rows.append(['Metrics', json.dumps(exp.metrics, indent=2)[:500]])
            
            data_table = Table(data_rows, colWidths=[1.5 * inch, 4.5 * inch])
            data_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748B')),
            ]))
            story.append(data_table)
            story.append(Spacer(1, 0.2 * inch))