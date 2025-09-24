from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser, FormParser
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import io
import logging
import traceback

from .models import DatasetAnalysis
from .serializers import DatasetAnalysisSerializer, FileUploadSerializer
from .analyzers import DatasetAnalyzer

# Configurar logging
logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class UploadAndAnalyzeView(APIView):
    parser_classes = (MultiPartParser, FileUploadParser, FormParser)
    
    def post(self, request, format=None):
        """
        Upload CSV file and analyze it
        """
        try:
            logger.info("Iniciando nuevo análisis de dataset")
            
            file_serializer = FileUploadSerializer(data=request.data)
            
            if not file_serializer.is_valid():
                logger.error(f"Serializer inválido: {file_serializer.errors}")
                return Response({
                    'error': 'Archivo inválido',
                    'details': file_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES.get('file')
            
            if not uploaded_file:
                logger.error("No se proporcionó archivo")
                return Response({
                    'error': 'No se proporcionó archivo'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not uploaded_file.name.endswith('.csv'):
                logger.error(f"Tipo de archivo inválido: {uploaded_file.name}")
                return Response({
                    'error': 'Solo se admiten archivos CSV'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Procesando archivo: {uploaded_file.name}, tamaño: {uploaded_file.size} bytes")
            
            # Lee el contenido del archivo
            file_content = uploaded_file.read()
            logger.info(f"Archivo leído correctamente, {len(file_content)} bytes")
            
            # Crea el analizador y ejecuta análisis
            try:
                analyzer = DatasetAnalyzer(file_content)
                logger.info("Analizador creado exitosamente")
                
                analysis_result = analyzer.analyze_complete()
                logger.info("Análisis completado")
                
            except Exception as analyzer_error:
                logger.error(f"Error en el analizador: {str(analyzer_error)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return Response({
                    'error': 'Error al analizar el archivo',
                    'details': str(analyzer_error)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            if analysis_result.get('analysis_status') == 'error':
                logger.error(f"Error en análisis: {analysis_result.get('error_message')}")
                return Response({
                    'error': 'Error al analizar el archivo',
                    'details': analysis_result.get('error_message', 'Error desconocido')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Guarda el análisis en la base de datos (opcional)
            try:
                dataset_analysis = DatasetAnalysis.objects.create(
                    name=file_serializer.validated_data.get('name', uploaded_file.name),
                    file_name=uploaded_file.name,
                    file_size=uploaded_file.size,
                    analysis_result=analysis_result
                )
                logger.info(f"Análisis guardado con ID: {dataset_analysis.id}")
            except Exception as db_error:
                logger.warning(f"Error al guardar en BD: {str(db_error)}")
                # Continuar sin guardar en BD
            
            return Response({
                'analysis_id': dataset_analysis.id if 'dataset_analysis' in locals() else None,
                'analysis': analysis_result,
                'message': 'Análisis completado exitosamente'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error interno del servidor: {str(e)}")
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            return Response({
                'error': 'Error interno del servidor',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AnalysisListView(APIView):
    """
    Lista todos los análisis guardados
    """
    def get(self, request):
        analyses = DatasetAnalysis.objects.all()
        serializer = DatasetAnalysisSerializer(analyses, many=True)
        return Response(serializer.data)

class AnalysisDetailView(APIView):
    """
    Obtiene detalles de un análisis específico
    """
    def get(self, request, analysis_id):
        try:
            analysis = DatasetAnalysis.objects.get(id=analysis_id)
            serializer = DatasetAnalysisSerializer(analysis)
            return Response(serializer.data)
        except DatasetAnalysis.DoesNotExist:
            return Response({
                'error': 'Análisis no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

class HealthCheckView(APIView):
    """
    Health check endpoint
    """
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'Dataset Analyzer API',
            'version': '1.0.0'
        })