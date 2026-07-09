import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from privacy_platform.test_utils import (
    create_user, create_technique, create_dataset_csv,
    create_experiment, create_completed_experiment,
)
from experiments.models import Experiment, ExperimentComparison


class ExperimentListViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="explistuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)

    def test_list_requires_login(self):
        response = self.client.get(reverse("experiments:list"))
        self.assertNotEqual(response.status_code, 200)

    def test_list_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("experiments:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experiments/experiment_list.html")

    def test_list_filters_by_status(self):
        create_experiment(self.user, self.technique, self.dataset, status="completed",
                          name="Completed Exp")
        create_experiment(self.user, self.technique, self.dataset, status="pending",
                          name="Pending Exp")
        self.client.force_login(self.user)
        response = self.client.get(reverse("experiments:list") + "?status=completed")
        self.assertEqual(len(response.context["experiments"]), 1)


class ResultsDashboardViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="resultsuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)

    def test_results_requires_login(self):
        response = self.client.get(reverse("experiments:results"))
        self.assertNotEqual(response.status_code, 200)

    def test_results_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("experiments:results"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experiments/results_dashboard.html")

    def test_results_context_has_stats(self):
        create_completed_experiment(self.user, self.technique, self.dataset)
        self.client.force_login(self.user)
        response = self.client.get(reverse("experiments:results"))
        self.assertIn("stats", response.context)


class ExperimentCreateViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="createexpuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)

    def test_create_requires_login(self):
        response = self.client.get(reverse("experiments:create"))
        self.assertNotEqual(response.status_code, 200)

    def test_get_create_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("experiments:create"))
        self.assertEqual(response.status_code, 200)

    def test_post_create_creates_experiment(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("experiments:create"), {
            "name": "New Test Exp",
            "description": "Test",
            "dataset": self.dataset.pk,
            "privacy_technique": self.technique.pk,
            "configuration": '{"ring_size": 5}',
        })
        exp = Experiment.objects.get(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("experiments:run", args=[exp.pk]), response.url)


class ExperimentDetailViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="detexpuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.experiment = create_completed_experiment(
            self.user, self.technique, self.dataset,
        )

    def test_detail_requires_login(self):
        response = self.client.get(reverse("experiments:detail", args=[self.experiment.pk]))
        self.assertNotEqual(response.status_code, 200)

    def test_detail_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("experiments:detail", args=[self.experiment.pk]))
        self.assertEqual(response.status_code, 200)

    def test_detail_404_for_wrong_user(self):
        other = create_user(username="otherdet", password="testpass123")
        self.client.force_login(other)
        response = self.client.get(reverse("experiments:detail", args=[self.experiment.pk]))
        self.assertEqual(response.status_code, 404)


class ExperimentExportViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="exportexpuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.experiment = create_completed_experiment(
            self.user, self.technique, self.dataset,
        )

    def test_export_requires_login(self):
        response = self.client.get(reverse("experiments:export", args=[self.experiment.pk]))
        self.assertNotEqual(response.status_code, 200)

    def test_export_json_returns_json(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("experiments:export", args=[self.experiment.pk]) + "?format=json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response["Content-Type"])

    def test_export_csv_returns_csv(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("experiments:export", args=[self.experiment.pk]) + "?format=csv",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])


class ExperimentRunViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="runexpuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.experiment = create_experiment(self.user, self.technique, self.dataset)

    def test_run_requires_login(self):
        response = self.client.post(reverse("experiments:run", args=[self.experiment.pk]))
        self.assertNotEqual(response.status_code, 200)

    @patch("experiments.views.run_ring_signature_experiment")
    def test_run_completes_experiment(self, mock_run):
        mock_run.return_value = {
            "privacy_score": 0.8, "accuracy": 0.9,
            "throughput": 50.0, "anonymity_set_size": 5,
        }
        self.client.force_login(self.user)
        response = self.client.post(reverse("experiments:run", args=[self.experiment.pk]))
        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.status, "completed")
        self.assertRedirects(response, reverse("experiments:detail", args=[self.experiment.pk]))


class ExperimentCompareViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="cmpuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.exp1 = create_completed_experiment(self.user, self.technique, self.dataset,
                                                name="Exp A")
        self.exp2 = create_completed_experiment(self.user, self.technique, self.dataset,
                                                name="Exp B")

    def test_compare_requires_login(self):
        response = self.client.get(reverse("experiments:compare"))
        self.assertNotEqual(response.status_code, 200)

    def test_get_compare_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("experiments:compare"))
        self.assertEqual(response.status_code, 200)

    def test_post_compare_creates_comparison(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("experiments:compare"), {
            "name": "Test Comparison",
            "experiments": [self.exp1.pk, self.exp2.pk],
        })
        comparison = ExperimentComparison.objects.get(user=self.user)
        self.assertRedirects(response, reverse("experiments:comparison_detail",
                                                args=[comparison.pk]))


class ComparisonDetailViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="cmpdetuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.exp1 = create_completed_experiment(self.user, self.technique, self.dataset,
                                                name="Exp A")
        self.exp2 = create_completed_experiment(self.user, self.technique, self.dataset,
                                                name="Exp B")
        self.comparison = ExperimentComparison.objects.create(
            name="Test Cmp", user=self.user,
        )
        self.comparison.experiments.set([self.exp1, self.exp2])

    def test_comparison_detail_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("experiments:comparison_detail", args=[self.comparison.pk]),
        )
        self.assertEqual(response.status_code, 200)

    def test_comparison_detail_404_for_wrong_user(self):
        other = create_user(username="othercmp", password="testpass123")
        self.client.force_login(other)
        response = self.client.get(
            reverse("experiments:comparison_detail", args=[self.comparison.pk]),
        )
        self.assertEqual(response.status_code, 404)


class ExportComparisonViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="cmpexpuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.exp1 = create_completed_experiment(self.user, self.technique, self.dataset,
                                                name="Exp A")
        self.exp2 = create_completed_experiment(self.user, self.technique, self.dataset,
                                                name="Exp B")
        self.comparison = ExperimentComparison.objects.create(
            name="Test Cmp", user=self.user,
        )
        self.comparison.experiments.set([self.exp1, self.exp2])

    def test_export_csv(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("experiments:export_comparison", args=[self.comparison.pk]) + "?format=csv",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])


class ExperimentDeleteViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="delexpuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.experiment = create_experiment(self.user, self.technique, self.dataset)

    def test_delete_get_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("experiments:delete", args=[self.experiment.pk]))
        self.assertEqual(response.status_code, 200)

    def test_delete_post_deletes(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("experiments:delete", args=[self.experiment.pk]))
        self.assertRedirects(response, reverse("experiments:list"))
        self.assertEqual(Experiment.objects.count(), 0)
