from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from audit.mixins import AuditableMixin
import os

User = get_user_model()


class Dataset(AuditableMixin, models.Model):
    """Model for storing user-uploaded datasets"""
    
    DATASET_TYPES = [
        ('blockchain_transactions', 'Blockchain Transactions'),
        ('network_data', 'Network Data'),
        ('user_behavior', 'User Behavior'),
        ('privacy_metrics', 'Privacy Metrics'),
        ('custom', 'Custom Dataset'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    dataset_type = models.CharField(max_length=50, choices=DATASET_TYPES)
    file = models.FileField(
        upload_to='datasets/',
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'json'])]
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='datasets'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_anonymized = models.BooleanField(default=False)
    
    # Approval fields
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_datasets'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True, null=True)
    
    # Metadata
    row_count = models.IntegerField(null=True, blank=True)
    column_count = models.IntegerField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dataset'
        verbose_name_plural = 'Datasets'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'uploaded_by'],
                name='uq_dataset_name_user'
            ),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to calculate metadata"""
        # Calculate file size if file exists
        if self.file:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        
        # Call parent save
        super().save(*args, **kwargs)
        
        # Calculate row and column count after file is saved
        if self.file and not self.row_count:
            self.calculate_metadata()
    
    def calculate_metadata(self):
        """Calculate dataset metadata (rows, columns)"""
        try:
            import pandas as pd
            
            file_path = self.file.path
            
            # Read based on file extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.json'):
                df = pd.read_json(file_path)
            else:
                return
            
            # Update metadata
            self.row_count = len(df)
            self.column_count = len(df.columns)
            
            # Save without triggering save again
            Dataset.objects.filter(pk=self.pk).update(
                row_count=self.row_count,
                column_count=self.column_count
            )
        
        except Exception as e:
            print(f"Error calculating metadata: {str(e)}")
    
    def get_data(self):
        """Load and return dataset as pandas DataFrame"""
        try:
            import pandas as pd
            
            file_path = self.file.path
            
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path)
            elif file_path.endswith('.json'):
                return pd.read_json(file_path)
            else:
                return None
        
        except Exception as e:
            print(f"Error loading dataset: {str(e)}")
            return None
    
    def get_sample_data(self, n=10):
        """Get first n rows of dataset"""
        try:
            df = self.get_data()
            if df is not None:
                return df.head(n)
            return None
        except Exception:
            return None
    
    def delete(self, *args, **kwargs):
        """Override delete to remove file"""
        # Delete the file from storage
        if self.file:
            try:
                if os.path.isfile(self.file.path):
                    os.remove(self.file.path)
            except Exception as e:
                print(f"Error deleting file: {str(e)}")
        
        # Call parent delete
        super().delete(*args, **kwargs)
    
    @property
    def is_approved(self):
        """Check if dataset is approved"""
        return self.status == 'approved'
    
    @property
    def is_pending(self):
        """Check if dataset is pending"""
        return self.status == 'pending'
    
    @property
    def is_rejected(self):
        """Check if dataset is rejected"""
        return self.status == 'rejected'
    
    @property
    def file_extension(self):
        """Get file extension"""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return None
