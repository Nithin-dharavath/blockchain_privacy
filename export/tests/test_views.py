from django.test import TestCase
from django.urls import reverse
from privacy_platform.test_utils import (
    create_user, create_admin, create_technique,
    create_dataset_csv, create_completed_experiment,
)


class ExportExperimentsViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="expuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.experiment = create_completed_experiment(
            self.user, self.technique, self.dataset,
        )

    def test_export_requires_login(self):
        response = self.client.get(reverse("export:export_experiments"))
        self.assertNotEqual(response.status_code, 200)

    def test_export_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("export:export_experiments"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "export/export_page.html")

    def test_export_csv_download(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("export:export_experiments") + "?action=download&format=csv",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])

    def test_export_json_download(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("export:export_experiments") + "?action=download&format=json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response["Content-Type"])

    def test_export_filters_by_technique(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("export:export_experiments")
            + "?technique=ring_signature&action=download&format=csv",
        )
        self.assertEqual(response.status_code, 200)

    def test_export_admin_sees_all(self):
        admin = create_admin()
        create_completed_experiment(admin, self.technique, self.dataset,
                                    name="Admin Exp")
        self.client.force_login(admin)
        response = self.client.get(
            reverse("export:export_experiments") + "?action=download&format=csv",
        )
        self.assertEqual(response.status_code, 200)


class ExportReportsViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="repexpuser", password="testpass123")

    def test_export_reports_requires_login(self):
        response = self.client.get(reverse("export:export_reports"))
        self.assertNotEqual(response.status_code, 200)

    def test_export_reports_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("export:export_reports"))
        self.assertEqual(response.status_code, 200)
