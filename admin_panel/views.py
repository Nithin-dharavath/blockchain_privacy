from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Q, Sum, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate, TruncMonth
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from accounts.models import User
from datasets.models import Dataset
from experiments.models import Experiment
from privacy_tools.models import PrivacyTechnique
from privacy_tools.forms import PrivacyTechniqueForm
from audit.models import AuditLog
from datetime import timedelta
import json
import csv
import io

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
    """View enhanced system-wide reports with full analytics"""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # ── Time-series analysis ──────────────────────────────────────

    # Experiment volume over time (daily, last 30 days)
    volume_data = (
        Experiment.objects
        .filter(created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    volume_labels = [str(v['date']) for v in volume_data]
    volume_values = [v['count'] for v in volume_data]

    # Success rate over time (daily, last 30 days based on completed_at)
    daily_status = (
        Experiment.objects
        .filter(completed_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('completed_at'))
        .values('date')
        .annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            failed=Count('id', filter=Q(status='failed')),
        )
        .order_by('date')
    )
    success_labels = [str(d['date']) for d in daily_status]
    success_rates = [
        (d['completed'] / d['total'] * 100) if d['total'] > 0 else 0
        for d in daily_status
    ]

    # Average scores over time (daily, last 30 days)
    daily_scores = (
        Experiment.objects
        .filter(status='completed', completed_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('completed_at'))
        .values('date')
        .annotate(
            avg_privacy=Avg('privacy_score'),
            avg_accuracy=Avg('accuracy'),
            avg_throughput=Avg('throughput'),
        )
        .order_by('date')
    )
    score_labels = [str(s['date']) for s in daily_scores]
    avg_privacy_scores = [round(float(s['avg_privacy'] or 0), 2) for s in daily_scores]
    avg_accuracy_scores = [round(float(s['avg_accuracy'] or 0) * 100, 1) for s in daily_scores]
    avg_throughput_scores = [round(float(s['avg_throughput'] or 0), 2) for s in daily_scores]

    # ── User analytics ────────────────────────────────────────────

    # Active users per month (last 6 months)
    six_months_ago = now - timedelta(days=180)
    monthly_active = (
        Experiment.objects
        .filter(completed_at__gte=six_months_ago)
        .annotate(month=TruncMonth('completed_at'))
        .values('month')
        .annotate(active_users=Count('user', distinct=True))
        .order_by('month')
    )
    active_labels = [str(m['month'])[:7] for m in monthly_active]
    active_values = [m['active_users'] for m in monthly_active]

    # New users per month (last 6 months)
    new_users_monthly = (
        User.objects
        .filter(date_joined__gte=six_months_ago)
        .annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    new_user_labels = [str(m['month'])[:7] for m in new_users_monthly]
    new_user_values = [m['count'] for m in new_users_monthly]

    # Top 10 experimenters
    top_experimenters = (
        User.objects
        .annotate(experiment_count=Count('experiments'))
        .filter(experiment_count__gt=0)
        .order_by('-experiment_count')[:10]
    )

    # User type distribution
    user_type_dist = (
        User.objects
        .values('user_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    type_labels = [u['user_type'] for u in user_type_dist]
    type_values = [u['count'] for u in user_type_dist]

    # Experiments per user histogram (buckets)
    user_exp_counts = (
        User.objects
        .annotate(exp_count=Count('experiments'))
        .values_list('exp_count', flat=True)
    )
    histogram_buckets = {'0': 0, '1': 0, '2-5': 0, '6-10': 0, '11-20': 0, '20+': 0}
    for ec in user_exp_counts:
        if ec == 0:
            histogram_buckets['0'] += 1
        elif ec == 1:
            histogram_buckets['1'] += 1
        elif ec <= 5:
            histogram_buckets['2-5'] += 1
        elif ec <= 10:
            histogram_buckets['6-10'] += 1
        elif ec <= 20:
            histogram_buckets['11-20'] += 1
        else:
            histogram_buckets['20+'] += 1

    # ── Dataset analytics ─────────────────────────────────────────

    # Approval rate
    dataset_status_counts = (
        Dataset.objects
        .values('status')
        .annotate(count=Count('id'))
    )
    ds_status_map = {s['status']: s['count'] for s in dataset_status_counts}

    # Average approval time
    approved_datasets = Dataset.objects.filter(
        status='approved',
        approved_at__isnull=False,
    )
    avg_approval_time = None
    if approved_datasets.exists():
        avg_approval = approved_datasets.annotate(
            approval_duration=ExpressionWrapper(
                F('approved_at') - F('created_at'),
                output_field=DurationField()
            )
        ).aggregate(avg=Avg('approval_duration'))['avg']
        if avg_approval:
            avg_approval_time = round(avg_approval.total_seconds() / 3600, 1)

    # Dataset type distribution
    ds_type_dist = (
        Dataset.objects
        .values('dataset_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    ds_type_labels = [d['dataset_type'] for d in ds_type_dist]
    ds_type_values = [d['count'] for d in ds_type_dist]

    # Upload volume over time (monthly, last 6 months)
    upload_volume = (
        Dataset.objects
        .filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    upload_months = [str(u['month'])[:7] for u in upload_volume]
    upload_counts = [u['count'] for u in upload_volume]

    # ── Technique analytics ───────────────────────────────────────

    all_techniques = PrivacyTechnique.objects.all()

    # Usage frequency per technique
    tech_usage = (
        Experiment.objects
        .values('privacy_technique__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    tech_usage_labels = [t['privacy_technique__name'] for t in tech_usage]
    tech_usage_values = [t['count'] for t in tech_usage]

    # Average performance per technique
    tech_perf = (
        Experiment.objects
        .filter(status='completed')
        .values('privacy_technique__name')
        .annotate(
            avg_privacy=Avg('privacy_score'),
            avg_accuracy=Avg('accuracy'),
            avg_throughput=Avg('throughput'),
            avg_exec_time=Avg('execution_time'),
            count=Count('id'),
        )
        .order_by('-avg_privacy')
    )
    tech_perf_labels = [t['privacy_technique__name'] for t in tech_perf]
    tech_perf_privacy = [round(float(t['avg_privacy'] or 0), 2) for t in tech_perf]
    tech_perf_accuracy = [round(float(t['avg_accuracy'] or 0) * 100, 1) for t in tech_perf]
    tech_perf_throughput = [round(float(t['avg_throughput'] or 0), 2) for t in tech_perf]

    # Success rate per technique
    tech_totals = (
        Experiment.objects
        .values('privacy_technique_id')
        .annotate(total=Count('id'))
    )
    tech_completed = (
        Experiment.objects
        .filter(status='completed')
        .values('privacy_technique_id')
        .annotate(completed=Count('id'))
    )
    tech_failed = (
        Experiment.objects
        .filter(status='failed')
        .values('privacy_technique_id')
        .annotate(failed=Count('id'))
    )
    tech_total_map = {t['privacy_technique_id']: t['total'] for t in tech_totals}
    tech_completed_map = {t['privacy_technique_id']: t['completed'] for t in tech_completed}
    tech_failed_map = {t['privacy_technique_id']: t['failed'] for t in tech_failed}

    tech_success_rates = []
    for tech in all_techniques:
        total = tech_total_map.get(tech.pk, 0)
        completed = tech_completed_map.get(tech.pk, 0)
        if total > 0:
            tech_success_rates.append({
                'name': tech.name,
                'total': total,
                'completed': completed,
                'failed': tech_failed_map.get(tech.pk, 0),
                'success_rate': round(completed / total * 100, 1),
            })

    # ── System health ─────────────────────────────────────────────

    # Failure rate over time (monthly, last 6 months)
    monthly_failures = (
        Experiment.objects
        .filter(completed_at__gte=six_months_ago)
        .annotate(month=TruncMonth('completed_at'))
        .values('month')
        .annotate(
            total=Count('id'),
            failed=Count('id', filter=Q(status='failed')),
        )
        .order_by('month')
    )
    health_labels = [str(h['month'])[:7] for h in monthly_failures]
    failure_rates = [
        round(h['failed'] / h['total'] * 100, 1) if h['total'] > 0 else 0
        for h in monthly_failures
    ]
    monthly_volumes = [h['total'] for h in monthly_failures]

    # Average execution time trend (monthly, last 6 months)
    monthly_exec = (
        Experiment.objects
        .filter(status='completed', completed_at__gte=six_months_ago)
        .annotate(month=TruncMonth('completed_at'))
        .values('month')
        .annotate(avg_time=Avg('execution_time'))
        .order_by('month')
    )
    exec_month_labels = [str(e['month'])[:7] for e in monthly_exec]
    exec_times = [round(float(e['avg_time'] or 0), 2) for e in monthly_exec]

    # Most common error messages
    common_errors = (
        Experiment.objects
        .filter(error_message__isnull=False)
        .exclude(error_message__exact='')
        .values('error_message')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # ── Aggregate stats ──────────────────────────────────────────

    total_experiments = Experiment.objects.count()
    total_users = User.objects.count()
    total_datasets = Dataset.objects.count()
    total_techniques = all_techniques.count()
    avg_privacy = (
        Experiment.objects
        .filter(status='completed')
        .aggregate(avg=Avg('privacy_score'))['avg'] or 0
    )
    avg_accuracy = (
        Experiment.objects
        .filter(status='completed')
        .aggregate(avg=Avg('accuracy'))['avg'] or 0
    ) * 100
    total_exec_time = (
        Experiment.objects
        .filter(status='completed')
        .aggregate(total=Sum('execution_time'))['total'] or 0
    )

    context = {
        # Aggregate
        'total_experiments': total_experiments,
        'total_users': total_users,
        'total_datasets': total_datasets,
        'total_techniques': total_techniques,
        'overall_avg_privacy': round(avg_privacy, 2),
        'overall_avg_accuracy': round(avg_accuracy, 1),
        'total_exec_time': round(total_exec_time, 2),

        # Time-series
        'volume_labels': json.dumps(volume_labels),
        'volume_values': json.dumps(volume_values),
        'success_labels': json.dumps(success_labels),
        'success_rates': json.dumps(success_rates),
        'score_labels': json.dumps(score_labels),
        'avg_privacy_scores': json.dumps(avg_privacy_scores),
        'avg_accuracy_scores': json.dumps(avg_accuracy_scores),
        'avg_throughput_scores': json.dumps(avg_throughput_scores),

        # User analytics
        'active_labels': json.dumps(active_labels),
        'active_values': json.dumps(active_values),
        'new_user_labels': json.dumps(new_user_labels),
        'new_user_values': json.dumps(new_user_values),
        'top_experimenters': top_experimenters,
        'type_labels': json.dumps(type_labels),
        'type_values': json.dumps(type_values),
        'histogram_labels': json.dumps(list(histogram_buckets.keys())),
        'histogram_values': json.dumps(list(histogram_buckets.values())),

        # Dataset analytics
        'ds_approved': ds_status_map.get('approved', 0),
        'ds_rejected': ds_status_map.get('rejected', 0),
        'ds_pending': ds_status_map.get('pending', 0),
        'avg_approval_time': avg_approval_time,
        'ds_type_labels': json.dumps(ds_type_labels),
        'ds_type_values': json.dumps(ds_type_values),
        'upload_months': json.dumps(upload_months),
        'upload_counts': json.dumps(upload_counts),

        # Technique analytics
        'tech_usage_labels': json.dumps(tech_usage_labels),
        'tech_usage_values': json.dumps(tech_usage_values),
        'tech_perf_labels': json.dumps(tech_perf_labels),
        'tech_perf_privacy': json.dumps(tech_perf_privacy),
        'tech_perf_accuracy': json.dumps(tech_perf_accuracy),
        'tech_perf_throughput': json.dumps(tech_perf_throughput),
        'tech_success_rates': tech_success_rates,

        # System health
        'health_labels': json.dumps(health_labels),
        'failure_rates': json.dumps(failure_rates),
        'monthly_volumes': json.dumps(monthly_volumes),
        'exec_month_labels': json.dumps(exec_month_labels),
        'exec_times': json.dumps(exec_times),
        'common_errors': common_errors,
    }
    return render(request, 'admin_panel/system_reports.html', context)


@login_required
@user_passes_test(is_admin)
def admin_audit_logs(request):
    """Admin audit viewer — full log with advanced filters and bulk actions."""
    queryset = AuditLog.objects.select_related("user").all()

    action_type = request.GET.get("action_type")
    content_type = request.GET.get("content_type")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    user_id = request.GET.get("user_id")
    search = request.GET.get("search")

    filters = Q()
    if action_type:
        filters &= Q(action_type=action_type)
    if content_type:
        filters &= Q(content_type__icontains=content_type)
    if date_from:
        filters &= Q(timestamp__gte=date_from)
    if date_to:
        filters &= Q(timestamp__date__lte=date_to)
    if user_id:
        filters &= Q(user_id=user_id)
    if search:
        filters &= Q(object_repr__icontains=search) | Q(url__icontains=search)

    if filters:
        queryset = queryset.filter(filters)

    # Bulk actions
    if request.method == "POST":
        action = request.POST.get("bulk_action")
        selected_ids = request.POST.getlist("selected_ids")

        if not selected_ids:
            messages.warning(request, "No entries selected.")
            return redirect(request.path)

        if action == "export_csv":
            selected = AuditLog.objects.filter(pk__in=selected_ids).select_related("user")
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'
            writer = csv.writer(response)
            writer.writerow(["Timestamp", "User", "Action", "Content Type", "Object ID", "Object Repr", "IP", "URL", "Method"])
            for log in selected:
                writer.writerow([
                    log.timestamp, log.user.username if log.user else "System",
                    log.action_type, log.content_type, log.object_id,
                    log.object_repr, log.ip_address, log.url, log.request_method,
                ])
            return response

        elif action == "export_json":
            selected = AuditLog.objects.filter(pk__in=selected_ids).select_related("user")
            data = []
            for log in selected:
                data.append({
                    "timestamp": log.timestamp.isoformat(),
                    "user": log.user.username if log.user else None,
                    "action_type": log.action_type,
                    "content_type": log.content_type,
                    "object_id": log.object_id,
                    "object_repr": log.object_repr,
                    "changes": log.changes,
                    "ip_address": str(log.ip_address) if log.ip_address else None,
                    "url": log.url,
                    "request_method": log.request_method,
                })
            return JsonResponse(data, safe=False)

        elif action == "delete":
            count = AuditLog.objects.filter(pk__in=selected_ids).count()
            AuditLog.objects.filter(pk__in=selected_ids).delete()
            messages.success(request, f"Deleted {count} audit log entries.")
            return redirect(request.path)

    action_choices = AuditLog.ACTION_CHOICES
    content_type_values = (
        AuditLog.objects.values_list("content_type", flat=True)
        .distinct()
        .order_by("content_type")
    )
    users = User.objects.filter(audit_logs__isnull=False).distinct().order_by("username")
    total_count = AuditLog.objects.count()

    paginator = Paginator(queryset, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "action_choices": action_choices,
        "content_type_values": content_type_values,
        "users": users,
        "total_count": total_count,
        "filtered_count": queryset.count(),
        "filters": {
            "action_type": action_type,
            "content_type": content_type,
            "date_from": date_from,
            "date_to": date_to,
            "user_id": user_id,
            "search": search,
        },
    }
    return render(request, "admin_panel/audit_logs.html", context)


@login_required
@user_passes_test(is_admin)
def admin_audit_user(request, pk):
    """Audit trail for a specific user."""
    user = get_object_or_404(User, pk=pk)
    queryset = AuditLog.objects.filter(user=user).select_related("user")

    paginator = Paginator(queryset, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "audit_user": user,
        "action_choices": AuditLog.ACTION_CHOICES,
        "total_count": queryset.count(),
    }
    return render(request, "admin_panel/audit_logs.html", context)


@login_required
@user_passes_test(is_admin)
def admin_audit_object(request, content_type, pk):
    """Audit trail for a specific object."""
    queryset = AuditLog.objects.filter(
        content_type__iexact=content_type, object_id=pk
    ).select_related("user")

    object_repr = ""
    if queryset.exists():
        object_repr = queryset.first().object_repr

    paginator = Paginator(queryset, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "object_content_type": content_type,
        "object_pk": pk,
        "object_repr": object_repr,
        "action_choices": AuditLog.ACTION_CHOICES,
        "total_count": queryset.count(),
    }
    return render(request, "admin_panel/audit_logs.html", context)
