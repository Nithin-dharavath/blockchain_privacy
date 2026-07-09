from io import StringIO
from django.core.management import call_command
from django.test import TestCase
from admin_panel.models import SystemMetric
from privacy_platform.test_utils import create_user, create_technique, create_dataset_csv, create_completed_experiment


class RecordSystemMetricsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("metricuser")
        technique = create_technique("ring_signature")
        dataset = create_dataset_csv(cls.user, rows=5)
        create_completed_experiment(cls.user, technique, dataset)

    def test_creates_4_metrics(self):
        out = StringIO()
        call_command("record_system_metrics", stdout=out)
        self.assertEqual(SystemMetric.objects.count(), 4)
        names = list(SystemMetric.objects.values_list("metric_name", flat=True))
        self.assertIn("active_users", names)
        self.assertIn("experiments_per_hour", names)
        self.assertIn("avg_response_time", names)
        self.assertIn("error_rate", names)
