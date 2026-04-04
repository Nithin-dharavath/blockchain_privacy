from django.db import models
from accounts.models import User
from experiments.models import Experiment

class Report(models.Model):
    REPORT_TYPE_CHOICES = (
        ('single', 'Single Experiment'),
        ('comparison', 'Comparison Report'),
        ('summary', 'Summary Report'),
    )
    
    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    )
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    experiments = models.ManyToManyField(Experiment, related_name='reports')
    
    content = models.TextField()
    summary = models.TextField(blank=True)
    
    file_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
