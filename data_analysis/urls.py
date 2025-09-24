from django.urls import path
from .views import (
    UploadAndAnalyzeView,
    AnalysisListView,
    AnalysisDetailView,
    HealthCheckView
)

app_name = 'data_analysis'

urlpatterns = [
    path('upload/', UploadAndAnalyzeView.as_view(), name='upload-analyze'),
    path('analyses/', AnalysisListView.as_view(), name='analysis-list'),
    path('analyses/<int:analysis_id>/', AnalysisDetailView.as_view(), name='analysis-detail'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]