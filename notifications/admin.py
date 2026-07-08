from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "recipient",
        "actor",
        "verb",
        "is_read",
        "action_url",
    ]
    list_filter = ["verb", "is_read", "created_at"]
    search_fields = ["description", "recipient__username", "actor__username"]
    readonly_fields = ["created_at", "read_at"]
    date_hierarchy = "created_at"
