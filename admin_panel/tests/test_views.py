from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from privacy_platform.test_utils import (
    create_user, create_admin, create_technique, create_dataset_csv,
    create_experiment,
)
from admin_panel.models import AdminNotification, SystemMetric, ExperimentErrorReport
from audit.models import AuditLog
from datasets.models import Dataset


class AdminDashboardViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user(username="regular", password="testpass123")

    def test_dashboard_redirects_non_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("admin_panel:dashboard"))
        self.assertNotEqual(response.status_code, 200)

    def test_dashboard_returns_200_for_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_panel/dashboard.html")


class RegularUserBlockedFromAdminTest(TestCase):
    def setUp(self):
        self.user = create_user(username="regularuser", password="testpass123")
        self.admin = create_admin()

    def _assert_blocked(self, url_name, *args):
        self.client.force_login(self.user)
        response = self.client.get(reverse(url_name, args=args))
        self.assertNotEqual(response.status_code, 200,
                            f"Regular user should be blocked from {url_name}")

    def test_regular_user_blocked_from_manage_users(self):
        self._assert_blocked("admin_panel:manage_users")

    def test_regular_user_blocked_from_manage_datasets(self):
        self._assert_blocked("admin_panel:manage_datasets")

    def test_regular_user_blocked_from_manage_techniques(self):
        self._assert_blocked("admin_panel:manage_techniques")

    def test_regular_user_blocked_from_audit_logs(self):
        self._assert_blocked("admin_panel:audit_logs")

    def test_regular_user_blocked_from_notifications(self):
        self._assert_blocked("admin_panel:notifications")

    def test_regular_user_blocked_from_system_reports(self):
        self._assert_blocked("admin_panel:system_reports")

    def test_regular_user_blocked_from_error_reports(self):
        self._assert_blocked("admin_panel:error_reports")

    def test_dashboard_context(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:dashboard"))
        self.assertIn("total_users", response.context)
        self.assertIn("total_experiments", response.context)
        self.assertIn("total_datasets", response.context)


class ManageUsersViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user(username="regular", password="testpass123")

    def test_manage_users_admin_only(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("admin_panel:manage_users"))
        self.assertNotEqual(response.status_code, 200)

    def test_manage_users_returns_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:manage_users"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_panel/manage_users.html")

    def test_manage_users_search(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:manage_users") + "?search=admin")
        self.assertEqual(response.status_code, 200)


class ToggleUserApprovalViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.target = create_user(username="toggleme", password="testpass123")

    def test_toggle_user(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("admin_panel:toggle_user", args=[self.target.pk]))
        self.assertRedirects(response, reverse("admin_panel:manage_users"))
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_approved)


class ManageDatasetsViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user(username="dsowner", password="testpass123")
        self.dataset = create_dataset_csv(self.user)

    def test_manage_datasets_returns_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:manage_datasets"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_panel/manage_datasets.html")

    def test_manage_datasets_filters_by_status(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:manage_datasets") + "?status=pending")
        self.assertEqual(response.status_code, 200)


class ApproveDatasetViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user(username="dsowner2", password="testpass123")
        self.dataset = create_dataset_csv(self.user, status="pending")

    def test_approve_dataset(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_panel:approve_dataset", args=[self.dataset.pk]),
            {"action": "approve"},
        )
        self.assertRedirects(response, reverse("admin_panel:manage_datasets"))
        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.status, "approved")

    def test_reject_dataset(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_panel:approve_dataset", args=[self.dataset.pk]),
            {"action": "reject"},
        )
        self.assertRedirects(response, reverse("admin_panel:manage_datasets"))
        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.status, "rejected")


class ManageTechniquesViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_manage_techniques_returns_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:manage_techniques"))
        self.assertEqual(response.status_code, 200)


class AddTechniqueViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_add_technique_get(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:add_technique"))
        self.assertEqual(response.status_code, 200)

    def test_add_technique_post(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("admin_panel:add_technique"), {
            "name": "New Tech",
            "technique_type": "zkp",
            "description": "Test",
            "algorithm_details": "Details",
            "parameters": '{"k": 1}',
            "security_level": 5,
        })
        self.assertRedirects(response, reverse("admin_panel:manage_techniques"))


class EditTechniqueViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.technique = create_technique("ring_signature")

    def test_edit_technique_get(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_panel:edit_technique", args=[self.technique.pk]),
        )
        self.assertEqual(response.status_code, 200)

    def test_edit_technique_post(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_panel:edit_technique", args=[self.technique.pk]),
            {
                "name": "Updated Tech",
                "technique_type": "ring_signature",
                "description": "Updated",
                "algorithm_details": "Details",
                "parameters": '{"k": 2}',
                "security_level": 7,
            },
        )
        self.assertRedirects(response, reverse("admin_panel:manage_techniques"))


class ToggleTechniqueViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.technique = create_technique("ring_signature")

    def test_toggle_technique(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_panel:toggle_technique", args=[self.technique.pk]),
        )
        self.assertRedirects(response, reverse("admin_panel:manage_techniques"))
        self.technique.refresh_from_db()
        self.assertFalse(self.technique.is_active)


class SystemReportsViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_system_reports_returns_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:system_reports"))
        self.assertEqual(response.status_code, 200)


class AdminAuditLogsViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_admin_audit_logs_returns_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:audit_logs"))
        self.assertEqual(response.status_code, 200)

    def test_admin_audit_logs_filters(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_panel:audit_logs") + "?action_type=CREATE",
        )
        self.assertEqual(response.status_code, 200)


class AdminAuditUserViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.target = create_user(username="audituser", password="testpass123")

    def test_admin_audit_user_returns_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_panel:audit_user", args=[self.target.pk]),
        )
        self.assertEqual(response.status_code, 200)


class AdminNotificationsViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_admin_notifications_returns_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:notifications"))
        self.assertEqual(response.status_code, 200)

    def test_mark_all_read(self):
        AdminNotification.objects.create(message="Test notification")
        self.client.force_login(self.admin)
        response = self.client.post(reverse("admin_panel:notifications"),
                                    {"action": "mark_all_read"})
        self.assertRedirects(response, reverse("admin_panel:notifications"))
        self.assertEqual(AdminNotification.objects.filter(is_read=False).count(), 0)


class MarkNotificationReadViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.notification = AdminNotification.objects.create(message="Test")

    def test_mark_notification_read(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_panel:mark_notification_read", args=[self.notification.pk]),
        )
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)


class MarkAllNotificationsReadViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_mark_all_read(self):
        AdminNotification.objects.create(message="N1")
        AdminNotification.objects.create(message="N2")
        self.client.force_login(self.admin)
        response = self.client.post(reverse("admin_panel:mark_all_notifications_read"))
        self.assertRedirects(response, reverse("admin_panel:notifications"))
        self.assertEqual(AdminNotification.objects.filter(is_read=False).count(), 0)


class UnreadNotificationsCountViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_unread_count_returns_json(self):
        AdminNotification.objects.create(message="Test")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:unread_notifications_count"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("count", data)
        self.assertIn("notifications", data)


class SystemMetricTrendsViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_metric_trends_returns_json(self):
        SystemMetric.objects.create(metric_name="active_users", metric_value=10.0)
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_panel:system_metric_trends") + "?metric=active_users&days=30",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("labels", data)
        self.assertIn("values", data)


class ErrorReportsViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.tech = create_technique("ring_signature")

    def test_error_reports_list_returns_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_panel:error_reports"))
        self.assertEqual(response.status_code, 200)

    def test_error_reports_filter_unresolved(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_panel:error_reports") + "?resolved=unresolved",
        )
        self.assertEqual(response.status_code, 200)


class ErrorReportResolveViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.tech = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.admin)
        self.exp = create_experiment(self.admin, self.tech, self.dataset)
        self.report = ExperimentErrorReport.objects.create(
            experiment=self.exp, technique=self.tech,
            error_message="Test error",
        )

    def test_resolve_error_report(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_panel:error_report_resolve", args=[self.report.pk]),
            {"resolution_notes": "Fixed"},
        )
        self.assertRedirects(response, reverse("admin_panel:error_reports"))
        self.report.refresh_from_db()
        self.assertTrue(self.report.resolved)


class AdminAuditObjectViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_audit_object_view(self):
        AuditLog.objects.create(
            action_type="CREATE", content_type="Experiment",
            object_id=1, object_repr="Test",
        )
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_panel:audit_object", args=["Experiment", 1]),
        )
        self.assertEqual(response.status_code, 200)
