from django.test import TestCase
from django.urls import reverse
from privacy_platform.test_utils import create_user, create_admin
from audit.models import AuditLog


class AuditLogListViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user(username="regular", password="testpass123")

    def test_list_redirects_non_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("audit:list"))
        self.assertNotEqual(response.status_code, 200)

    def test_list_returns_200_for_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("audit:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "audit/audit_list.html")

    def test_list_context_has_action_choices(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("audit:list"))
        self.assertIn("action_choices", response.context)

    def test_list_filters(self):
        AuditLog.objects.create(
            action_type="CREATE", content_type="Experiment",
            object_id=1, object_repr="Test",
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse("audit:list") + "?action_type=CREATE")
        self.assertEqual(response.status_code, 200)


class AuditLogDetailViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.log = AuditLog.objects.create(
            action_type="CREATE",
            content_type="Experiment",
            object_id=1,
            object_repr="Test Object",
            changes={"field": {"old": None, "new": "value"}},
        )

    def test_detail_returns_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("audit:detail", args=[self.log.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "audit/audit_detail.html")

    def test_detail_context(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("audit:detail", args=[self.log.pk]))
        self.assertIn("log_entry", response.context)
        self.assertIn("before", response.context)
        self.assertIn("after", response.context)


class AuditObjectHistoryViewTest(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_object_history_requires_both_params(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("audit:object_history"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.context)

    def test_object_history_with_params(self):
        AuditLog.objects.create(
            action_type="UPDATE", content_type="Experiment",
            object_id=42, object_repr="Test Exp",
        )
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("audit:object_history")
            + "?content_type=Experiment&object_id=42",
        )
        self.assertEqual(response.status_code, 200)
