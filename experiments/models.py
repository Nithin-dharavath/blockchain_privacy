from django.db import models
from accounts.models import User
from datasets.models import Dataset
from privacy_tools.models import PrivacyTechnique
from audit.mixins import AuditableMixin
import json

class Experiment(AuditableMixin, models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiments')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='experiments')
    privacy_technique = models.ForeignKey(
        PrivacyTechnique, 
        on_delete=models.CASCADE,
        related_name='experiments'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Experiment Configuration
    configuration = models.JSONField(default=dict)
    
    # Results
    accuracy = models.FloatField(null=True, blank=True)
    privacy_score = models.FloatField(null=True, blank=True)
    execution_time = models.FloatField(null=True, blank=True)  # in seconds
    throughput = models.FloatField(null=True, blank=True)  # transactions per second
    anonymity_set_size = models.IntegerField(null=True, blank=True)
    
    # Detailed metrics
    metrics = models.JSONField(default=dict)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.privacy_technique.name}"
    
    class Meta:
        db_table = 'experiments'
        ordering = ['-created_at']


class ExperimentComparison(AuditableMixin, models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comparisons')
    experiments = models.ManyToManyField(Experiment, related_name='comparisons')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    class Meta:
        db_table = 'experiment_comparisons'
        ordering = ['-created_at']
