from django.conf import settings
from django.db import models


class Notification(models.Model):
    VERB_CHOICES = [
        ("experiment_completed", "Experiment Completed"),
        ("experiment_failed", "Experiment Failed"),
        ("dataset_approved", "Dataset Approved"),
        ("dataset_rejected", "Dataset Rejected"),
        ("dataset_pending", "Dataset Pending Approval"),
        ("report_ready", "Report Ready"),
        ("report_shared", "Report Shared"),
        ("comparison_shared", "Comparison Shared"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions",
    )
    verb = models.CharField(max_length=30, choices=VERB_CHOICES)
    description = models.TextField()
    action_url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"], name="idx_notif_recipient_read"),
            models.Index(fields=["recipient", "created_at"], name="idx_notif_recipient_date"),
        ]

    def __str__(self):
        return f"{self.get_verb_display()} for {self.recipient.username} at {self.created_at}"
