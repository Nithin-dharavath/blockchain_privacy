from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from audit.models import AuditLog

User = get_user_model()


@receiver(post_save, sender=User)
def audit_user_save(sender, instance, created, **kwargs):
    AuditLog.objects.create(
        user=instance,
        action_type="CREATE" if created else "UPDATE",
        content_type="user",
        object_id=instance.pk,
        object_repr=str(instance)[:255],
        changes={},
    )


@receiver(post_delete, sender=User)
def audit_user_delete(sender, instance, **kwargs):
    AuditLog.objects.create(
        user=instance,
        action_type="DELETE",
        content_type="user",
        object_id=instance.pk,
        object_repr=str(instance)[:255],
        changes={},
    )


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        action_type="LOGIN",
        content_type="user",
        object_id=user.pk,
        object_repr=str(user)[:255],
        changes={},
        ip_address=request.META.get("REMOTE_ADDR"),
    )


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    if user is None:
        return
    AuditLog.objects.create(
        user=user,
        action_type="LOGOUT",
        content_type="user",
        object_id=user.pk,
        object_repr=str(user)[:255],
        changes={},
        ip_address=request.META.get("REMOTE_ADDR"),
    )
