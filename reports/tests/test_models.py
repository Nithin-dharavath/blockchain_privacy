from django.test import TestCase
from reports.models import ReportTemplate, Report, ReportSchedule, ReportShare
from accounts.models import User
from experiments.models import Experiment
from privacy_tools.models import PrivacyTechnique
from datasets.models import Dataset
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import datetime, timedelta


class TestReportTemplate(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="templateuser", password="pass"
        )
        self.template = ReportTemplate.objects.create(
            name="Standard Report",
            description="A standard template",
            user=self.user,
        )

    def test_create(self):
        self.assertEqual(ReportTemplate.objects.count(), 1)

    def test_is_public_default(self):
        self.assertFalse(self.template.is_public)


class TestReport(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reportuser", password="pass"
        )
        technique = PrivacyTechnique.objects.create(
            name="RepTech", technique_type="smpc",
            description="T", algorithm_details="T",
        )
        csv_file = SimpleUploadedFile(
            "rep.csv", b"a,b\n1,2", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="RepDataset", description="T",
            dataset_type="custom", file=csv_file,
            uploaded_by=self.user,
        )
        self.experiment = Experiment.objects.create(
            name="RepExp", user=self.user,
            dataset=dataset, privacy_technique=technique,
        )
        self.report = Report.objects.create(
            title="Test Report",
            report_type="single",
            user=self.user,
            content="Report content here",
        )
        self.report.experiments.add(self.experiment)

    def test_create(self):
        self.assertEqual(Report.objects.count(), 1)

    def test_report_types(self):
        types = [c[0] for c in Report.REPORT_TYPE_CHOICES]
        self.assertIn("single", types)
        self.assertIn("comparison", types)
        self.assertIn("summary", types)

    def test_file_field(self):
        self.assertIsNone(self.report.file.name)


class TestReportSchedule(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="scheduleuser", password="pass"
        )
        self.schedule = ReportSchedule.objects.create(
            user=self.user,
            name="Daily Report",
            report_type="single",
            schedule_frequency="daily",
        )

    def test_create(self):
        self.assertEqual(ReportSchedule.objects.count(), 1)

    def test_compute_next_run_daily(self):
        next_run = self.schedule.compute_next_run()
        self.assertGreater(next_run, datetime.now())

    def test_compute_next_run_weekly(self):
        self.schedule.schedule_frequency = "weekly"
        self.schedule.schedule_day = 0
        next_run = self.schedule.compute_next_run()
        self.assertGreater(next_run, datetime.now())

    def test_compute_next_run_monthly(self):
        self.schedule.schedule_frequency = "monthly"
        self.schedule.schedule_day = 15
        next_run = self.schedule.compute_next_run()
        self.assertGreater(next_run, datetime.now())


class TestReportShare(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="shareuser", password="pass"
        )
        technique = PrivacyTechnique.objects.create(
            name="ShareTech", technique_type="mixer",
            description="T", algorithm_details="T",
        )
        csv_file = SimpleUploadedFile(
            "share.csv", b"a,b\n1,2", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="ShareDataset", description="T",
            dataset_type="custom", file=csv_file,
            uploaded_by=self.user,
        )
        self.experiment = Experiment.objects.create(
            name="ShareExp", user=self.user,
            dataset=dataset, privacy_technique=technique,
        )
        self.report = Report.objects.create(
            title="Shared Report",
            report_type="single",
            user=self.user,
            content="Content",
        )
        self.report.experiments.add(self.experiment)
        self.share = ReportShare.objects.create(
            report=self.report,
            shared_by=self.user,
        )

    def test_create(self):
        self.assertEqual(ReportShare.objects.count(), 1)

    def test_unique_token(self):
        self.assertIsNotNone(self.share.share_token)

    def test_is_expired(self):
        self.assertFalse(self.share.is_expired())
        self.share.expires_at = datetime.now() - timedelta(days=1)
        self.assertTrue(self.share.is_expired())

    def test_is_active(self):
        self.assertTrue(self.share.is_active())
        self.share.is_revoked = True
        self.assertFalse(self.share.is_active())

    def test_record_access(self):
        count_before = self.share.access_count
        self.share.record_access()
        self.share.refresh_from_db()
        self.assertEqual(self.share.access_count, count_before + 1)

    def test_revoked_inactive(self):
        self.share.is_revoked = True
        self.share.save()
        self.assertFalse(self.share.is_active())
