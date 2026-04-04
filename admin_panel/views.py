from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.core.paginator import Paginator
from accounts.models import User
from datasets.models import Dataset
from experiments.models import Experiment
from privacy_tools.models import PrivacyTechnique
from privacy_tools.forms import PrivacyTechniqueForm

def is_admin(user):
    """Check if user is admin"""
    return user.is_staff or user.user_type == 'admin'

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard"""
    # Statistics
    total_users = User.objects.count()
    total_experiments = Experiment.objects.count()
    total_datasets = Dataset.objects.count()
    pending_datasets = Dataset.objects.filter(status='pending').count()
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_experiments = Experiment.objects.order_by('-created_at')[:5]
    pending_dataset_list = Dataset.objects.filter(status='pending').order_by('-created_at')[:5]
    
    # Technique statistics
    technique_stats = PrivacyTechnique.objects.annotate(
        experiment_count=Count('experiments')
    ).order_by('-experiment_count')
    
    # Performance metrics
    avg_privacy_score = Experiment.objects.filter(
        status='completed'
    ).aggregate(Avg('privacy_score'))['privacy_score__avg'] or 0
    
    context = {
        'total_users': total_users,
        'total_experiments': total_experiments,
        'total_datasets': total_datasets,
        'pending_datasets': pending_datasets,
        'recent_users': recent_users,
        'recent_experiments': recent_experiments,
        'pending_dataset_list': pending_dataset_list,
        'technique_stats': technique_stats,
        'avg_privacy_score': round(avg_privacy_score, 2),
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    """Manage users"""
    users = User.objects.all().order_by('-date_joined')
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Filter by user type
    user_type = request.GET.get('user_type')
    if user_type:
        users = users.filter(user_type=user_type)
    
    # Pagination
    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'search_query': search_query,
        'user_type': user_type
    }
    return render(request, 'admin_panel/manage_users.html', context)

@login_required
@user_passes_test(is_admin)
def toggle_user_approval(request, pk):
    """Toggle user approval status"""
    user = get_object_or_404(User, pk=pk)
    user.is_approved = not user.is_approved
    user.save()
    
    status = "approved" if user.is_approved else "suspended"
    messages.success(request, f'User {user.username} has been {status}.')
    return redirect('admin_panel:manage_users')

@login_required
@user_passes_test(is_admin)
def manage_datasets(request):
    """Manage datasets"""
    datasets = Dataset.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        datasets = datasets.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(datasets, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'datasets': page_obj,
        'status_filter': status_filter
    }
    return render(request, 'admin_panel/manage_datasets.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.user_type == 'admin')
def approve_dataset(request, pk):
    """Approve or reject a dataset"""
    from django.utils import timezone
    from django.contrib import messages
    
    dataset = get_object_or_404(Dataset, pk=pk)
    
    if request.method == 'POST':
        # Get action from POST data
        action = request.POST.get('action', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Debug: Print what was received
        print(f"DEBUG - POST Data: {request.POST}")
        print(f"DEBUG - Action: '{action}'")
        print(f"DEBUG - Notes: '{notes}'")
        
        # Check action and process
        if action == 'approve':
            dataset.status = 'approved'
            dataset.approval_notes = notes if notes else 'Approved by admin'
            dataset.approved_by = request.user
            dataset.approved_at = timezone.now()
            dataset.save()
            
            messages.success(request, f'Dataset "{dataset.name}" has been approved successfully.')
            return redirect('admin_panel:manage_datasets')
        
        elif action == 'reject':
            dataset.status = 'rejected'
            dataset.approval_notes = notes if notes else 'Rejected by admin'
            dataset.approved_by = request.user
            dataset.approved_at = timezone.now()
            dataset.save()
            
            messages.warning(request, f'Dataset "{dataset.name}" has been rejected.')
            return redirect('admin_panel:manage_datasets')
        
        else:
            # Unknown action - show error
            messages.error(request, f'Invalid action: "{action}"')
            print(f"DEBUG - Invalid action received: '{action}'")
    
    context = {
        'dataset': dataset,
    }
    
    return render(request, 'admin_panel/approve_dataset.html', context)


@login_required
@user_passes_test(is_admin)
def manage_techniques(request):
    """Manage privacy techniques"""
    techniques = PrivacyTechnique.objects.all().order_by('technique_type')
    
    context = {'techniques': techniques}
    return render(request, 'admin_panel/manage_techniques.html', context)

@login_required
@user_passes_test(is_admin)
def add_technique(request):
    """Add new privacy technique"""
    if request.method == 'POST':
        form = PrivacyTechniqueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Privacy technique added successfully.')
            return redirect('admin_panel:manage_techniques')
    else:
        form = PrivacyTechniqueForm()
    
    context = {'form': form}
    return render(request, 'admin_panel/add_technique.html', context)

@login_required
@user_passes_test(is_admin)
def edit_technique(request, pk):
    """Edit privacy technique"""
    technique = get_object_or_404(PrivacyTechnique, pk=pk)
    
    if request.method == 'POST':
        form = PrivacyTechniqueForm(request.POST, instance=technique)
        if form.is_valid():
            form.save()
            messages.success(request, 'Privacy technique updated successfully.')
            return redirect('admin_panel:manage_techniques')
    else:
        form = PrivacyTechniqueForm(instance=technique)
    
    context = {'form': form, 'technique': technique}
    return render(request, 'admin_panel/edit_technique.html', context)

@login_required
@user_passes_test(is_admin)
def toggle_technique(request, pk):
    """Toggle technique active status"""
    technique = get_object_or_404(PrivacyTechnique, pk=pk)
    technique.is_active = not technique.is_active
    technique.save()
    
    status = "activated" if technique.is_active else "deactivated"
    messages.success(request, f'Technique "{technique.name}" has been {status}.')
    return redirect('admin_panel:manage_techniques')

@login_required
@user_passes_test(is_admin)
def system_reports(request):
    """View system-wide reports"""
    # Experiment statistics by technique
    technique_performance = []
    techniques = PrivacyTechnique.objects.all()
    
    for technique in techniques:
        experiments = Experiment.objects.filter(
            privacy_technique=technique,
            status='completed'
        )
        
        if experiments.exists():
            stats = {
                'technique': technique.name,
                'total_experiments': experiments.count(),
                'avg_privacy_score': experiments.aggregate(Avg('privacy_score'))['privacy_score__avg'] or 0,
                'avg_execution_time': experiments.aggregate(Avg('execution_time'))['execution_time__avg'] or 0,
                'avg_accuracy': experiments.aggregate(Avg('accuracy'))['accuracy__avg'] or 0,
            }
            technique_performance.append(stats)
    
    # User activity
    user_activity = User.objects.annotate(
        experiment_count=Count('experiments')
    ).order_by('-experiment_count')[:10]
    
    context = {
        'technique_performance': technique_performance,
        'user_activity': user_activity
    }
    return render(request, 'admin_panel/system_reports.html', context)
