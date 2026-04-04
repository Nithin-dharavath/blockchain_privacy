from django import forms
from .models import Dataset

class DatasetUploadForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name', 'description', 'dataset_type', 'file', 'is_anonymized']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dataset name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your dataset...'
            }),
            'dataset_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.csv,.json'
            }),
            'is_anonymized': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            if not file.name.endswith(('.csv', '.json')):
                raise forms.ValidationError('Only CSV and JSON files are allowed.')
            
            # Check file size (max 50MB)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('File size must not exceed 50MB.')
        
        return file
