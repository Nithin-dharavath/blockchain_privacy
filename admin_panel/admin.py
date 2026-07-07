from django.contrib import admin
from .models import AdminNotification, SystemMetric


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ('message', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('message',)
    readonly_fields = ('created_at',)


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ('metric_name', 'metric_value', 'recorded_at')
    list_filter = ('metric_name', 'recorded_at')
    date_hierarchy = 'recorded_at'
    readonly_fields = ('recorded_at',)
