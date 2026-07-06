import uuid
from django.db import models
from accounts.models import User
from experiments.models import Experiment
from audit.mixins import AuditableMixin
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class ReportTemplate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='report_templates'
    )
    sections = models.JSONField(
        default=list,
        help_text="Which sections to include: summary, methodology, results, comparison, recommendations, raw"
    )
    layout = models.JSONField(
        default=dict,
        help_text="Header text, footer text, colors, logo configuration"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'report_templates'
        ordering = ['name']


class Report(AuditableMixin, models.Model):
    REPORT_TYPE_CHOICES = (
        ('single', 'Single Experiment'),
        ('comparison', 'Comparison Report'),
        ('summary', 'Summary Report'),
    )
    
    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    )
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    experiments = models.ManyToManyField(Experiment, related_name='reports')
    
    content = models.TextField()
    summary = models.TextField(blank=True)
    
    file_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    
    template = models.ForeignKey(
        ReportTemplate, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='reports'
    )
    schedule = models.ForeignKey(
        'ReportSchedule', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='generated_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']


class ReportSchedule(models.Model):
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_schedules')
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=Report.REPORT_TYPE_CHOICES)
    file_format = models.CharField(max_length=10, choices=Report.FORMAT_CHOICES, default='pdf')
    schedule_frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    schedule_day = models.IntegerField(
        blank=True, null=True,
        help_text="Day of week (0=Mon..6=Sun) for weekly, day of month (1-31) for monthly"
    )
    experiments = models.ManyToManyField(Experiment, blank=True)
    filter_criteria = models.JSONField(blank=True, null=True, default=dict)
    last_run = models.DateTimeField(blank=True, null=True)
    next_run = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    auto_generate = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def compute_next_run(self):
        now = datetime.now()
        if self.schedule_frequency == 'daily':
            return now + timedelta(days=1)
        elif self.schedule_frequency == 'weekly':
            if self.schedule_day is None:
                return now + timedelta(days=7)
            days_ahead = (self.schedule_day - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return now + timedelta(days=days_ahead)
        elif self.schedule_frequency == 'monthly':
            day = self.schedule_day or 1
            next_date = now.replace(day=min(day, 28))
            if next_date <= now:
                next_date = next_date + relativedelta(months=1)
            return next_date
        return now + timedelta(days=7)

    def __str__(self):
        return f"{self.name} ({self.get_schedule_frequency_display()})"

    class Meta:
        db_table = 'report_schedules'
        ordering = ['-created_at']


class ReportShare(models.Model):
    PERMISSION_CHOICES = (
        ('view_only', 'View Only'),
        ('download', 'Can Download'),
    )

    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name='shared_links'
    )
    shared_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shared_reports'
    )
    shared_with_user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='received_shares'
    )
    share_token = models.UUIDField(
        unique=True, default=uuid.uuid4, editable=False
    )
    expires_at = models.DateTimeField(blank=True, null=True)
    max_access_count = models.IntegerField(blank=True, null=True)
    permissions = models.CharField(
        max_length=20, choices=PERMISSION_CHOICES, default='view_only'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(blank=True, null=True)
    access_count = models.IntegerField(default=0)
    is_revoked = models.BooleanField(default=False)

    def is_expired(self):
        if self.expires_at and self.expires_at < datetime.now(self.expires_at.tzinfo):
            return True
        return False

    def is_active(self):
        if self.is_revoked:
            return False
        if self.is_expired():
            return False
        if self.max_access_count and self.access_count >= self.max_access_count:
            return False
        return True

    def record_access(self):
        from django.utils import timezone
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])

    def __str__(self):
        return f"Share {self.share_token} - {self.report.title}"

    class Meta:
        db_table = 'report_shares'
        ordering = ['-created_at']
