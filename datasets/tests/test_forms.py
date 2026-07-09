from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from datasets.forms import DatasetUploadForm


class TestDatasetUploadForm(TestCase):
    def test_valid(self):
        csv_file = SimpleUploadedFile(
            "test.csv", b"a,b\n1,2\n3,4", content_type="text/csv"
        )
        form = DatasetUploadForm(data={
            'name': 'My Dataset',
            'description': 'A test dataset',
            'dataset_type': 'custom',
            'is_anonymized': False,
        }, files={
            'file': csv_file,
        })
        self.assertTrue(form.is_valid())

    def test_rejects_invalid_extension(self):
        txt_file = SimpleUploadedFile(
            "test.txt", b"hello world", content_type="text/plain"
        )
        form = DatasetUploadForm(data={
            'name': 'Bad File',
            'description': 'Should fail',
            'dataset_type': 'custom',
            'is_anonymized': False,
        }, files={
            'file': txt_file,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)
