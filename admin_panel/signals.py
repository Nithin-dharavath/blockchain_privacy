from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import AdminNotification

User = get_user_model()


@receiver(post_save, sender=User)
def notify_new_user_registration(sender, instance, created, **kwargs):
    if created:
        AdminNotification.objects.create(
            message=f'New user registered: {instance.username} ({instance.email})',
            type='info',
            link=f'/admin-panel/users/',
        )


def notify_dataset_pending(sender, instance, created, **kwargs):
    from datasets.models import Dataset
    if created and instance.status == 'pending':
        AdminNotification.objects.create(
            message=f'New dataset pending approval: "{instance.name}" uploaded by {instance.uploaded_by.username}',
            type='warning',
            link=f'/admin-panel/datasets/{instance.pk}/approve/',
        )
    elif not created and instance.status == 'pending':
        AdminNotification.objects.create(
            message=f'Dataset re-submitted: "{instance.name}" by {instance.uploaded_by.username}',
            type='warning',
            link=f'/admin-panel/datasets/{instance.pk}/approve/',
        )


def check_experiment_failure_rate(sender, instance, **kwargs):
    from experiments.models import Experiment
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_failures = Experiment.objects.filter(
        status='failed',
        completed_at__gte=one_hour_ago,
    ).count()
    if recent_failures >= 3:
        threshold = 3
        AdminNotification.objects.create(
            message=f'Experiment failure rate spike: {recent_failures} failures in the last hour (threshold: {threshold})',
            type='danger',
            link='/admin-panel/reports/',
        )


def connect_notification_signals():
    from datasets.models import Dataset
    from experiments.models import Experiment

    post_save.connect(notify_dataset_pending, sender=Dataset, weak=False)
    post_save.connect(check_experiment_failure_rate, sender=Experiment, weak=False)
