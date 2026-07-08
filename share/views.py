import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.urls import reverse

from experiments.models import Experiment
from .models import ExperimentShare
from audit.models import AuditLog


@login_required
def create_share_link(request, experiment_id):
    """Create a shareable link for an experiment result."""
    experiment = get_object_or_404(Experiment, pk=experiment_id, user=request.user)

    if request.method == "POST":
        permissions = request.POST.get("permissions", "view_only")
        expires_days = request.POST.get("expires_days", "")
        max_access = request.POST.get("max_access", "")

        kwargs = {
            "experiment": experiment,
            "shared_by": request.user,
            "permissions": permissions,
        }
        if expires_days:
            try:
                kwargs["expires_at"] = timezone.now() + timezone.timedelta(days=int(expires_days))
            except (ValueError, TypeError):
                pass
        if max_access:
            try:
                kwargs["max_access_count"] = int(max_access)
            except (ValueError, TypeError):
                pass

        share = ExperimentShare.objects.create(**kwargs)
        share_url = request.build_absolute_uri(
            reverse("share:experiment_shared_view", kwargs={"token": share.share_token})
        )

        AuditLog.objects.create(
            user=request.user,
            action_type="CREATE",
            content_type="Experiment",
            object_id=experiment.id,
            object_repr=f"Share link created for {experiment.name}",
        )

        messages.success(request, "Share link created!")
        return render(request, "share/experiment_view.html", {
            "share": share,
            "share_url": share_url,
            "experiment": experiment,
            "created": True,
        })

    return render(request, "share/experiment_view.html", {
        "experiment": experiment,
        "creating": True,
    })


def shared_experiment_view(request, token):
    """Public view for a shared experiment result."""
    share = get_object_or_404(ExperimentShare, share_token=token)

    if not share.is_active():
        return render(request, "share/experiment_view.html", {
            "error": "This share link has expired or been revoked.",
            "share": share,
        })

    experiment = share.experiment
    share.record_access()

    AuditLog.objects.create(
        action_type="VIEW",
        content_type="Experiment",
        object_id=experiment.id,
        object_repr=f"Shared experiment viewed: {experiment.name}",
    )

    can_download = share.permissions == "download"
    context = {
        "share": share,
        "experiment": experiment,
        "can_download": can_download,
        "shared": True,
    }
    return render(request, "share/experiment_view.html", context)


@login_required
def manage_links(request, experiment_id):
    """List and manage share links for an experiment."""
    experiment = get_object_or_404(Experiment, pk=experiment_id, user=request.user)
    links = ExperimentShare.objects.filter(experiment=experiment).order_by("-created_at")
    return render(request, "share/experiment_view.html", {
        "experiment": experiment,
        "links": links,
        "managing": True,
    })


@login_required
def revoke_link(request, share_pk):
    """Revoke a share link."""
    share = get_object_or_404(ExperimentShare, pk=share_pk, shared_by=request.user)
    share.is_revoked = True
    share.save(update_fields=["is_revoked"])

    AuditLog.objects.create(
        user=request.user,
        action_type="UPDATE",
        content_type="ExperimentShare",
        object_id=share.pk,
        object_repr=f"Share link revoked for {share.experiment.name}",
    )

    messages.success(request, "Share link revoked.")
    return redirect("share:manage_experiment_links", experiment_id=share.experiment_id)
