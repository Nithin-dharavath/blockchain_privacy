from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("RUN", "Run"),
        ("APPROVE", "Approve"),
        ("REJECT", "Reject"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("EXPORT", "Export"),
        ("DOWNLOAD", "Download"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    content_type = models.CharField(max_length=100)
    object_id = models.IntegerField()
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    url = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["content_type", "object_id"], name="idx_audit_content_object"),
            models.Index(fields=["user", "timestamp"], name="idx_audit_user_timestamp"),
            models.Index(fields=["action_type"], name="idx_audit_action_type"),
        ]

    def __str__(self):
        return f"{self.get_action_type_display()} on {self.content_type}#{self.object_id} at {self.timestamp}"
