import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from audit.models import AuditLog

audit_logger = logging.getLogger('audit')
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
    action = "created" if created else "updated"
    audit_logger.info("User %s %s (pk=%s)", instance.username, action, instance.pk)


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
    audit_logger.info("User %s deleted (pk=%s)", instance.username, instance.pk)


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    ip = request.META.get("REMOTE_ADDR")
    AuditLog.objects.create(
        user=user,
        action_type="LOGIN",
        content_type="user",
        object_id=user.pk,
        object_repr=str(user)[:255],
        changes={},
        ip_address=ip,
    )
    audit_logger.info("User %s logged in from %s", user.username, ip)


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    if user is None:
        return
    ip = request.META.get("REMOTE_ADDR")
    AuditLog.objects.create(
        user=user,
        action_type="LOGOUT",
        content_type="user",
        object_id=user.pk,
        object_repr=str(user)[:255],
        changes={},
        ip_address=ip,
    )
    audit_logger.info("User %s logged out from %s", user.username, ip)
