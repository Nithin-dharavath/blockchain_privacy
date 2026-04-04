from django.contrib import admin
from .models import PrivacyTechnique

@admin.register(PrivacyTechnique)
class PrivacyTechniqueAdmin(admin.ModelAdmin):
    list_display = ['name', 'technique_type', 'security_level', 'is_active', 'created_at']
    list_filter = ['technique_type', 'is_active', 'security_level']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'technique_type', 'description')
        }),
        ('Technical Details', {
            'fields': ('algorithm_details', 'parameters', 'complexity')
        }),
        ('Security', {
            'fields': ('security_level', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
