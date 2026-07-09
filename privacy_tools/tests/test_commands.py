from io import StringIO
from django.core.management import call_command
from django.test import TestCase
from privacy_tools.models import PrivacyTechnique


class LoadTechniquesTest(TestCase):
    def test_load_techniques_creates_at_least_5(self):
        out = StringIO()
        call_command("load_techniques", stdout=out)
        self.assertGreaterEqual(PrivacyTechnique.objects.count(), 5)
        self.assertIn("Successfully loaded", out.getvalue())

    def test_load_techniques_idempotent(self):
        call_command("load_techniques", stdout=StringIO())
        count_before = PrivacyTechnique.objects.count()
        out = StringIO()
        call_command("load_techniques", stdout=out)
        self.assertEqual(PrivacyTechnique.objects.count(), count_before)
        self.assertIn("already exists", out.getvalue().lower())
