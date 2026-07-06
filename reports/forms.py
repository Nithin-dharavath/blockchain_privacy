from django import forms
from .models import Report, ReportSchedule
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


class ReportScheduleForm(forms.ModelForm):
    class Meta:
        model = ReportSchedule
        fields = [
            'name', 'report_type', 'file_format',
            'schedule_frequency', 'schedule_day', 'experiments',
            'is_active', 'auto_generate',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Schedule name'
            }),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'file_format': forms.Select(attrs={'class': 'form-select'}),
            'schedule_frequency': forms.Select(attrs={'class': 'form-select'}),
            'schedule_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 1 for Monday, 15 for 15th of month'
            }),
            'experiments': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '8'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_generate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['experiments'].queryset = Experiment.objects.filter(
                user=user, status='completed'
            ).order_by('-created_at')
        self.fields['schedule_day'].required = False
        self.fields['experiments'].required = False
