from django.test import TestCase
from django.db import IntegrityError
from experiments.models import Experiment, ExperimentComparison
from accounts.models import User
from privacy_tools.models import PrivacyTechnique
from datasets.models import Dataset
from django.core.files.uploadedfile import SimpleUploadedFile


class TestExperimentModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="expuser", password="pass"
        )
        self.technique = PrivacyTechnique.objects.create(
            name="Ring Sig",
            technique_type="ring_signature",
            description="Test",
            algorithm_details="Test",
        )
        csv_file = SimpleUploadedFile(
            "data.csv", b"a,b\n1,2\n3,4", content_type="text/csv"
        )
        self.dataset = Dataset.objects.create(
            name="Exp Dataset",
            description="Test",
            dataset_type="custom",
            file=csv_file,
            uploaded_by=self.user,
        )
        self.experiment = Experiment.objects.create(
            name="Test Experiment",
            user=self.user,
            dataset=self.dataset,
            privacy_technique=self.technique,
        )

    def test_create(self):
        self.assertEqual(Experiment.objects.count(), 1)

    def test_str(self):
        self.assertIn("Test Experiment", str(self.experiment))

    def test_unique_user_name(self):
        with self.assertRaises(IntegrityError):
            Experiment.objects.create(
                name="Test Experiment",
                user=self.user,
                dataset=self.dataset,
                privacy_technique=self.technique,
            )

    def test_status_default(self):
        self.assertEqual(self.experiment.status, "pending")

    def test_audit_log_create(self):
        self.assertIsNotNone(self.experiment.pk)
        self.assertIsNotNone(self.experiment.created_at)

    def test_audit_log_status_change(self):
        self.experiment.status = "running"
        self.experiment.save()
        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.status, "running")


class TestExperimentComparisonModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="compuser", password="pass"
        )
        self.technique = PrivacyTechnique.objects.create(
            name="ZKP",
            technique_type="zkp",
            description="Test",
            algorithm_details="Test",
        )
        csv_file = SimpleUploadedFile(
            "cdata.csv", b"x,y\n1,2\n3,4", content_type="text/csv"
        )
        self.dataset = Dataset.objects.create(
            name="Comp Dataset",
            description="Test",
            dataset_type="custom",
            file=csv_file,
            uploaded_by=self.user,
        )
        self.exp1 = Experiment.objects.create(
            name="Exp 1", user=self.user,
            dataset=self.dataset, privacy_technique=self.technique,
        )
        self.exp2 = Experiment.objects.create(
            name="Exp 2", user=self.user,
            dataset=self.dataset, privacy_technique=self.technique,
        )
        self.comparison = ExperimentComparison.objects.create(
            name="Test Comparison", user=self.user,
        )
        self.comparison.experiments.add(self.exp1, self.exp2)

    def test_create(self):
        self.assertEqual(ExperimentComparison.objects.count(), 1)

    def test_str(self):
        self.assertIn("Test Comparison", str(self.comparison))

    def test_many_to_many(self):
        self.assertEqual(self.comparison.experiments.count(), 2)


class TestExperimentEdgeCases(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="edgeexpuser", password="pass"
        )
        self.technique = PrivacyTechnique.objects.create(
            name="Edge Tech",
            technique_type="ring_signature",
            description="Test",
            algorithm_details="Test",
        )
        csv_file = SimpleUploadedFile(
            "edgedata.csv", b"a,b\n1,2", content_type="text/csv"
        )
        self.dataset = Dataset.objects.create(
            name="Edge Dataset",
            description="Test",
            dataset_type="custom",
            file=csv_file,
            uploaded_by=self.user,
        )

    def test_create_with_empty_config(self):
        exp = Experiment.objects.create(
            name="Empty Config",
            user=self.user,
            dataset=self.dataset,
            privacy_technique=self.technique,
            configuration={},
        )
        self.assertEqual(exp.configuration, {})

    def test_create_with_empty_dict_config(self):
        exp = Experiment.objects.create(
            name="Empty Dict Config",
            user=self.user,
            dataset=self.dataset,
            privacy_technique=self.technique,
            configuration={},
        )
        self.assertEqual(exp.configuration, {})

    def test_create_with_null_metrics(self):
        exp = Experiment.objects.create(
            name="Null Metrics",
            user=self.user,
            dataset=self.dataset,
            privacy_technique=self.technique,
            status="completed",
            privacy_score=None,
            accuracy=None,
            execution_time=None,
            throughput=None,
            anonymity_set_size=None,
        )
        self.assertIsNone(exp.privacy_score)
        self.assertIsNone(exp.accuracy)

    def test_create_with_null_metrics(self):
        exp = Experiment.objects.create(
            name="Null Metrics",
            user=self.user,
            dataset=self.dataset,
            privacy_technique=self.technique,
            status="completed",
            privacy_score=None,
            accuracy=None,
            execution_time=None,
            throughput=None,
            anonymity_set_size=None,
        )
        self.assertIsNone(exp.privacy_score)
        self.assertIsNone(exp.accuracy)
