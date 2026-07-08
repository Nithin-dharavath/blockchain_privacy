from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from privacy_tools.models import PrivacyTechnique


class TestPrivacyTechniqueModel(TestCase):
    def setUp(self):
        self.technique = PrivacyTechnique.objects.create(
            name="Test Ring Signature",
            technique_type="ring_signature",
            description="A test technique",
            algorithm_details="Test algorithm",
            parameters={"ring_size": 5},
            complexity="O(n)",
            security_level=5
        )

    def test_create(self):
        count = PrivacyTechnique.objects.count()
        self.assertEqual(count, 1)

    def test_str(self):
        expected = "Test Ring Signature (Ring Signatures)"
        self.assertEqual(str(self.technique), expected)

    def test_type_choices(self):
        choices = dict(PrivacyTechnique.TECHNIQUE_CHOICES)
        self.assertIn('ring_signature', choices)
        self.assertIn('zkp', choices)
        self.assertIn('smpc', choices)
        self.assertIn('tee', choices)
        self.assertIn('mixer', choices)

    def test_security_level_validators(self):
        technique = PrivacyTechnique(
            name="Invalid Security",
            technique_type="zkp",
            description="test",
            algorithm_details="test",
            security_level=15
        )
        with self.assertRaises(ValidationError):
            technique.full_clean()

    def test_unique_name(self):
        with self.assertRaises(IntegrityError):
            PrivacyTechnique.objects.create(
                name="Test Ring Signature",
                technique_type="zkp",
                description="Duplicate",
                algorithm_details="test"
            )

    def test_audit_log_create(self):
        self.assertIsNotNone(self.technique.pk)
        self.assertIsNotNone(self.technique.created_at)
        self.assertIsNotNone(self.technique.updated_at)

    def test_audit_log_update(self):
        original_updated = self.technique.updated_at
        self.technique.description = "Updated description"
        self.technique.save()
        self.assertGreaterEqual(self.technique.updated_at, original_updated)
