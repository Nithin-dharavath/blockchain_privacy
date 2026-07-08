from .models import Notification


def notification_processor(request):
    if request.user.is_authenticated:
        qs = Notification.objects.filter(
            recipient=request.user, is_read=False
        )
        count = qs.count()
        return {
            "unread_notifications": qs[:5],
            "unread_count": count,
        }
    return {}
