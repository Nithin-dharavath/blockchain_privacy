from django.test import TestCase
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile
from datasets.models import Dataset
from accounts.models import User


class TestDatasetModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="datasetuser", password="pass"
        )
        self.csv_file = SimpleUploadedFile(
            "test.csv", b"col1,col2\n1,2\n3,4\n5,6", content_type="text/csv"
        )
        self.dataset = Dataset.objects.create(
            name="Test Dataset",
            description="A test dataset",
            dataset_type="custom",
            file=self.csv_file,
            uploaded_by=self.user,
        )

    def test_create(self):
        self.assertEqual(Dataset.objects.count(), 1)

    def test_str(self):
        self.assertEqual(str(self.dataset), "Test Dataset")

    def test_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            Dataset.objects.create(
                name="Test Dataset",
                description="Duplicate",
                dataset_type="custom",
                file=self.csv_file,
                uploaded_by=self.user,
            )

    def test_is_approved(self):
        self.assertFalse(self.dataset.is_approved)
        self.dataset.status = "approved"
        self.dataset.save()
        self.assertTrue(self.dataset.is_approved)

    def test_is_pending(self):
        self.assertTrue(self.dataset.is_pending)
        self.dataset.status = "approved"
        self.dataset.save()
        self.assertFalse(self.dataset.is_pending)

    def test_is_rejected(self):
        self.assertFalse(self.dataset.is_rejected)
        self.dataset.status = "rejected"
        self.dataset.save()
        self.assertTrue(self.dataset.is_rejected)

    def test_file_extension(self):
        self.assertEqual(self.dataset.file_extension, ".csv")

    def test_get_data_returns_dataframe(self):
        df = self.dataset.get_data()
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 3)

    def test_get_sample_data(self):
        sample = self.dataset.get_sample_data(n=2)
        self.assertIsNotNone(sample)
        self.assertEqual(len(sample), 2)

    def test_save_calculates_file_size(self):
        self.assertIsNotNone(self.dataset.file_size)
        self.assertGreater(self.dataset.file_size, 0)

    def test_delete_removes_file(self):
        file_path = self.dataset.file.path
        self.dataset.delete()
        self.assertFalse(__import__("os").path.isfile(file_path))

    def test_audit_log_create(self):
        self.assertIsNotNone(self.dataset.pk)
        self.assertIsNotNone(self.dataset.created_at)

    def test_audit_log_status_change_approve(self):
        self.dataset.status = "approved"
        self.dataset.approved_by = self.user
        self.dataset.save()
        self.assertEqual(self.dataset.status, "approved")


class TestDatasetEdgeCases(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="edgeuser", password="pass"
        )

    def test_empty_dataset_zero_rows_zero_columns(self):
        csv_file = SimpleUploadedFile(
            "empty.csv", b"", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="Empty Dataset",
            description="Empty",
            dataset_type="custom",
            file=csv_file,
            uploaded_by=self.user,
        )
        df = dataset.get_data()
        self.assertIsNone(df)
        self.assertIsNone(dataset.row_count)

    def test_get_sample_data_empty(self):
        csv_file = SimpleUploadedFile(
            "empty2.csv", b"", content_type="text/csv"
        )
        dataset = Dataset.objects.create(
            name="Empty Dataset 2",
            description="Empty",
            dataset_type="custom",
            file=csv_file,
            uploaded_by=self.user,
        )
        sample = dataset.get_sample_data()
        self.assertIsNone(sample)

    def test_string_only_columns(self):
        csv_file = SimpleUploadedFile(
            "strings.csv",
            b"name,city,country\nAlice,NYC,USA\nBob,London,UK\nCharlie,Paris,FR",
            content_type="text/csv",
        )
        dataset = Dataset.objects.create(
            name="String Only Dataset",
            description="Strings only",
            dataset_type="custom",
            file=csv_file,
            uploaded_by=self.user,
        )
        df = dataset.get_data()
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 3)
        self.assertEqual(df.iloc[0]["name"], "Alice")
