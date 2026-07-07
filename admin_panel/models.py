from django.db import models
from django.conf import settings


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
