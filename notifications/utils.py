from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()


def create_notification(recipient, verb, description, actor=None, action_url=""):
    Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=verb,
        description=description,
        action_url=action_url,
    )


def notify_all_admins(verb, description, actor=None, action_url=""):
    admins = User.objects.filter(is_staff=True)
    for admin in admins:
        create_notification(admin, verb, description, actor, action_url)
