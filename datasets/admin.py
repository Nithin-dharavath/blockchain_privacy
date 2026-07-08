from django.contrib import admin
from django.utils import timezone
from django.urls import reverse
from .models import Dataset
from notifications.utils import create_notification


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

    def save_model(self, request, obj, form, change):
        if change:
            old_status = Dataset.objects.get(pk=obj.pk).status
            new_status = obj.status
            if old_status != new_status and new_status in ('approved', 'rejected'):
                obj.approved_by = request.user
                obj.approved_at = timezone.now()
                verb = 'dataset_approved' if new_status == 'approved' else 'dataset_rejected'
                notes = obj.approval_notes or ''
                create_notification(
                    recipient=obj.uploaded_by,
                    verb=verb,
                    description=f'Dataset "{obj.name}" was {new_status} by {request.user.username}. {notes}',
                    actor=request.user,
                    action_url=reverse('datasets:detail', kwargs={'pk': obj.pk}),
                )
        super().save_model(request, obj, form, change)
