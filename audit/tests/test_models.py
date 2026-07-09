from django.test import TestCase
from audit.models import AuditLog
from accounts.models import User


class TestAuditLogModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="audituser", password="pass"
        )
        self.log = AuditLog.objects.create(
            user=self.user,
            action_type="CREATE",
            content_type="experiment",
            object_id=1,
            object_repr="Test Experiment",
            changes={"name": {"old": "", "new": "Test Experiment"}},
        )

    def test_create(self):
        self.assertIsNotNone(self.log.pk)

    def test_str(self):
        self.assertIn("Create", str(self.log))

    def test_indexes(self):
        from django.db import connection
        with connection.schema_editor() as schema_editor:
            indices = [
                "idx_audit_content_object",
                "idx_audit_user_timestamp",
                "idx_audit_action_type",
            ]
            for idx in indices:
                self.assertTrue(
                    any(idx in str(c) for c in schema_editor._constraint_names(AuditLog, index=True)),
                    f"Index {idx} not found",
                )

    def test_all_action_types(self):
        actions = [c[0] for c in AuditLog.ACTION_CHOICES]
        expected = [
            "CREATE", "UPDATE", "DELETE", "RUN", "APPROVE",
            "REJECT", "LOGIN", "LOGOUT", "EXPORT", "DOWNLOAD",
        ]
        self.assertEqual(actions, expected)


class TestAuditableMixin(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mixintest", password="pass"
        )

    def test_tracks_original_state(self):
        from experiments.models import Experiment
        from privacy_tools.models import PrivacyTechnique
        from datasets.models import Dataset
        from django.core.files.uploadedfile import SimpleUploadedFile

        technique = PrivacyTechnique.objects.create(
            name="MixTech", technique_type="smpc",
            description="T", algorithm_details="T",
        )
        csv_file = SimpleUploadedFile(
            "m.csv", b"a,b\n1,2", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="MDataset", description="T",
            dataset_type="custom", file=csv_file,
            uploaded_by=self.user,
        )
        experiment = Experiment.objects.create(
            name="MixExp", user=self.user,
            dataset=dataset, privacy_technique=technique,
        )
        self.assertIsNotNone(experiment._original_state)

    def test_detects_changes(self):
        from experiments.models import Experiment
        from privacy_tools.models import PrivacyTechnique
        from datasets.models import Dataset
        from django.core.files.uploadedfile import SimpleUploadedFile

        technique = PrivacyTechnique.objects.create(
            name="DetectTech", technique_type="tee",
            description="T", algorithm_details="T",
        )
        csv_file = SimpleUploadedFile(
            "det.csv", b"a,b\n1,2", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="DetDataset", description="T",
            dataset_type="custom", file=csv_file,
            uploaded_by=self.user,
        )
        experiment = Experiment.objects.create(
            name="DetExp", user=self.user,
            dataset=dataset, privacy_technique=technique,
        )
        experiment.name = "Updated"
        changes = experiment._get_changes()
        self.assertIn("name", changes)

    def test_get_special_action_run(self):
        from experiments.models import Experiment
        from privacy_tools.models import PrivacyTechnique
        from datasets.models import Dataset
        from django.core.files.uploadedfile import SimpleUploadedFile

        technique = PrivacyTechnique.objects.create(
            name="RunTech", technique_type="ring_signature",
            description="T", algorithm_details="T",
        )
        csv_file = SimpleUploadedFile(
            "run.csv", b"a,b\n1,2", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="RunDataset", description="T",
            dataset_type="custom", file=csv_file,
            uploaded_by=self.user,
        )
        experiment = Experiment.objects.create(
            name="RunExp", user=self.user,
            dataset=dataset, privacy_technique=technique,
        )
        experiment.status = "running"
        experiment.save()
        logs = AuditLog.objects.filter(
            object_id=experiment.pk, content_type="experiment"
        )
        self.assertTrue(logs.filter(action_type="RUN").exists())

    def test_get_special_action_approve(self):
        from datasets.models import Dataset
        from django.core.files.uploadedfile import SimpleUploadedFile

        csv_file = SimpleUploadedFile(
            "app.csv", b"a,b\n1,2", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="AppDataset", description="T",
            dataset_type="custom", file=csv_file,
            uploaded_by=self.user,
        )
        dataset.status = "approved"
        dataset.approved_by = self.user
        dataset.save()
        logs = AuditLog.objects.filter(
            object_id=dataset.pk, content_type="dataset"
        )
        self.assertTrue(logs.filter(action_type="APPROVE").exists())

    def test_save_logs_create(self):
        from experiments.models import Experiment
        from privacy_tools.models import PrivacyTechnique
        from datasets.models import Dataset
        from django.core.files.uploadedfile import SimpleUploadedFile

        technique = PrivacyTechnique.objects.create(
            name="SaveTech", technique_type="mixer",
            description="T", algorithm_details="T",
        )
        csv_file = SimpleUploadedFile(
            "save.csv", b"a,b\n1,2", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="SaveDataset", description="T",
            dataset_type="custom", file=csv_file,
            uploaded_by=self.user,
        )
        experiment = Experiment.objects.create(
            name="SaveExp", user=self.user,
            dataset=dataset, privacy_technique=technique,
        )
        log = AuditLog.objects.filter(
            object_id=experiment.pk,
            content_type="experiment",
            action_type="CREATE",
        )
        self.assertTrue(log.exists())

    def test_delete_logs_delete(self):
        experiment = None
        from experiments.models import Experiment
        from privacy_tools.models import PrivacyTechnique
        from datasets.models import Dataset
        from django.core.files.uploadedfile import SimpleUploadedFile

        technique = PrivacyTechnique.objects.create(
            name="DelTech", technique_type="zkp",
            description="T", algorithm_details="T",
        )
        csv_file = SimpleUploadedFile(
            "del.csv", b"a,b\n1,2", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="DelDataset", description="T",
            dataset_type="custom", file=csv_file,
            uploaded_by=self.user,
        )
        experiment = Experiment.objects.create(
            name="DelExp", user=self.user,
            dataset=dataset, privacy_technique=technique,
        )
        pk = experiment.pk
        experiment.delete()
        log = AuditLog.objects.filter(
            object_id=pk,
            content_type="experiment",
            action_type="DELETE",
        )
        self.assertTrue(log.exists())
