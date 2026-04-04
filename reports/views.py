from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from .models import Report
from .forms import ReportGenerationForm
from experiments.models import Experiment
import json
import csv
from datetime import datetime

@login_required
def report_list(request):
    """List all user's reports"""
    reports = Report.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'reports': page_obj
    }
    return render(request, 'reports/report_list.html', context)

@login_required
def report_generate(request):
    """Generate new report"""
    if request.method == 'POST':
        form = ReportGenerationForm(request.POST, user=request.user)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            
            # Get selected experiments
            experiments = form.cleaned_data['experiments']
            
            # Generate report content
            content = generate_report_content(experiments, report.report_type)
            report.content = content
            
            # Generate summary
            report.summary = generate_report_summary(experiments)
            
            report.save()
            form.save_m2m()
            
            # Generate file if needed
            if report.file_format in ['csv', 'json']:
                generate_report_file(report)
            
            messages.success(request, 'Report generated successfully!')
            return redirect('reports:detail', pk=report.pk)
    else:
        form = ReportGenerationForm(user=request.user)
    
    context = {
        'form': form,
        'completed_experiments': Experiment.objects.filter(
            user=request.user,
            status='completed'
        ).order_by('-created_at')
    }
    return render(request, 'reports/report_generate.html', context)

def generate_report_content(experiments, report_type):
    """Generate report content based on experiments"""
    content = []
    
    for exp in experiments:
        exp_data = {
            'name': exp.name,
            'technique': exp.privacy_technique.name,
            'dataset': exp.dataset.name,
            'status': exp.status,
            'privacy_score': exp.privacy_score,
            'execution_time': exp.execution_time,
            'accuracy': exp.accuracy,
            'throughput': exp.throughput,
            'anonymity_set_size': exp.anonymity_set_size,
            'metrics': exp.metrics,
            'created_at': exp.created_at.isoformat(),
            'completed_at': exp.completed_at.isoformat() if exp.completed_at else None
        }
        content.append(exp_data)
    
    return json.dumps(content, indent=2)

def generate_report_summary(experiments):
    """Generate summary statistics"""
    if not experiments:
        return "No experiments included in this report."
    
    total = experiments.count()
    avg_privacy = sum(e.privacy_score or 0 for e in experiments) / total
    avg_time = sum(e.execution_time or 0 for e in experiments) / total
    avg_accuracy = sum(e.accuracy or 0 for e in experiments) / total
    
    techniques = set(e.privacy_technique.name for e in experiments)
    
    summary = f"""
    Report Summary:
    - Total Experiments: {total}
    - Techniques Evaluated: {', '.join(techniques)}
    - Average Privacy Score: {avg_privacy:.2f}
    - Average Execution Time: {avg_time:.3f} seconds
    - Average Accuracy: {avg_accuracy:.4f}
    """
    
    return summary.strip()

def generate_report_file(report):
    """Generate downloadable report file"""
    import os
    from django.conf import settings
    
    experiments = report.experiments.all()
    filename = f"report_{report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{report.file_format}"
    filepath = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    if report.file_format == 'csv':
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['name', 'technique', 'dataset', 'privacy_score', 
                         'execution_time', 'accuracy', 'throughput', 'anonymity_set_size']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for exp in experiments:
                writer.writerow({
                    'name': exp.name,
                    'technique': exp.privacy_technique.name,
                    'dataset': exp.dataset.name,
                    'privacy_score': exp.privacy_score or 0,
                    'execution_time': exp.execution_time or 0,
                    'accuracy': exp.accuracy or 0,
                    'throughput': exp.throughput or 0,
                    'anonymity_set_size': exp.anonymity_set_size or 0,
                })
    
    elif report.file_format == 'json':
        data = []
        for exp in experiments:
            data.append({
                'name': exp.name,
                'technique': exp.privacy_technique.name,
                'dataset': exp.dataset.name,
                'privacy_score': exp.privacy_score,
                'execution_time': exp.execution_time,
                'accuracy': exp.accuracy,
                'throughput': exp.throughput,
                'anonymity_set_size': exp.anonymity_set_size,
                'metrics': exp.metrics
            })
        
        with open(filepath, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=2)
    
    report.file = f'reports/{filename}'
    report.save()

@login_required
def report_detail(request, pk):
    """View report details"""
    report = get_object_or_404(Report, pk=pk, user=request.user)
    
    # Parse content
    try:
        content_data = json.loads(report.content)
    except:
        content_data = []
    
    context = {
        'report': report,
        'content_data': content_data,
        'experiments': report.experiments.all()
    }
    return render(request, 'reports/report_detail.html', context)

@login_required
def report_download(request, pk):
    """Download report file"""
    report = get_object_or_404(Report, pk=pk, user=request.user)
    
    if not report.file:
        messages.error(request, 'No file available for download.')
        return redirect('reports:detail', pk=pk)
    
    # Serve file
    if report.file_format == 'csv':
        content_type = 'text/csv'
    elif report.file_format == 'json':
        content_type = 'application/json'
    else:
        content_type = 'application/octet-stream'
    
    with open(report.file.path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{report.file.name.split("/")[-1]}"'
        return response

@login_required
def report_delete(request, pk):
    """Delete report"""
    report = get_object_or_404(Report, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Delete file if exists
        if report.file:
            import os
            if os.path.isfile(report.file.path):
                os.remove(report.file.path)
        
        report.delete()
        messages.success(request, 'Report deleted successfully.')
        return redirect('reports:list')
    
    context = {'report': report}
    return render(request, 'reports/report_confirm_delete.html', context)
