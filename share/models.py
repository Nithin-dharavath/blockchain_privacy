import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class ExperimentShare(models.Model):
    PERMISSION_CHOICES = (
        ('view_only', 'View Only'),
        ('download', 'Can Download'),
    )

    experiment = models.ForeignKey(
        'experiments.Experiment', on_delete=models.CASCADE,
        related_name='shared_links',
    )
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='shared_experiments',
    )
    share_token = models.UUIDField(
        unique=True, default=uuid.uuid4, editable=False,
    )
    expires_at = models.DateTimeField(blank=True, null=True)
    max_access_count = models.IntegerField(blank=True, null=True)
    permissions = models.CharField(
        max_length=20, choices=PERMISSION_CHOICES, default='view_only',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(blank=True, null=True)
    access_count = models.IntegerField(default=0)
    is_revoked = models.BooleanField(default=False)

    class Meta:
        db_table = 'experiment_shares'
        ordering = ['-created_at']

    def is_expired(self):
        if self.expires_at and self.expires_at < timezone.now():
            return True
        return False

    def is_active(self):
        if self.is_revoked:
            return False
        if self.is_expired():
            return False
        if self.max_access_count and self.access_count >= self.max_access_count:
            return False
        return True

    def record_access(self):
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])

    def __str__(self):
        return f"ExperimentShare {self.share_token} - {self.experiment.name}"
