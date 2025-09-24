from rest_framework import serializers
from .models import DatasetAnalysis

class DatasetAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetAnalysis
        fields = '__all__'

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    name = serializers.CharField(max_length=255, required=False)