from django.db import models
from django.conf import settings


class ExperimentErrorReport(models.Model):
    experiment = models.ForeignKey(
        'experiments.Experiment', on_delete=models.CASCADE,
        related_name='error_reports'
    )
    technique = models.ForeignKey(
        'privacy_tools.PrivacyTechnique', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    error_message = models.TextField()
    traceback = models.TextField(blank=True, default='')
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resolved_errors'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Experiment Error Report'
        verbose_name_plural = 'Experiment Error Reports'

    def __str__(self):
        return f"Error #{self.pk}: {self.error_message[:80]}"


class SystemMetric(models.Model):
    METRIC_NAMES = [
        ('active_users', 'Active Users'),
        ('experiments_per_hour', 'Experiments Per Hour'),
        ('avg_response_time', 'Avg Response Time (s)'),
        ('error_rate', 'Error Rate (%)'),
    ]

    metric_name = models.CharField(max_length=50, choices=METRIC_NAMES, db_index=True)
    metric_value = models.FloatField()
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-recorded_at']
        verbose_name = 'System Metric'
        verbose_name_plural = 'System Metrics'
        indexes = [
            models.Index(fields=['metric_name', 'recorded_at']),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} @ {self.recorded_at}"


class AdminNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
        ('success', 'Success'),
    ]

    message = models.TextField()
    type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='info')
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Notification'
        verbose_name_plural = 'Admin Notifications'

    def __str__(self):
        return f"[{self.get_type_display()}] {self.message[:60]}"
