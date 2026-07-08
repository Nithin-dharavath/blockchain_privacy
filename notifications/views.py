from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone

from .models import Notification


@login_required
def notification_list(request):
    queryset = Notification.objects.filter(recipient=request.user)

    filter_param = request.GET.get("filter")
    if filter_param == "unread":
        queryset = queryset.filter(is_read=False)
    elif filter_param == "read":
        queryset = queryset.filter(is_read=True)

    paginator = Paginator(queryset, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "current_filter": filter_param or "all",
    }
    return render(request, "notifications/list.html", context)


@login_required
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=["is_read", "read_at"])
    return JsonResponse({"status": "ok"})


@login_required
def mark_all_read(request):
    now = timezone.now()
    updated = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True, read_at=now)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"status": "ok", "updated": updated})
    return render(request, "notifications/list.html")


@login_required
def unread_count(request):
    count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()
    return JsonResponse({"unread_count": count})
