from django.test import TestCase
from notifications.models import Notification
from accounts.models import User


class TestNotificationModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notifuser", password="pass"
        )
        self.notification = Notification.objects.create(
            recipient=self.user,
            verb="experiment_completed",
            description="Your experiment is done",
        )

    def test_create(self):
        self.assertEqual(Notification.objects.count(), 1)

    def test_is_read_default_false(self):
        self.assertFalse(self.notification.is_read)
