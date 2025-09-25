from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def root_view(request):
    return JsonResponse({
        'message': 'Dataset Analyzer API',
        'status': 'running',
        'available_endpoints': [
            '/api/health/',
            '/api/upload/',
            '/api/analyses/',
            '/admin/',
        ]
    })

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/', include('data_analysis.urls')),
]