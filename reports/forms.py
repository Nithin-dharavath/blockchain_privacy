from django import forms
from django.db import models
from .models import Report, ReportSchedule, ReportTemplate
from experiments.models import Experiment

class ReportGenerationForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'report_type', 'template', 'experiments', 'file_format']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Report title'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'template': forms.Select(attrs={
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
        
        self.fields['template'].required = False
        self.fields['template'].empty_label = '-- No Template --'
        # Show public templates + user's own templates
        self.fields['template'].queryset = ReportTemplate.objects.filter(
            models.Q(is_public=True) | models.Q(user=user)
        ) if user else ReportTemplate.objects.filter(is_public=True)


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


class ReportTemplateForm(forms.ModelForm):
    class Meta:
        model = ReportTemplate
        fields = ['name', 'description', 'is_public', 'sections', 'layout']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Template name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of this template'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sections': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '6'
            }),
            'layout': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 8,
                'placeholder': '{"header_text": "...", "footer_text": "...", "primary_color": "#...", "logo_url": "..."}'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sections'].required = False
        SECTION_CHOICES = [
            ('summary', 'Executive Summary'),
            ('methodology', 'Methodology'),
            ('results', 'Results'),
            ('comparison', 'Comparison'),
            ('recommendations', 'Recommendations'),
            ('raw', 'Raw Data'),
        ]
        self.fields['sections'] = forms.MultipleChoiceField(
            choices=SECTION_CHOICES,
            widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '6'}),
            required=False,
            initial=['summary', 'methodology', 'results', 'comparison', 'recommendations'],
        )
        self.fields['layout'].required = False
