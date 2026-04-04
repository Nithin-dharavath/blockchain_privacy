from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class PrivacyTechnique(models.Model):
    TECHNIQUE_CHOICES = (
        ('ring_signature', 'Ring Signatures'),
        ('zkp', 'Zero-Knowledge Proofs'),
        ('smpc', 'Secure Multi-Party Computation'),
        ('tee', 'Trusted Execution Environments'),
        ('mixer', 'Cryptocurrency Mixers'),
    )
    
    name = models.CharField(max_length=100, unique=True)
    technique_type = models.CharField(max_length=20, choices=TECHNIQUE_CHOICES)
    description = models.TextField()
    algorithm_details = models.TextField()
    parameters = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    complexity = models.CharField(max_length=50, blank=True)
    security_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_technique_type_display()})"
    
    class Meta:
        db_table = 'privacy_techniques'
        ordering = ['technique_type', 'name']
