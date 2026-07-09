from django.test import TestCase
from admin_panel.models import ExperimentErrorReport, SystemMetric, AdminNotification
from accounts.models import User
from privacy_tools.models import PrivacyTechnique
from experiments.models import Experiment
from datasets.models import Dataset
from django.core.files.uploadedfile import SimpleUploadedFile


class TestExperimentErrorReport(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="adminuser", password="pass"
        )
        technique = PrivacyTechnique.objects.create(
            name="ErrTech", technique_type="ring_signature",
            description="T", algorithm_details="T",
        )
        csv_file = SimpleUploadedFile(
            "err.csv", b"a,b\n1,2", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="ErrDataset", description="T",
            dataset_type="custom", file=csv_file,
            uploaded_by=self.user,
        )
        self.experiment = Experiment.objects.create(
            name="ErrExp", user=self.user,
            dataset=dataset, privacy_technique=technique,
        )
        self.report = ExperimentErrorReport.objects.create(
            experiment=self.experiment,
            technique=technique,
            error_message="Something went wrong",
        )

    def test_create(self):
        self.assertEqual(ExperimentErrorReport.objects.count(), 1)

    def test_resolve_workflow(self):
        self.assertFalse(self.report.resolved)
        self.report.resolved = True
        self.report.resolved_by = self.user
        self.report.resolution_notes = "Fixed"
        self.report.save()
        self.report.refresh_from_db()
        self.assertTrue(self.report.resolved)
        self.assertEqual(self.report.resolution_notes, "Fixed")


class TestSystemMetric(TestCase):
    def setUp(self):
        self.metric = SystemMetric.objects.create(
            metric_name="active_users",
            metric_value=42.0,
        )

    def test_create(self):
        self.assertEqual(SystemMetric.objects.count(), 1)

    def test_metric_name_choices(self):
        names = [c[0] for c in SystemMetric.METRIC_NAMES]
        expected = [
            "active_users", "experiments_per_hour",
            "avg_response_time", "error_rate",
        ]
        self.assertEqual(names, expected)


class TestAdminNotification(TestCase):
    def setUp(self):
        self.notification = AdminNotification.objects.create(
            message="Test notification",
            type="info",
        )

    def test_create(self):
        self.assertEqual(AdminNotification.objects.count(), 1)

    def test_mark_read(self):
        self.assertFalse(self.notification.is_read)
        self.notification.is_read = True
        self.notification.save()
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
