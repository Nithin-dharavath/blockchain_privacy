from django.test import TestCase
from share.models import ExperimentShare
from accounts.models import User
from experiments.models import Experiment
from privacy_tools.models import PrivacyTechnique
from datasets.models import Dataset
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
from django.utils import timezone


class TestExperimentShare(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="shareuser", password="pass"
        )
        technique = PrivacyTechnique.objects.create(
            name="ShareTech", technique_type="ring_signature",
            description="T", algorithm_details="T",
        )
        csv_file = SimpleUploadedFile(
            "share.csv", b"a,b\n1,2", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="ShareDataset", description="T",
            dataset_type="custom", file=csv_file,
            uploaded_by=self.user,
        )
        self.experiment = Experiment.objects.create(
            name="ShareExp", user=self.user,
            dataset=dataset, privacy_technique=technique,
        )
        self.share = ExperimentShare.objects.create(
            experiment=self.experiment,
            shared_by=self.user,
        )

    def test_create(self):
        self.assertEqual(ExperimentShare.objects.count(), 1)

    def test_unique_token(self):
        self.assertIsNotNone(self.share.share_token)

    def test_is_expired(self):
        self.assertFalse(self.share.is_expired())
        self.share.expires_at = timezone.now() - timedelta(days=1)
        self.assertTrue(self.share.is_expired())

    def test_is_active(self):
        self.assertTrue(self.share.is_active())
        self.share.is_revoked = True
        self.assertFalse(self.share.is_active())

    def test_record_access(self):
        count_before = self.share.access_count
        self.share.record_access()
        self.share.refresh_from_db()
        self.assertEqual(self.share.access_count, count_before + 1)

    def test_revoked(self):
        self.share.is_revoked = True
        self.share.save()
        self.assertFalse(self.share.is_active())
