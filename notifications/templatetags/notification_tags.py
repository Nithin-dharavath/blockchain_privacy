from django import template
from django.db.models import Count

from ..models import Notification

register = template.Library()


@register.simple_tag
def notification_badge(user):
    count = (
        Notification.objects.filter(recipient=user, is_read=False)
        .aggregate(count=Count("id"))["count"]
    )
    if count == 0:
        return ""
    return (
        f'<span class="notification-badge badge rounded-pill bg-danger ms-1"'
        f' data-unread-count="{count}">{count}</span>'
    )
