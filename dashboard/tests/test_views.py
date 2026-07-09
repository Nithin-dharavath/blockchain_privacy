from django.test import TestCase
from django.urls import reverse
from privacy_platform.test_utils import (
    create_user, create_technique, create_dataset_csv,
    create_completed_experiment,
)


class HomeViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="dashuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)

    def test_home_requires_login(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertNotEqual(response.status_code, 200)

    def test_home_returns_200_for_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/home.html")

    def test_home_context_has_stats(self):
        create_completed_experiment(self.user, self.technique, self.dataset)
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:home"))
        self.assertIn("total_experiments", response.context)
        self.assertIn("completed_experiments", response.context)
        self.assertIn("total_datasets", response.context)
        self.assertIn("privacy_techniques", response.context)
        self.assertIn("recent_experiments", response.context)


class TechniquesOverviewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="techuser", password="testpass123")

    def test_techniques_requires_login(self):
        response = self.client.get(reverse("dashboard:techniques"))
        self.assertNotEqual(response.status_code, 200)

    def test_techniques_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:techniques"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/techniques_overview.html")

    def test_techniques_context_has_technique_stats(self):
        create_technique("ring_signature")
        create_technique("zkp")
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:techniques"))
        self.assertIn("technique_stats", response.context)


class HomeViewEmptyDashboardTest(TestCase):
    def setUp(self):
        self.user = create_user(username="emptydash", password="testpass123")

    def test_home_with_zero_experiments_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/home.html")

    def test_home_with_zero_experiments_has_zero_context(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.context["total_experiments"], 0)
        self.assertEqual(response.context["completed_experiments"], 0)
        self.assertEqual(response.context["total_datasets"], 0)
