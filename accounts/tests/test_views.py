from django.test import TestCase
from django.urls import reverse
from privacy_platform.test_utils import create_user


class RegisterViewTest(TestCase):
    def test_get_register_returns_200(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_post_register_creates_user_and_redirects(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "user_type": "researcher",
        }
        response = self.client.post(reverse("accounts:register"), data)
        self.assertRedirects(response, reverse("accounts:login"))

    def test_post_register_rejects_password_mismatch(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "testpass123",
            "password2": "different",
            "user_type": "researcher",
        }
        response = self.client.post(reverse("accounts:register"), data)
        self.assertEqual(response.status_code, 200)

    def test_register_redirects_authenticated_user(self):
        user = create_user()
        self.client.force_login(user)
        response = self.client.get(reverse("accounts:register"))
        self.assertRedirects(response, reverse("dashboard:home"))


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="loginuser", password="validpass123")

    def test_get_login_returns_200(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_post_login_valid_credentials_redirects(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "loginuser",
            "password": "validpass123",
        })
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_post_login_invalid_credentials_redirects_login(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "loginuser",
            "password": "wrongpass",
        })
        self.assertRedirects(response, reverse("accounts:login"))

    def test_login_redirects_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:login"))
        self.assertRedirects(response, reverse("dashboard:home"))


class LogoutViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="logoutuser", password="testpass123")

    def test_logout_requires_login(self):
        response = self.client.get(reverse("accounts:logout"))
        self.assertNotEqual(response.status_code, 200)

    def test_logout_logs_out_and_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))


class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="profileuser", password="testpass123")

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertNotEqual(response.status_code, 200)

    def test_get_profile_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")

    def test_post_profile_updates_user(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:profile"), {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "profileuser@example.com",
        })
        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
