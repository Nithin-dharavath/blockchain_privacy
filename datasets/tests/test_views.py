import io
import csv
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from privacy_platform.test_utils import create_user, create_dataset_csv
from datasets.models import Dataset


class DatasetListViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="dsuser", password="testpass123")

    def test_list_requires_login(self):
        response = self.client.get(reverse("datasets:list"))
        self.assertNotEqual(response.status_code, 200)

    def test_list_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("datasets:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "datasets/dataset_list.html")

    def test_list_shows_user_datasets_only(self):
        other_user = create_user(username="other", password="testpass123")
        create_dataset_csv(self.user, name="my_data.csv")
        create_dataset_csv(other_user, name="other_data.csv")
        self.client.force_login(self.user)
        response = self.client.get(reverse("datasets:list"))
        self.assertEqual(len(response.context["datasets"]), 1)


class DatasetUploadViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="uploaduser", password="testpass123")

    def test_upload_requires_login(self):
        response = self.client.get(reverse("datasets:upload"))
        self.assertNotEqual(response.status_code, 200)

    def test_get_upload_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("datasets:upload"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "datasets/dataset_upload.html")

    def test_post_upload_creates_dataset(self):
        self.client.force_login(self.user)
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["a", "b"])
        writer.writerow([1, 2])
        csv_file = SimpleUploadedFile(
            "new_data.csv",
            csv_buffer.getvalue().encode("utf-8"),
            content_type="text/csv",
        )
        response = self.client.post(reverse("datasets:upload"), {
            "name": "New Dataset",
            "description": "Test desc",
            "dataset_type": "custom",
            "file": csv_file,
        })
        self.assertRedirects(response, reverse("datasets:list"))
        self.assertEqual(
            Dataset.objects.filter(uploaded_by=self.user).count(), 1,
        )


class DatasetDetailViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="detuser", password="testpass123")
        self.dataset = create_dataset_csv(self.user, name="detail_data.csv")

    def test_detail_requires_login(self):
        response = self.client.get(reverse("datasets:detail", args=[self.dataset.pk]))
        self.assertNotEqual(response.status_code, 200)

    def test_detail_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("datasets:detail", args=[self.dataset.pk]))
        self.assertEqual(response.status_code, 200)

    def test_detail_404_for_wrong_user(self):
        other_user = create_user(username="other2", password="testpass123")
        self.client.force_login(other_user)
        response = self.client.get(reverse("datasets:detail", args=[self.dataset.pk]))
        self.assertEqual(response.status_code, 404)


class DatasetDeleteViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="deluser", password="testpass123")
        self.dataset = create_dataset_csv(self.user, name="del_data.csv")

    def test_delete_get_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("datasets:delete", args=[self.dataset.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "datasets/dataset_confirm_delete.html")

    def test_delete_post_deletes_dataset(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("datasets:delete", args=[self.dataset.pk]))
        self.assertRedirects(response, reverse("datasets:list"))
        self.assertFalse(
            Dataset.objects.filter(pk=self.dataset.pk).exists(),
        )
