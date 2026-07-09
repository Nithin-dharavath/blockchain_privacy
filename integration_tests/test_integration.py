import json
import io
import csv
from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.conf import settings
from privacy_platform.test_utils import (
    create_user, create_admin, create_technique, create_dataset_csv,
    create_experiment, create_completed_experiment, create_notification,
    create_report, create_report_schedule,
)
from experiments.models import Experiment, ExperimentComparison
from notifications.models import Notification
from audit.models import AuditLog
from admin_panel.models import ExperimentErrorReport
from reports.models import Report, ReportSchedule
from share.models import ExperimentShare

MOCK_RESULTS = {
    'privacy_score': 0.85,
    'accuracy': 0.92,
    'execution_time': 1.5,
    'throughput': 100.0,
    'anonymity_set_size': 10,
    'unlinkability_score': 0.9,
    'ring_size': 5,
    'successful_operations': 10,
    'total_operations': 10,
}


class FullExperimentFlowTest(TestCase):
    def setUp(self):
        self.user = create_user(username="flowuser", password="testpass123")
        self.admin = create_admin(username="flowadmin", password="admin123")
        self.technique = create_technique("ring_signature")

    def test_full_experiment_flow(self):
        self.client.login(username="flowuser", password="testpass123")

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["col1", "col2", "col3"])
        for i in range(10):
            writer.writerow([i, f"val_{i}", i * 1.5])
        csv_file = SimpleUploadedFile(
            "flow_test.csv",
            csv_buffer.getvalue().encode("utf-8"),
            content_type="text/csv",
        )

        upload_response = self.client.post(reverse("datasets:upload"), {
            "name": "Flow Test Dataset",
            "description": "Test dataset",
            "dataset_type": "custom",
            "file": csv_file,
            "is_anonymized": False,
        })
        self.assertEqual(upload_response.status_code, 302)

        from datasets.models import Dataset
        dataset = Dataset.objects.get(uploaded_by=self.user)

        self.client.logout()

        self.client.login(username="flowadmin", password="admin123")
        approve_response = self.client.post(
            reverse("admin_panel:approve_dataset", args=[dataset.pk]),
            {"action": "approve"},
        )
        self.assertIn(approve_response.status_code, [200, 302])
        dataset.refresh_from_db()
        self.assertEqual(dataset.status, "approved")

        self.client.logout()
        self.client.login(username="flowuser", password="testpass123")

        create_response = self.client.post(reverse("experiments:create"), {
            "name": "Flow Integration Exp",
            "description": "Integration test experiment",
            "dataset": dataset.pk,
            "privacy_technique": self.technique.pk,
            "configuration": '{"ring_size": 5}',
        })
        self.assertEqual(create_response.status_code, 302)

        experiment = Experiment.objects.get(user=self.user, name="Flow Integration Exp")
        self.assertEqual(experiment.status, "pending")

        with patch("experiments.views.run_ring_signature_experiment") as mock_run:
            mock_run.return_value = dict(MOCK_RESULTS)
            run_response = self.client.post(
                reverse("experiments:run", args=[experiment.pk])
            )
            self.assertEqual(run_response.status_code, 302)

        experiment.refresh_from_db()
        self.assertEqual(experiment.status, "completed")
        self.assertEqual(experiment.privacy_score, 0.85)
        self.assertEqual(experiment.accuracy, 0.92)

        notifications = Notification.objects.filter(
            recipient=self.user,
            verb="experiment_completed",
        )
        self.assertEqual(notifications.count(), 1)

        audit_logs = AuditLog.objects.filter(
            action_type="RUN",
        )
        self.assertGreaterEqual(audit_logs.count(), 1)


class ComparisonFlowTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(username="compuser", password="testpass123")
        cls.technique1 = create_technique("ring_signature", name="Ring Sig 1")
        cls.technique2 = create_technique("zkp", name="ZKP 1")
        cls.dataset1 = create_dataset_csv(cls.user, name="comp_ds1.csv", rows=10)
        cls.dataset2 = create_dataset_csv(cls.user, name="comp_ds2.csv", rows=10)
        cls.exp1 = create_completed_experiment(
            cls.user, cls.technique1, cls.dataset1,
            name="Comp Exp A", privacy_score=0.75, accuracy=0.80, execution_time=2.0,
        )
        cls.exp2 = create_completed_experiment(
            cls.user, cls.technique2, cls.dataset2,
            name="Comp Exp B", privacy_score=0.90, accuracy=0.95, execution_time=1.0,
        )

    def test_comparison_flow(self):
        self.client.force_login(self.user)

        create_response = self.client.post(reverse("experiments:compare"), {
            "name": "My Comparison",
            "description": "Comparing two techniques",
            "experiments": [self.exp1.pk, self.exp2.pk],
        })
        self.assertEqual(create_response.status_code, 302)

        comparison = ExperimentComparison.objects.get(user=self.user, name="My Comparison")
        self.assertEqual(comparison.experiments.count(), 2)

        detail_response = self.client.get(
            reverse("experiments:comparison_detail", args=[comparison.pk])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertIn("comparison_data", detail_response.context)
        self.assertIn("ranking_data", detail_response.context)
        self.assertIn("best_privacy_score", detail_response.context)

        self.assertEqual(
            detail_response.context["best_privacy_score"], 0.90
        )

        export_response = self.client.get(
            reverse("experiments:export_comparison", args=[comparison.pk]),
            {"format": "csv"},
        )
        self.assertEqual(export_response.status_code, 200)
        self.assertIn("text/csv", export_response["Content-Type"])


class AuditMiddlewareTest(TestCase):
    def setUp(self):
        self.user = create_user(username="auditmiduser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user, name="audit_mid.csv")

    def test_post_creates_audit_log(self):
        self.client.login(username="auditmiduser", password="testpass123")

        create_response = self.client.post(reverse("experiments:create"), {
            "name": "Audit Middleware Exp",
            "description": "Testing audit middleware",
            "dataset": self.dataset.pk,
            "privacy_technique": self.technique.pk,
            "configuration": '{"ring_size": 5}',
        })
        self.assertEqual(create_response.status_code, 302)

        experiment = Experiment.objects.get(name="Audit Middleware Exp")
        audit_log_mixin = AuditLog.objects.filter(
            action_type="CREATE",
            content_type="experiment",
            object_id=experiment.pk,
        ).first()
        self.assertIsNotNone(audit_log_mixin, "No AuditLog from AuditableMixin")
        self.assertEqual(audit_log_mixin.action_type, "CREATE")
        self.assertEqual(audit_log_mixin.object_id, experiment.pk)

        audit_log_mw = AuditLog.objects.filter(
            content_type="Experiment",
            request_method="POST",
            url__icontains="experiments/create",
        ).order_by("-id").first()
        self.assertIsNotNone(audit_log_mw, "No AuditLog from AuditMiddleware")
        self.assertEqual(audit_log_mw.object_id, 0)
        self.assertIsNotNone(audit_log_mw.ip_address)

    def test_get_does_not_create_audit_log(self):
        self.client.login(username="auditmiduser", password="testpass123")
        log_count_before = AuditLog.objects.count()
        self.client.get(reverse("experiments:list"))
        log_count_after = AuditLog.objects.count()
        self.assertEqual(log_count_after, log_count_before)


class ReportFlowTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(username="reportflowuser", password="testpass123")
        cls.technique = create_technique("ring_signature")
        cls.dataset = create_dataset_csv(cls.user, name="report_flow.csv", rows=10)
        cls.experiment = create_completed_experiment(
            cls.user, cls.technique, cls.dataset,
            name="Report Flow Exp",
            privacy_score=0.88, accuracy=0.91,
        )

    def test_report_generate_download_share_flow(self):
        self.client.login(username="reportflowuser", password="testpass123")

        with patch("reports.views.PDFReportGenerator") as mock_pdf:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = None
            mock_pdf.return_value = mock_instance

            generate_response = self.client.post(reverse("reports:generate"), {
                "title": "Integration Report",
                "report_type": "single",
                "file_format": "pdf",
                "experiments": [self.experiment.pk],
            })
            self.assertEqual(generate_response.status_code, 302)

        report = Report.objects.get(user=self.user, title="Integration Report")
        self.assertIsNotNone(report)
        self.assertEqual(report.report_type, "single")
        self.assertEqual(report.file_format, "pdf")

        detail_response = self.client.get(
            reverse("reports:detail", args=[report.pk])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertTemplateUsed(detail_response, "reports/report_detail.html")

        download_response = self.client.get(
            reverse("reports:download", args=[report.pk])
        )
        self.assertIn(download_response.status_code, [200, 302])

        share_response = self.client.post(
            reverse("reports:share_report", args=[report.pk]),
            {"permissions": "view_only"},
        )
        self.assertEqual(share_response.status_code, 200)
        share_data = json.loads(share_response.content)
        self.assertTrue(share_data.get("success"))
        self.assertIn("share_token", share_data)

        from reports.models import ReportShare
        report_share = ReportShare.objects.filter(report=report).first()
        self.assertIsNotNone(report_share)
        self.assertFalse(report_share.is_revoked)

        self.client.logout()

        shared_url = reverse("reports:shared_view", args=[report_share.share_token])
        shared_response = self.client.get(shared_url)
        self.assertEqual(shared_response.status_code, 200)


class RegistrationToResultsTest(TestCase):
    def test_registration_to_results_flow(self):
        technique = create_technique("ring_signature")

        register_response = self.client.post(reverse("accounts:register"), {
            "username": "newuser_integration",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "user_type": "researcher",
            "password": "testpass123",
            "password2": "testpass123",
        })
        self.assertEqual(register_response.status_code, 302)
        self.assertIn(reverse("accounts:login"), register_response.url)

        login_response = self.client.post(reverse("accounts:login"), {
            "username": "newuser_integration",
            "password": "testpass123",
        })
        self.assertEqual(login_response.status_code, 302)

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["col1", "col2", "col3"])
        for i in range(10):
            writer.writerow([i, f"val_{i}", i * 1.5])
        csv_file = SimpleUploadedFile(
            "reg_test.csv",
            csv_buffer.getvalue().encode("utf-8"),
            content_type="text/csv",
        )

        upload_response = self.client.post(reverse("datasets:upload"), {
            "name": "Reg Test Dataset",
            "description": "Test",
            "dataset_type": "custom",
            "file": csv_file,
            "is_anonymized": False,
        })
        self.assertEqual(upload_response.status_code, 302)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(username="newuser_integration")
        admin = create_admin(username="regadmin", password="admin123")

        from datasets.models import Dataset
        dataset = Dataset.objects.get(uploaded_by=user)

        self.client.logout()
        self.client.login(username="regadmin", password="admin123")
        self.client.post(
            reverse("admin_panel:approve_dataset", args=[dataset.pk]),
            {"action": "approve"},
        )
        dataset.refresh_from_db()
        self.assertEqual(dataset.status, "approved")

        self.client.logout()
        self.client.login(username="newuser_integration", password="testpass123")

        create_response = self.client.post(reverse("experiments:create"), {
            "name": "Reg Flow Exp",
            "description": "Registration flow experiment",
            "dataset": dataset.pk,
            "privacy_technique": technique.pk,
            "configuration": '{"ring_size": 5}',
        })
        self.assertEqual(create_response.status_code, 302)

        experiment = Experiment.objects.get(user=user, name="Reg Flow Exp")

        with patch("experiments.views.run_ring_signature_experiment") as mock_run:
            mock_run.return_value = dict(MOCK_RESULTS)
            run_response = self.client.post(
                reverse("experiments:run", args=[experiment.pk])
            )
            self.assertEqual(run_response.status_code, 302)

        experiment.refresh_from_db()
        self.assertEqual(experiment.status, "completed")

        detail_response = self.client.get(
            reverse("experiments:detail", args=[experiment.pk])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertIn(experiment.name, str(detail_response.content))


class ErrorHandlingTest(TestCase):
    def setUp(self):
        self.user = create_user(username="erroruser", password="testpass123")
        self.admin = create_admin(username="erroradmin", password="admin123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user, name="error_test.csv", rows=5)
        self.experiment = create_experiment(
            self.user, self.technique, self.dataset,
            name="Error Test Exp", configuration={"ring_size": 3},
        )

    def test_experiment_failure_and_resolve(self):
        self.client.login(username="erroruser", password="testpass123")

        with patch("experiments.views.run_ring_signature_experiment") as mock_run:
            mock_run.side_effect = RuntimeError("Simulated crypto failure")
            run_response = self.client.post(
                reverse("experiments:run", args=[self.experiment.pk])
            )
            self.assertEqual(run_response.status_code, 302)

        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.status, "failed")
        self.assertIn("Simulated crypto failure", self.experiment.error_message)

        error_report = ExperimentErrorReport.objects.filter(
            experiment=self.experiment
        ).first()
        self.assertIsNotNone(error_report)
        self.assertEqual(error_report.error_message, "Simulated crypto failure")
        self.assertFalse(error_report.resolved)

        notification = Notification.objects.filter(
            recipient=self.user,
            verb="experiment_failed",
        ).first()
        self.assertIsNotNone(notification)
        self.assertIn("Error Test Exp", notification.description)

        self.client.logout()
        self.client.login(username="erroradmin", password="admin123")

        resolve_response = self.client.post(
            reverse("admin_panel:error_report_resolve", args=[error_report.pk]),
            {"resolution_notes": "Simulated error, no action needed"},
        )
        self.assertIn(resolve_response.status_code, [200, 302])

        error_report.refresh_from_db()
        self.assertTrue(error_report.resolved)
        self.assertEqual(error_report.resolved_by, self.admin)
        self.assertIsNotNone(error_report.resolved_at)


class ScheduledReportsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(username="scheduser", password="testpass123")
        cls.technique = create_technique("ring_signature")
        cls.dataset = create_dataset_csv(cls.user, name="sched_ds.csv", rows=10)
        cls.experiment = create_completed_experiment(
            cls.user, cls.technique, cls.dataset,
            name="Scheduled Exp",
        )

    def test_process_scheduled_reports(self):
        schedule = create_report_schedule(
            self.user,
            experiments=[self.experiment],
        )
        schedule.next_run = timezone.now() - timedelta(hours=1)
        schedule.save()

        report_count_before = Report.objects.count()

        with patch("reports.management.commands.process_scheduled_reports.PDFReportGenerator") as mock_pdf:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = None
            mock_pdf.return_value = mock_instance

            out = io.StringIO()
            call_command("process_scheduled_reports", stdout=out)

        report_count_after = Report.objects.count()
        self.assertEqual(report_count_after, report_count_before + 1)

        report = Report.objects.filter(user=self.user).order_by("-created_at").first()
        self.assertIsNotNone(report)
        self.assertEqual(report.schedule, schedule)
        self.assertEqual(report.report_type, schedule.report_type)

        schedule.refresh_from_db()
        self.assertGreater(schedule.next_run, timezone.now() - timedelta(minutes=1))


class NotificationsTest(TestCase):
    def setUp(self):
        self.user = create_user(username="notifuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user, name="notif_ds.csv", rows=10)
        self.experiment = create_experiment(
            self.user, self.technique, self.dataset,
            name="Notif Test Exp", configuration={"ring_size": 5},
        )

    def test_notification_flow(self):
        self.client.login(username="notifuser", password="testpass123")

        with patch("experiments.views.run_ring_signature_experiment") as mock_run:
            mock_run.return_value = dict(MOCK_RESULTS)
            self.client.post(reverse("experiments:run", args=[self.experiment.pk]))

        notification = Notification.objects.filter(
            recipient=self.user,
            verb="experiment_completed",
        ).first()
        self.assertIsNotNone(notification)
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        self.assertIn("Notif Test Exp", notification.description)

        unread_response = self.client.get(reverse("notifications:unread_count"))
        self.assertEqual(unread_response.status_code, 200)
        data = json.loads(unread_response.content)
        self.assertGreaterEqual(data.get("unread_count", 0), 1)

        list_response = self.client.get(reverse("notifications:list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertIn(notification, list_response.context["page_obj"].object_list)

        mark_read_response = self.client.get(
            reverse("notifications:mark_read", args=[notification.pk])
        )
        self.assertEqual(mark_read_response.status_code, 200)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_mark_all_read(self):
        for i in range(3):
            create_notification(
                recipient=self.user,
                verb="experiment_completed",
                is_read=False,
            )

        self.client.force_login(self.user)
        mark_all_response = self.client.get(reverse("notifications:mark_all_read"))
        self.assertEqual(mark_all_response.status_code, 200)

        unread_count = Notification.objects.filter(
            recipient=self.user,
            is_read=False,
        ).count()
        self.assertEqual(unread_count, 0)
