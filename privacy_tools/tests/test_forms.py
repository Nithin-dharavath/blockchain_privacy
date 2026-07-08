from django.test import TestCase
from privacy_tools.forms import PrivacyTechniqueForm


class TestPrivacyTechniqueForm(TestCase):
    def test_valid(self):
        form_data = {
            'name': 'New Technique',
            'technique_type': 'zkp',
            'description': 'A valid technique',
            'algorithm_details': 'Some details',
            'parameters': '{"key": "value"}',
            'complexity': 'O(n)',
            'security_level': 5,
            'is_active': True
        }
        form = PrivacyTechniqueForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        form = PrivacyTechniqueForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('technique_type', form.errors)
        self.assertIn('description', form.errors)
        self.assertIn('algorithm_details', form.errors)
