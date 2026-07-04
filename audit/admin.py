from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp",
        "user",
        "action_type",
        "content_type",
        "object_id",
        "object_repr",
        "ip_address",
        "request_method",
    ]
    list_filter = ["action_type", "content_type", "timestamp"]
    search_fields = ["object_repr", "url", "ip_address"]
    readonly_fields = ["timestamp", "changes"]
    date_hierarchy = "timestamp"
