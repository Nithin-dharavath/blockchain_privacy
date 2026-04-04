from django.contrib import admin
from .models import Dataset

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'dataset_type', 'uploaded_by', 'status', 'row_count', 'created_at']
    list_filter = ['status', 'dataset_type', 'is_anonymized']
    search_fields = ['name', 'description', 'uploaded_by__username']
    readonly_fields = ['row_count', 'column_count', 'file_size', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'dataset_type', 'file')
        }),
        ('Upload Information', {
            'fields': ('uploaded_by', 'status', 'is_anonymized')
        }),
        ('File Details', {
            'fields': ('row_count', 'column_count', 'file_size')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approval_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
