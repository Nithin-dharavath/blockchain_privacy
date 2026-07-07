from django.contrib import admin
from .models import AdminNotification, SystemMetric, ExperimentErrorReport


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ('message', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('message',)
    readonly_fields = ('created_at',)


@admin.register(ExperimentErrorReport)
class ExperimentErrorReportAdmin(admin.ModelAdmin):
    list_display = ('experiment', 'error_message_short', 'resolved', 'created_at')
    list_filter = ('resolved', 'created_at', 'technique')
    search_fields = ('error_message', 'experiment__name')
    readonly_fields = ('created_at',)

    def error_message_short(self, obj):
        return obj.error_message[:80]
    error_message_short.short_description = 'Error Message'


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ('metric_name', 'metric_value', 'recorded_at')
    list_filter = ('metric_name', 'recorded_at')
    date_hierarchy = 'recorded_at'
    readonly_fields = ('recorded_at',)
