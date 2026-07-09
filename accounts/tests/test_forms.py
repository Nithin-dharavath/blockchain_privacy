from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.forms import UserRegistrationForm, UserProfileForm

User = get_user_model()


class TestUserRegistrationForm(TestCase):
    def test_valid(self):
        form = UserRegistrationForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'secret123',
            'password2': 'secret123',
            'first_name': 'New',
            'last_name': 'User',
            'user_type': 'researcher',
            'organization': 'Test Org',
        })
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        form = UserRegistrationForm(data={
            'username': 'user1',
            'email': 'user1@example.com',
            'password': 'secret123',
            'password2': 'different',
            'user_type': 'researcher',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_password_too_short(self):
        form = UserRegistrationForm(data={
            'username': 'user2',
            'email': 'user2@example.com',
            'password': 'abc',
            'password2': 'abc',
            'user_type': 'researcher',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_duplicate_email(self):
        User.objects.create_user(
            username='existing', email='dup@example.com', password='pass123'
        )
        form = UserRegistrationForm(data={
            'username': 'newguy',
            'email': 'dup@example.com',
            'password': 'secret123',
            'password2': 'secret123',
            'user_type': 'researcher',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_username(self):
        User.objects.create_user(
            username='taken', email='taken@example.com', password='pass123'
        )
        form = UserRegistrationForm(data={
            'username': 'taken',
            'email': 'other@example.com',
            'password': 'secret123',
            'password2': 'secret123',
            'user_type': 'researcher',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)


class TestUserProfileForm(TestCase):
    def test_valid(self):
        form = UserProfileForm(data={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'organization': 'ACME',
            'phone': '1234567890',
            'bio': 'A researcher.',
        })
        self.assertTrue(form.is_valid())

    def test_optional_fields(self):
        form = UserProfileForm(data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
        })
        self.assertTrue(form.is_valid())
