from django import forms
from .models import Report
from experiments.models import Experiment

class ReportGenerationForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'report_type', 'experiments', 'file_format']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Report title'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'experiments': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '8'
            }),
            'file_format': forms.Select(attrs={
                'class': 'form-select'
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
