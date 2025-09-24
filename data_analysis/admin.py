from django.contrib import admin
from .models import DatasetAnalysis

# Versión simple del admin para evitar errores
admin.site.register(DatasetAnalysis)