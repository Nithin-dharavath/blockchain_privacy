from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from experiments.models import Experiment
from datasets.models import Dataset
from privacy_tools.models import PrivacyTechnique
from reports.models import Report

@login_required
def home_view(request):
    """Main dashboard view"""
    user = request.user
    
    # Get user statistics
    total_experiments = Experiment.objects.filter(user=user).count()
    completed_experiments = Experiment.objects.filter(
        user=user, 
        status='completed'
    ).count()
    total_datasets = Dataset.objects.filter(uploaded_by=user).count()
    total_reports = Report.objects.filter(user=user).count()
    
    # Recent experiments
    recent_experiments = Experiment.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Available privacy techniques
    privacy_techniques = PrivacyTechnique.objects.filter(is_active=True)
    
    # Recent datasets
    recent_datasets = Dataset.objects.filter(
        uploaded_by=user,
        status='approved'
    ).order_by('-created_at')[:5]
    
    # Performance metrics
    avg_privacy_score = Experiment.objects.filter(
        user=user,
        status='completed',
        privacy_score__isnull=False
    ).aggregate(Avg('privacy_score'))['privacy_score__avg'] or 0
    
    avg_execution_time = Experiment.objects.filter(
        user=user,
        status='completed',
        execution_time__isnull=False
    ).aggregate(Avg('execution_time'))['execution_time__avg'] or 0
    
    context = {
        'total_experiments': total_experiments,
        'completed_experiments': completed_experiments,
        'total_datasets': total_datasets,
        'total_reports': total_reports,
        'recent_experiments': recent_experiments,
        'privacy_techniques': privacy_techniques,
        'recent_datasets': recent_datasets,
        'avg_privacy_score': round(avg_privacy_score, 2),
        'avg_execution_time': round(avg_execution_time, 2),
    }
    
    return render(request, 'dashboard/home.html', context)

@login_required
def techniques_overview(request):
    """Privacy techniques overview"""
    techniques = PrivacyTechnique.objects.filter(is_active=True)
    
    # Get experiment counts for each technique
    technique_stats = []
    for technique in techniques:
        stats = {
            'technique': technique,
            'total_experiments': Experiment.objects.filter(
                privacy_technique=technique
            ).count(),
            'avg_privacy_score': Experiment.objects.filter(
                privacy_technique=technique,
                status='completed'
            ).aggregate(Avg('privacy_score'))['privacy_score__avg'] or 0,
            'avg_execution_time': Experiment.objects.filter(
                privacy_technique=technique,
                status='completed'
            ).aggregate(Avg('execution_time'))['execution_time__avg'] or 0,
        }
        technique_stats.append(stats)
    
    context = {
        'technique_stats': technique_stats
    }
    
    return render(request, 'dashboard/techniques_overview.html', context)
