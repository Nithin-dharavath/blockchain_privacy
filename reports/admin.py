from django.contrib import admin
from .models import Report, ReportSchedule, ReportTemplate, ReportShare

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_public', 'user', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'user', 'file_format', 'template', 'created_at']
    list_filter = ['report_type', 'file_format', 'template', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at']
    filter_horizontal = ['experiments']

@admin.register(ReportShare)
class ReportShareAdmin(admin.ModelAdmin):
    list_display = ['report', 'shared_by', 'shared_with_user', 'permissions', 'access_count', 'is_active', 'is_revoked', 'created_at']
    list_filter = ['permissions', 'is_revoked', 'created_at']
    search_fields = ['report__title', 'shared_by__username', 'shared_with_user__username']
    readonly_fields = ['share_token', 'created_at', 'last_accessed', 'access_count']

    def is_active(self, obj):
        return obj.is_active()
    is_active.boolean = True
    is_active.short_description = 'Active'

@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'schedule_frequency', 'next_run', 'last_run', 'is_active']
    list_filter = ['schedule_frequency', 'is_active', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'last_run', 'next_run']
    filter_horizontal = ['experiments']
