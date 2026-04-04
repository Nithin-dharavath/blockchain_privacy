from django import forms
from .models import Experiment, ExperimentComparison
from datasets.models import Dataset
from privacy_tools.models import PrivacyTechnique
import json


class ExperimentForm(forms.ModelForm):
    class Meta:
        model = Experiment
        fields = ['name', 'description', 'dataset', 'privacy_technique', 'configuration']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Experiment name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe your experiment...'
            }),
            'dataset': forms.Select(attrs={
                'class': 'form-select'
            }),
            'privacy_technique': forms.Select(attrs={
                'class': 'form-select'
            }),
            'configuration': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter configuration as JSON: {"ring_size": 5, "num_transactions": 100}'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['dataset'].queryset = Dataset.objects.filter(
                uploaded_by=user,
                status='approved'
            )
        
        self.fields['privacy_technique'].queryset = PrivacyTechnique.objects.filter(
            is_active=True
        )
    
    def clean_configuration(self):
        """Validate and parse configuration JSON"""
        config = self.cleaned_data.get('configuration')
        
        # Handle empty configuration
        if not config:
            return {}
        
        # If it's already a dict, return it
        if isinstance(config, dict):
            return config
        
        # If it's a string, try to parse as JSON
        if isinstance(config, str):
            config = config.strip()
            if not config:
                return {}
            
            try:
                config_dict = json.loads(config)
                
                # Validate it's a dictionary
                if not isinstance(config_dict, dict):
                    raise forms.ValidationError('Configuration must be a JSON object (dictionary)')
                
                return config_dict
            
            except json.JSONDecodeError as e:
                raise forms.ValidationError(f'Invalid JSON format: {str(e)}')
        
        # Unknown type
        raise forms.ValidationError('Configuration must be a valid JSON string or dictionary')


class ExperimentComparisonForm(forms.ModelForm):
    class Meta:
        model = ExperimentComparison
        fields = ['name', 'experiments', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Comparison name'
            }),
            'experiments': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '8'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['experiments'].queryset = Experiment.objects.filter(
                user=user,
                status='completed'
            ).order_by('-created_at')
    
    def clean_experiments(self):
        """Validate that at least 2 experiments are selected"""
        experiments = self.cleaned_data.get('experiments')
        
        if not experiments:
            raise forms.ValidationError('Please select at least 2 experiments to compare.')
        
        if experiments.count() < 2:
            raise forms.ValidationError('Please select at least 2 experiments to compare.')
        
        return experiments
