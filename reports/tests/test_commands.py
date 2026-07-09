from io import StringIO
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from reports.models import ReportTemplate, ReportSchedule, Report
from privacy_platform.test_utils import create_user, create_technique, create_dataset_csv, create_completed_experiment


class SeedReportTemplatesTest(TestCase):
    def test_creates_3_templates(self):
        out = StringIO()
        call_command("seed_report_templates", stdout=out)
        self.assertEqual(ReportTemplate.objects.count(), 3)
        self.assertIn("Created: Full Report", out.getvalue())

    def test_idempotent(self):
        call_command("seed_report_templates", stdout=StringIO())
        out = StringIO()
        call_command("seed_report_templates", stdout=out)
        self.assertEqual(ReportTemplate.objects.count(), 3)
        self.assertIn("Already exists", out.getvalue())


class ProcessScheduledReportsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("scheduser")
        cls.technique = create_technique("ring_signature")
        cls.dataset = create_dataset_csv(cls.user, rows=5)
        cls.exp = create_completed_experiment(cls.user, cls.technique, cls.dataset)

    @patch("reports.management.commands.process_scheduled_reports.generate_report_file")
    def test_no_due_schedules(self, mock_gen):
        out = StringIO()
        call_command("process_scheduled_reports", stdout=out)
        self.assertIn("No scheduled reports due", out.getvalue())
        mock_gen.assert_not_called()

    @patch("reports.management.commands.process_scheduled_reports.generate_report_file")
    def test_generates_report_for_due_schedule(self, mock_gen):
        mock_gen.return_value = None
        schedule = ReportSchedule.objects.create(
            user=self.user,
            name="Daily Report",
            report_type="single",
            file_format="json",
            schedule_frequency="daily",
            next_run=timezone.now() - timezone.timedelta(hours=1),
        )
        schedule.experiments.set([self.exp])
        out = StringIO()
        call_command("process_scheduled_reports", stdout=out)
        self.assertEqual(Report.objects.count(), 1)
        schedule.refresh_from_db()
        self.assertIsNotNone(schedule.last_run)
        self.assertGreater(schedule.next_run, schedule.last_run)
        mock_gen.assert_called_once()

    @patch("reports.management.commands.process_scheduled_reports.generate_report_file")
    def test_skips_schedule_with_no_experiments(self, mock_gen):
        ReportSchedule.objects.create(
            user=self.user,
            name="Empty Report",
            report_type="single",
            file_format="json",
            schedule_frequency="daily",
            next_run=timezone.now() - timezone.timedelta(hours=1),
        )
        out = StringIO()
        call_command("process_scheduled_reports", stdout=out)
        self.assertEqual(Report.objects.count(), 0)
        mock_gen.assert_not_called()
