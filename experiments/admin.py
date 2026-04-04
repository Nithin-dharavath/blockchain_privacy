from django.contrib import admin
from .models import Experiment, ExperimentComparison

@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'privacy_technique', 'status', 'privacy_score', 'created_at']
    list_filter = ['status', 'privacy_technique', 'created_at']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'user')
        }),
        ('Experiment Setup', {
            'fields': ('dataset', 'privacy_technique', 'configuration', 'status')
        }),
        ('Results', {
            'fields': ('accuracy', 'privacy_score', 'execution_time', 'throughput', 
                      'anonymity_set_size', 'metrics')
        }),
        ('Error Handling', {
            'fields': ('error_message',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at', 'updated_at')
        }),
    )

@admin.register(ExperimentComparison)
class ExperimentComparisonAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    search_fields = ['name', 'user__username']
    filter_horizontal = ['experiments']
