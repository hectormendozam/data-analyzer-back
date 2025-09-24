from django.db import models

class DatasetAnalysis(models.Model):
    name = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)
    analysis_result = models.JSONField(default=dict)
    file_size = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-upload_date']
        
    def __str__(self):
        return f"Analysis: {self.name}"