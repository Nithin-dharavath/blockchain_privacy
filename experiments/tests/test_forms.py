from django.test import TestCase
from django.contrib.auth import get_user_model
from experiments.forms import ExperimentForm, ExperimentComparisonForm
from experiments.models import Experiment, ExperimentComparison
from privacy_tools.models import PrivacyTechnique
from datasets.models import Dataset
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class TestExperimentForm(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="expuser", password="pass"
        )
        self.other_user = User.objects.create_user(
            username="other", password="pass"
        )
        self.technique = PrivacyTechnique.objects.create(
            name="Ring Sig",
            technique_type="ring_signature",
            description="Test",
            algorithm_details="Test",
        )
        self.inactive_technique = PrivacyTechnique.objects.create(
            name="Old Tech",
            technique_type="zkp",
            description="Inactive",
            algorithm_details="Inactive",
            is_active=False,
        )
        csv_file = SimpleUploadedFile(
            "data.csv", b"a,b\n1,2\n3,4", content_type="text/csv"
        )
        self.dataset = Dataset.objects.create(
            name="My Dataset",
            description="Test",
            dataset_type="custom",
            file=csv_file,
            uploaded_by=self.user,
            status='approved',
        )
        self.other_dataset = Dataset.objects.create(
            name="Other Dataset",
            description="Test",
            dataset_type="custom",
            file=csv_file,
            uploaded_by=self.other_user,
            status='approved',
        )

    def test_valid(self):
        form = ExperimentForm(
            data={
                'name': 'My Experiment',
                'description': 'Testing',
                'dataset': self.dataset.pk,
                'privacy_technique': self.technique.pk,
                'configuration': '{"ring_size": 5}',
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_filters_dataset_by_user(self):
        form = ExperimentForm(user=self.user)
        qs = form.fields['dataset'].queryset
        self.assertIn(self.dataset, qs)
        self.assertNotIn(self.other_dataset, qs)

    def test_filters_technique_by_active(self):
        form = ExperimentForm(user=self.user)
        qs = form.fields['privacy_technique'].queryset
        self.assertIn(self.technique, qs)
        self.assertNotIn(self.inactive_technique, qs)

    def test_validates_json_config(self):
        form = ExperimentForm(
            data={
                'name': 'JSON Test',
                'description': '',
                'dataset': self.dataset.pk,
                'privacy_technique': self.technique.pk,
                'configuration': '{"ring_size": 10, "num_tx": 100}',
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())
        config = form.cleaned_data['configuration']
        self.assertEqual(config['ring_size'], 10)
        self.assertEqual(config['num_tx'], 100)

    def test_invalid_json(self):
        form = ExperimentForm(
            data={
                'name': 'Bad JSON',
                'description': '',
                'dataset': self.dataset.pk,
                'privacy_technique': self.technique.pk,
                'configuration': 'not-json-at-all',
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('configuration', form.errors)

    def test_empty_config_returns_dict(self):
        form = ExperimentForm(
            data={
                'name': 'Empty Config',
                'description': '',
                'dataset': self.dataset.pk,
                'privacy_technique': self.technique.pk,
                'configuration': '',
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['configuration'], {})


class TestExperimentComparisonForm(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="compuser", password="pass"
        )
        self.other_user = User.objects.create_user(
            username="other", password="pass"
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
            status='approved',
        )
        self.exp1 = Experiment.objects.create(
            name="Exp 1", user=self.user,
            dataset=self.dataset, privacy_technique=self.technique,
            status='completed',
        )
        self.exp2 = Experiment.objects.create(
            name="Exp 2", user=self.user,
            dataset=self.dataset, privacy_technique=self.technique,
            status='completed',
        )
        self.other_exp = Experiment.objects.create(
            name="Other Exp", user=self.other_user,
            dataset=self.dataset, privacy_technique=self.technique,
            status='completed',
        )
        self.pending_exp = Experiment.objects.create(
            name="Pending Exp", user=self.user,
            dataset=self.dataset, privacy_technique=self.technique,
            status='pending',
        )

    def test_valid(self):
        form = ExperimentComparisonForm(
            data={
                'name': 'My Comparison',
                'experiments': [self.exp1.pk, self.exp2.pk],
                'notes': 'Comparing approaches',
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_filters_by_user_and_completed(self):
        form = ExperimentComparisonForm(user=self.user)
        qs = form.fields['experiments'].queryset
        self.assertIn(self.exp1, qs)
        self.assertIn(self.exp2, qs)
        self.assertNotIn(self.other_exp, qs)
        self.assertNotIn(self.pending_exp, qs)

    def test_requires_two_experiments(self):
        form = ExperimentComparisonForm(
            data={
                'name': 'Empty Compare',
                'experiments': [],
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('experiments', form.errors)

    def test_rejects_single(self):
        form = ExperimentComparisonForm(
            data={
                'name': 'Single Exp',
                'experiments': [self.exp1.pk],
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('experiments', form.errors)
