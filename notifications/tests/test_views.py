import json
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from privacy_platform.test_utils import create_user, create_notification


class NotificationListViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="notifuser", password="testpass123")

    def test_list_requires_login(self):
        response = self.client.get(reverse("notifications:list"))
        self.assertNotEqual(response.status_code, 200)

    def test_list_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("notifications:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "notifications/list.html")

    def test_list_filters_unread(self):
        create_notification(self.user, is_read=False)
        create_notification(self.user, is_read=True)
        self.client.force_login(self.user)
        response = self.client.get(reverse("notifications:list") + "?filter=unread")
        self.assertEqual(len(response.context["page_obj"]), 1)

    def test_list_filters_read(self):
        create_notification(self.user, is_read=False)
        create_notification(self.user, is_read=True)
        self.client.force_login(self.user)
        response = self.client.get(reverse("notifications:list") + "?filter=read")
        self.assertEqual(len(response.context["page_obj"]), 1)


class MarkReadViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="markreaduser", password="testpass123")

    def test_mark_read_requires_login(self):
        n = create_notification(self.user)
        response = self.client.get(reverse("notifications:mark_read", args=[n.pk]))
        self.assertNotEqual(response.status_code, 200)

    def test_mark_read_returns_json(self):
        n = create_notification(self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse("notifications:mark_read", args=[n.pk]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_mark_read_404_for_wrong_user(self):
        other = create_user(username="othernotif", password="testpass123")
        n = create_notification(self.user)
        self.client.force_login(other)
        response = self.client.get(reverse("notifications:mark_read", args=[n.pk]))
        self.assertEqual(response.status_code, 404)


class MarkAllReadViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="markalluser", password="testpass123")

    def test_mark_all_read_marks_all(self):
        create_notification(self.user, is_read=False)
        create_notification(self.user, is_read=False)
        self.client.force_login(self.user)
        response = self.client.get(reverse("notifications:mark_all_read"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.user.notifications.filter(is_read=False).count(), 0,
        )


class UnreadCountViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="countuser", password="testpass123")

    def test_unread_count_returns_json(self):
        create_notification(self.user, is_read=False)
        create_notification(self.user, is_read=False)
        self.client.force_login(self.user)
        response = self.client.get(reverse("notifications:unread_count"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["unread_count"], 2)
