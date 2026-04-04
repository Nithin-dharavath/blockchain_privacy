from django import forms
from .models import PrivacyTechnique
import json


class PrivacyTechniqueForm(forms.ModelForm):
    class Meta:
        model = PrivacyTechnique
        fields = [
            'name',
            'technique_type',
            'description',
            'algorithm_details',
            'parameters',
            'complexity',
            'security_level',
            'is_active'
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Technique name'
            }),

            'technique_type': forms.Select(attrs={
                'class': 'form-select'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Brief description...'
            }),

            'algorithm_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Technical details...'
            }),

            'parameters': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Example: {"epsilon": 1.0, "k": 5}'
            }),

            'complexity': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., O(n log n)'
            }),

            'security_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),

            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_parameters(self):
        params = self.cleaned_data.get('parameters')

        # If empty → return empty dict
        if not params:
            return {}

        # If already a dict (e.g., from JSONField)
        if isinstance(params, dict):
            return params

        # If string → parse JSON
        if isinstance(params, str):
            try:
                parsed = json.loads(params)
            except json.JSONDecodeError:
                raise forms.ValidationError(
                    'Parameters must be valid JSON (e.g., {"key": "value"})'
                )

            if not isinstance(parsed, dict):
                raise forms.ValidationError(
                    'JSON must represent an object (key-value pairs)'
                )

            return parsed

        # Any unexpected type
        raise forms.ValidationError(
            'Invalid format. Parameters must be a JSON object'
        )