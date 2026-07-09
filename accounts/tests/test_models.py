from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class TestUserModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            user_type="researcher",
        )

    def test_create(self):
        self.assertEqual(User.objects.count(), 1)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_str(self):
        self.assertEqual(str(self.user), "testuser (researcher)")

    def test_user_type_choices(self):
        self.assertEqual(self.user.user_type, "researcher")

    def test_is_approved_default_true(self):
        self.assertTrue(self.user.is_approved)

    def test_ordering(self):
        user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="pass"
        )
        qs = User.objects.all()
        self.assertGreater(qs[0].created_at, qs[1].created_at)
