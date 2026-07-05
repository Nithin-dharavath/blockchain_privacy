from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import AuditLog

User = get_user_model()


def is_admin(user):
    return user.is_staff or user.user_type == "admin"


@login_required
@user_passes_test(is_admin)
def audit_log_list(request):
    queryset = AuditLog.objects.select_related("user").all()

    action_type = request.GET.get("action_type")
    content_type = request.GET.get("content_type")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    user_id = request.GET.get("user_id")
    search = request.GET.get("search")

    filters = Q()
    if action_type:
        filters &= Q(action_type=action_type)
    if content_type:
        filters &= Q(content_type__icontains=content_type)
    if date_from:
        filters &= Q(timestamp__gte=date_from)
    if date_to:
        filters &= Q(timestamp__date__lte=date_to)
    if user_id:
        filters &= Q(user_id=user_id)
    if search:
        filters &= Q(object_repr__icontains=search) | Q(url__icontains=search)

    if filters:
        queryset = queryset.filter(filters)

    action_choices = AuditLog.ACTION_CHOICES
    content_type_values = (
        AuditLog.objects.values_list("content_type", flat=True)
        .distinct()
        .order_by("content_type")
    )
    users = User.objects.filter(audit_logs__isnull=False).distinct().order_by("username")

    paginator = Paginator(queryset, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "action_choices": action_choices,
        "content_type_values": content_type_values,
        "users": users,
        "filters": {
            "action_type": action_type,
            "content_type": content_type,
            "date_from": date_from,
            "date_to": date_to,
            "user_id": user_id,
            "search": search,
        },
        "is_object_history": False,
    }
    return render(request, "audit/audit_list.html", context)


@login_required
@user_passes_test(is_admin)
def audit_log_detail(request, pk):
    log_entry = get_object_or_404(AuditLog.objects.select_related("user"), pk=pk)

    before = {}
    after = {}
    for field, change in log_entry.changes.items():
        if isinstance(change, dict) and "old" in change and "new" in change:
            before[field] = change["old"]
            after[field] = change["new"]

    context = {
        "log_entry": log_entry,
        "before": before,
        "after": after,
    }
    return render(request, "audit/audit_detail.html", context)


@login_required
@user_passes_test(is_admin)
def audit_object_history(request):
    content_type = request.GET.get("content_type")
    object_id = request.GET.get("object_id")

    if not content_type or not object_id:
        return render(
            request,
            "audit/audit_list.html",
            {
                "page_obj": None,
                "error": "Both content_type and object_id are required.",
                "is_object_history": True,
            },
        )

    queryset = AuditLog.objects.select_related("user").filter(
        content_type__iexact=content_type, object_id=object_id
    )

    object_repr = ""
    if queryset.exists():
        object_repr = queryset.first().object_repr

    paginator = Paginator(queryset, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "is_object_history": True,
        "history_content_type": content_type,
        "history_object_id": object_id,
        "history_object_repr": object_repr,
    }
    return render(request, "audit/audit_list.html", context)
