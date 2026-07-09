import io
import csv
import json
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
from privacy_tools.models import PrivacyTechnique
from datasets.models import Dataset
from experiments.models import Experiment, ExperimentComparison
from reports.models import Report, ReportTemplate, ReportSchedule, ReportShare
from notifications.models import Notification

User = get_user_model()


def create_user(username="testuser", password="testpass123", user_type="researcher", **kwargs):
    kwargs.setdefault("email", f"{username}@example.com")
    kwargs.setdefault("first_name", "Test")
    kwargs.setdefault("last_name", "User")
    user = User.objects.create_user(
        username=username,
        password=password,
        user_type=user_type,
        **kwargs,
    )
    return user


def create_admin(username="admin", password="admin123", **kwargs):
    kwargs.setdefault("email", "admin@example.com")
    user = User.objects.create_superuser(
        username=username,
        password=password,
        **kwargs,
    )
    user.user_type = "admin"
    user.save(update_fields=["user_type"])
    return user


def create_technique(technique_type="ring_signature", name=None, **kwargs):
    if name is None:
        name = technique_type.replace("_", " ").title()
    defaults = {
        "description": f"Test {name}",
        "algorithm_details": "Test algorithm details",
        "parameters": {"key": "value"},
        "is_active": True,
        "complexity": "O(n)",
        "security_level": 5,
    }
    defaults.update(kwargs)
    technique, _ = PrivacyTechnique.objects.get_or_create(
        name=name,
        technique_type=technique_type,
        defaults=defaults,
    )
    return technique


def create_dataset_csv(uploaded_by, name="test_dataset.csv", rows=10, status="approved"):
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["col1", "col2", "col3"])
    for i in range(rows):
        writer.writerow([i, f"val_{i}", i * 1.5])
    csv_file = SimpleUploadedFile(
        name,
        csv_buffer.getvalue().encode("utf-8"),
        content_type="text/csv",
    )
    dataset = Dataset.objects.create(
        name=name.replace(".csv", ""),
        description="Test dataset",
        dataset_type="custom",
        file=csv_file,
        uploaded_by=uploaded_by,
        status=status,
        row_count=rows,
        column_count=3,
        file_size=len(csv_buffer.getvalue()),
    )
    return dataset


def create_experiment(user, technique, dataset, status="pending", **kwargs):
    defaults = {
        "name": f"Experiment {technique.name}",
        "description": "Test experiment",
        "configuration": {"param1": "value1"},
        "status": status,
    }
    defaults.update(kwargs)
    exp = Experiment.objects.create(
        user=user,
        privacy_technique=technique,
        dataset=dataset,
        **defaults,
    )
    return exp


def create_completed_experiment(user, technique, dataset, **kwargs):
    kwargs.setdefault("privacy_score", 0.85)
    kwargs.setdefault("accuracy", 0.92)
    kwargs.setdefault("execution_time", 1.5)
    kwargs.setdefault("throughput", 100.0)
    kwargs.setdefault("anonymity_set_size", 10)
    kwargs.setdefault("metrics", {"score": 0.85})
    return create_experiment(
        user, technique, dataset,
        status="completed",
        completed_at=timezone.now(),
        **kwargs,
    )


def create_notification(recipient, verb="experiment_completed", is_read=False):
    n = Notification.objects.create(
        recipient=recipient,
        verb=verb,
        description=f"Test notification for {recipient.username}",
        action_url="/test/",
        is_read=is_read,
    )
    return n


def create_report(user, experiments=None, report_type="single", file_format="pdf"):
    if experiments is None:
        experiments = []
    report = Report.objects.create(
        title=f"Test Report for {user.username}",
        report_type=report_type,
        user=user,
        content=json.dumps({"summary": "test"}),
        summary="Test summary",
        file_format=file_format,
    )
    if experiments:
        report.experiments.set(experiments)
    return report


def create_report_template(user=None, is_public=True):
    return ReportTemplate.objects.create(
        name="Test Template",
        description="Test description",
        is_public=is_public,
        user=user,
        sections=["summary", "results"],
        layout={"header_text": "Test"},
    )


def create_report_schedule(user, experiments=None):
    if experiments is None:
        experiments = []
    schedule = ReportSchedule.objects.create(
        user=user,
        name="Test Schedule",
        report_type="summary",
        file_format="pdf",
        schedule_frequency="daily",
        next_run=timezone.now() + timedelta(days=1),
    )
    if experiments:
        schedule.experiments.set(experiments)
    return schedule


def create_experiment_share(experiment, shared_by, permissions="view_only"):
    from share.models import ExperimentShare
    return ExperimentShare.objects.create(
        experiment=experiment,
        shared_by=shared_by,
        permissions=permissions,
    )


def create_report_share(report, shared_by):
    return ReportShare.objects.create(
        report=report,
        shared_by=shared_by,
    )
