from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'user', 'file_format', 'created_at']
    list_filter = ['report_type', 'file_format', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at']
    filter_horizontal = ['experiments']
