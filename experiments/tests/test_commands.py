import json
import os
import tempfile
from io import StringIO
from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django.db import connection
from experiments.models import Experiment, ExperimentComparison
from reports.models import Report
from audit.models import AuditLog
from admin_panel.models import SystemMetric
from privacy_platform.test_utils import (
    create_user, create_technique, create_dataset_csv,
    create_experiment, create_completed_experiment,
)


MOCK_RUNNER_RESULTS = {
    "privacy_score": 0.85,
    "accuracy": 0.92,
    "execution_time": 1.5,
    "throughput": 100.0,
    "anonymity_set_size": 10,
    "metrics": {"score": 0.85},
}


class RerunExperimentsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("rerunuser")
        cls.technique = create_technique("ring_signature")
        cls.dataset = create_dataset_csv(cls.user, rows=10)
        cls.exp = create_completed_experiment(
            cls.user, cls.technique, cls.dataset,
            privacy_score=0.5, accuracy=0.5,
        )

    @patch("experiments.experiment_runner.PrivacyExperimentRunner")
    def test_with_ids(self, mock_runner_cls):
        mock_runner = MagicMock()
        mock_runner.run.return_value = MOCK_RUNNER_RESULTS
        mock_runner_cls.return_value = mock_runner

        out = StringIO()
        call_command("rerun_experiments", f"--ids={self.exp.pk}", "--force", stdout=out)
        self.assertIn("Re-running experiment", out.getvalue())
        self.assertIn("Completed", out.getvalue())
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.privacy_score, 0.85)
        self.assertEqual(self.exp.status, "completed")

    def test_skip_running(self):
        self.exp.status = "running"
        self.exp.save()
        out = StringIO()
        call_command("rerun_experiments", f"--ids={self.exp.pk}", stdout=out)
        self.assertIn("Skipping", out.getvalue())

    def test_skip_completed_without_force(self):
        exp2 = create_completed_experiment(
            self.user, self.technique, self.dataset,
            name="SkipMe", privacy_score=0.5, accuracy=0.5,
        )
        out = StringIO()
        call_command("rerun_experiments", f"--ids={exp2.pk}", stdout=out)
        self.assertIn("already completed", out.getvalue())

    def test_invalid_ids(self):
        out = StringIO()
        call_command("rerun_experiments", "--ids=abc", stdout=out)
        self.assertIn("Invalid --ids format", out.getvalue())

    @patch("experiments.experiment_runner.PrivacyExperimentRunner")
    def test_failure_sets_failed(self, mock_runner_cls):
        mock_runner = MagicMock()
        mock_runner.run.side_effect = RuntimeError("Test failure")
        mock_runner_cls.return_value = mock_runner

        out = StringIO()
        call_command("rerun_experiments", f"--ids={self.exp.pk}", "--force", stdout=out)
        self.assertIn("failed", out.getvalue().lower())
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.status, "failed")
        self.assertEqual(self.exp.error_message, "Test failure")


class RerunAllReportTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("reportuser")
        cls.technique = create_technique("ring_signature")
        cls.dataset = create_dataset_csv(cls.user, rows=10)
        cls.exp = create_completed_experiment(
            cls.user, cls.technique, cls.dataset,
            privacy_score=0.5, accuracy=0.5,
        )

    @patch("experiments.experiment_runner.PrivacyExperimentRunner")
    def test_creates_csv(self, mock_runner_cls):
        mock_runner = MagicMock()
        mock_runner.run.return_value = MOCK_RUNNER_RESULTS
        mock_runner_cls.return_value = mock_runner

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", newline="") as f:
            tmpfile = f.name
        try:
            out = StringIO()
            call_command("rerun_all_report", f"--out={tmpfile}", "--force", stdout=out)
            self.assertIn("Wrote report to", out.getvalue())
            self.assertTrue(os.path.getsize(tmpfile) > 0)
        finally:
            if os.path.exists(tmpfile):
                os.remove(tmpfile)


class BackfillMetricsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("backfilluser")
        cls.technique = create_technique("ring_signature")
        cls.dataset = create_dataset_csv(cls.user, rows=10)
        cls.exp = create_experiment(
            cls.user, cls.technique, cls.dataset,
            status="completed",
            completed_at=timezone.now(),
            privacy_score=None,
            accuracy=None,
            metrics={
                "successful_operations": 90,
                "total_operations": 100,
                "ring_size": 5,
            },
        )

    def test_updates_null_metrics(self):
        out = StringIO()
        call_command("backfill_metrics", stdout=out)
        self.exp.refresh_from_db()
        self.assertIsNotNone(self.exp.accuracy)
        self.assertIsNotNone(self.exp.privacy_score)
        self.assertIn("Updated:", out.getvalue())


class FixAllAccuracyTest(TestCase):
    def test_fixes_null_accuracy(self):
        user = create_user("fixaccuser")
        technique = create_technique("ring_signature")
        dataset = create_dataset_csv(user, rows=5)
        exp = create_experiment(
            user, technique, dataset,
            status="completed",
            completed_at=timezone.now(),
            privacy_score=0.8, accuracy=None,
            metrics={"total_operations": 100, "successful_operations": 95},
        )
        out = StringIO()
        call_command("fix_all_accuracy", stdout=out)
        exp.refresh_from_db()
        self.assertEqual(exp.accuracy, 0.95)

    def test_skips_without_metrics(self):
        user = create_user("fixacc2")
        technique = create_technique("zkp")
        dataset = create_dataset_csv(user, rows=5)
        exp = create_experiment(
            user, technique, dataset,
            status="completed",
            completed_at=timezone.now(),
            privacy_score=0.8, accuracy=None,
        )
        out = StringIO()
        call_command("fix_all_accuracy", stdout=out)
        exp.refresh_from_db()
        self.assertIsNone(exp.accuracy)


class AuditConsistencyCheckTest(TestCase):
    def test_no_orphans(self):
        out = StringIO()
        call_command("audit_consistency_check", stdout=out)
        self.assertIn("All FK relationships intact", out.getvalue())

    def _create_orphan_experiment(self):
        user = create_user("orphanhelper")
        technique = create_technique("zkp")
        dataset = create_dataset_csv(user, rows=5)
        exp = create_experiment(user, technique, dataset, name="Orphaned")
        exp_id = exp.pk
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS=0")
            Experiment.objects.filter(pk=exp_id).update(user_id=99999)
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        return exp_id

    def test_detects_orphans(self):
        self._create_orphan_experiment()
        out = StringIO()
        call_command("audit_consistency_check", stdout=out)
        self.assertIn("orphaned", out.getvalue().lower())

    def test_fix_deletes_orphans(self):
        exp_id = self._create_orphan_experiment()
        out = StringIO()
        call_command("audit_consistency_check", "--fix", stdout=out)
        self.assertEqual(Experiment.objects.filter(pk=exp_id).count(), 0)


class GenerateMissingReportsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("genrepuser")
        cls.technique = create_technique("ring_signature")
        cls.dataset = create_dataset_csv(cls.user, rows=5)
        cls.exp = create_completed_experiment(cls.user, cls.technique, cls.dataset)

    def test_dry_run(self):
        out = StringIO()
        call_command("generate_missing_reports", "--dry-run", stdout=out)
        self.assertEqual(Report.objects.count(), 0)
        self.assertIn("DRY RUN", out.getvalue())

    def test_creates_reports(self):
        out = StringIO()
        call_command("generate_missing_reports", stdout=out)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.first()
        self.assertEqual(report.user, self.user)
        content = json.loads(report.content)
        self.assertIn("executive_summary", content)

    def test_skips_with_report(self):
        Report.objects.create(
            title="Existing",
            user=self.user,
            report_type="single",
            file_format="json",
            content="{}",
        ).experiments.set([self.exp])
        out = StringIO()
        call_command("generate_missing_reports", stdout=out)
        self.assertEqual(Report.objects.count(), 1)


class ReportDataFixTest(TestCase):
    def test_fixes_accuracy(self):
        user = create_user("rptfixuser")
        technique = create_technique("ring_signature")
        dataset = create_dataset_csv(user, rows=5)
        exp = create_experiment(
            user, technique, dataset,
            status="completed",
            completed_at=timezone.now(),
            accuracy=None,
            metrics={"total_operations": 100, "successful_operations": 90},
        )
        out = StringIO()
        call_command("report_data_fix", "--fix-accuracy", stdout=out)
        exp.refresh_from_db()
        self.assertEqual(exp.accuracy, 0.9)

    def test_fixes_summaries(self):
        user = create_user("sumfixuser")
        technique = create_technique("zkp")
        dataset = create_dataset_csv(user, rows=5)
        exp = create_completed_experiment(user, technique, dataset)
        Report.objects.create(
            title="No Summary",
            user=user,
            report_type="single",
            file_format="json",
            content=json.dumps({"executive_summary": ""}),
            summary="",
        ).experiments.set([exp])
        out = StringIO()
        call_command("report_data_fix", "--fix-summaries", stdout=out)
        report = Report.objects.first()
        self.assertNotEqual(report.summary, "")


class SyncAuditMetricsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("syncuser")
        cls.technique = create_technique("ring_signature")
        cls.dataset = create_dataset_csv(cls.user, rows=5)
        create_completed_experiment(cls.user, cls.technique, cls.dataset)

    def test_dry_run(self):
        out = StringIO()
        call_command("sync_audit_metrics", "--dry-run", stdout=out)
        self.assertEqual(SystemMetric.objects.count(), 0)

    def test_stores_metrics(self):
        out = StringIO()
        call_command("sync_audit_metrics", stdout=out)
        self.assertEqual(SystemMetric.objects.count(), 9)
        names = list(SystemMetric.objects.values_list("metric_name", flat=True))
        self.assertIn("experiment_count", names)
        self.assertIn("avg_privacy_score", names)
