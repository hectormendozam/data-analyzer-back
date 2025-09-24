import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from scipy import stats
import io
import json

class DatasetAnalyzer:
    def __init__(self, file_data):
        """
        Inicializa el analizador con datos de archivo CSV
        """
        try:
            # Resetear el puntero del archivo si es necesario
            if hasattr(file_data, 'seek'):
                file_data.seek(0)
            
            # Convertir bytes a string si es necesario
            if isinstance(file_data, bytes):
                file_content = file_data.decode('utf-8')
            else:
                file_content = str(file_data)
            
            # Crear DataFrame con manejo de errores
            self.df = pd.read_csv(io.StringIO(file_content), encoding='utf-8')
            self.original_df = self.df.copy()
            
            # Validar que el DataFrame no esté vacío
            if self.df.empty:
                raise ValueError("El archivo CSV está vacío o no contiene datos válidos")
                
        except UnicodeDecodeError as e:
            raise ValueError(f"Error de codificación del archivo: {str(e)}. Intenta guardar el CSV con codificación UTF-8")
        except pd.errors.EmptyDataError:
            raise ValueError("El archivo CSV está vacío")
        except pd.errors.ParserError as e:
            raise ValueError(f"Error al parsear el archivo CSV: {str(e)}. Verifica que el formato sea correcto")
        except Exception as e:
            raise ValueError(f"Error al procesar el archivo: {str(e)}")
        
    def get_basic_info(self):
        """
        Obtiene información básica del dataset
        """
        file_size_mb = round(self.df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        
        data_types = {
            'numeric': int(self.df.select_dtypes(include=[np.number]).shape[1]),
            'object': int(self.df.select_dtypes(include=['object']).shape[1]),
            'datetime': int(self.df.select_dtypes(include=['datetime64']).shape[1])
        }
        
        return {
            'total_rows': int(self.df.shape[0]),
            'total_columns': int(self.df.shape[1]),
            'file_size': f"{file_size_mb} MB",
            'data_types': data_types,
            'column_names': list(self.df.columns),
            'dtypes': {col: str(dtype) for col, dtype in self.df.dtypes.items()}
        }
    
    def analyze_missing_data(self):
        """
        Analiza valores faltantes en el dataset
        """
        missing_data = self.df.isnull().sum()
        total_cells = self.df.shape[0] * self.df.shape[1]
        total_missing = missing_data.sum()
        
        columns_with_missing = []
        for col in missing_data.index:
            if missing_data[col] > 0:
                columns_with_missing.append({
                    'column': col,
                    'missing_count': int(missing_data[col]),
                    'percentage': round((missing_data[col] / self.df.shape[0]) * 100, 2)
                })
        
        return {
            'columns_with_missing': columns_with_missing,
            'total_missing_percentage': round((total_missing / total_cells) * 100, 2),
            'total_missing_values': int(total_missing)
        }
    
    def analyze_duplicates(self):
        """
        Analiza datos duplicados
        """
        total_duplicates = self.df.duplicated().sum()
        duplicate_percentage = (total_duplicates / self.df.shape[0]) * 100
        
        # Encuentra columnas que más contribuyen a duplicados
        contributing_columns = []
        for col in self.df.columns:
            if self.df[col].dtype == 'object' or self.df[col].dtype.name == 'category':
                dup_in_col = self.df.duplicated(subset=[col]).sum()
                if dup_in_col > 0:
                    contributing_columns.append(col)
        
        return {
            'total_duplicates': int(total_duplicates),
            'percentage': round(duplicate_percentage, 2),
            'columns_contributing': contributing_columns[:5]  # Top 5
        }
    
    def calculate_data_quality(self):
        """
        Calcula métricas de calidad de datos
        """
        total_cells = self.df.shape[0] * self.df.shape[1]
        missing_cells = self.df.isnull().sum().sum()
        
        # Completitud
        completeness = ((total_cells - missing_cells) / total_cells) * 100
        
        # Consistencia (basada en tipos de datos esperados)
        consistency_score = 85.0  # Valor base, puede mejorarse con reglas específicas
        
        # Validez (porcentaje de valores válidos en columnas numéricas)
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        validity_scores = []
        
        for col in numeric_cols:
            # Verifica valores infinitos y NaN
            invalid_count = np.isinf(self.df[col]).sum() + self.df[col].isnull().sum()
            validity_scores.append((len(self.df) - invalid_count) / len(self.df) * 100)
        
        validity = np.mean(validity_scores) if validity_scores else 95.0
        
        # Unicidad
        duplicate_percentage = (self.df.duplicated().sum() / self.df.shape[0]) * 100
        uniqueness = 100 - duplicate_percentage
        
        return {
            'completeness': round(completeness, 1),
            'consistency': round(consistency_score, 1),
            'validity': round(validity, 1),
            'uniqueness': round(uniqueness, 1)
        }
    
    def detect_outliers(self):
        """
        Detecta valores atípicos en columnas numéricas
        """
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        outliers_info = []
        
        for col in numeric_cols:
            if self.df[col].dtype in ['int64', 'float64']:
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
                
                if len(outliers) > 0:
                    outliers_info.append({
                        'column': col,
                        'outlier_count': len(outliers),
                        'percentage': round((len(outliers) / len(self.df)) * 100, 2)
                    })
        
        return {
            'columns_with_outliers': outliers_info,
            'total_outlier_percentage': sum([item['percentage'] for item in outliers_info])
        }
    
    def calculate_correlations(self):
        """
        Calcula correlaciones entre variables numéricas
        """
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        if numeric_df.shape[1] < 2:
            return {'correlations': []}
        
        corr_matrix = numeric_df.corr()
        correlations = []
        
        # Obtiene las correlaciones más significativas
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                var1 = corr_matrix.columns[i]
                var2 = corr_matrix.columns[j]
                correlation = corr_matrix.iloc[i, j]
                
                if not np.isnan(correlation) and abs(correlation) > 0.3:
                    correlations.append({
                        'var1': var1,
                        'var2': var2,
                        'correlation': round(correlation, 3)
                    })
        
        # Ordena por correlación absoluta descendente
        correlations = sorted(correlations, key=lambda x: abs(x['correlation']), reverse=True)
        
        return {'correlations': correlations[:10]}  # Top 10
    
    def get_column_statistics(self):
        """
        Obtiene estadísticas descriptivas por columna
        """
        stats = {}
        
        for col in self.df.columns:
            if self.df[col].dtype in ['int64', 'float64']:
                stats[col] = {
                    'type': 'numeric',
                    'mean': round(self.df[col].mean(), 2) if pd.notna(self.df[col].mean()) else None,
                    'median': round(self.df[col].median(), 2) if pd.notna(self.df[col].median()) else None,
                    'std': round(self.df[col].std(), 2) if pd.notna(self.df[col].std()) else None,
                    'min': round(self.df[col].min(), 2) if pd.notna(self.df[col].min()) else None,
                    'max': round(self.df[col].max(), 2) if pd.notna(self.df[col].max()) else None,
                    'unique_values': int(self.df[col].nunique()),
                    'missing_count': int(self.df[col].isnull().sum())
                }
            else:
                value_counts = self.df[col].value_counts().head(5)
                stats[col] = {
                    'type': 'categorical',
                    'unique_values': int(self.df[col].nunique()),
                    'most_frequent': value_counts.to_dict() if not value_counts.empty else {},
                    'missing_count': int(self.df[col].isnull().sum())
                }
        
        return stats
    
    def generate_recommendations(self):
        """
        Genera recomendaciones basadas en el análisis
        """
        recommendations = {
            'critical': [],
            'moderate': [],
            'optional': []
        }
        
        # Análisis para recomendaciones críticas
        missing_data = self.analyze_missing_data()
        duplicates = self.analyze_duplicates()
        
        if missing_data['total_missing_percentage'] > 10:
            recommendations['critical'].append({
                'issue': 'Valores faltantes elevados',
                'description': f"El dataset tiene {missing_data['total_missing_percentage']}% de valores faltantes",
                'action': 'Implementar estrategias de imputación o eliminación de registros'
            })
        
        if duplicates['total_duplicates'] > 0:
            recommendations['critical'].append({
                'issue': 'Datos duplicados',
                'description': f"Se encontraron {duplicates['total_duplicates']} registros duplicados",
                'action': 'Eliminar o consolidar registros duplicados'
            })
        
        # Análisis para recomendaciones moderadas
        outliers = self.detect_outliers()
        quality = self.calculate_data_quality()
        
        if outliers['total_outlier_percentage'] > 5:
            recommendations['moderate'].append({
                'issue': 'Valores atípicos detectados',
                'description': f"Se detectaron outliers en {len(outliers['columns_with_outliers'])} columnas",
                'action': 'Revisar y decidir tratamiento de valores atípicos'
            })
        
        if quality['consistency'] < 80:
            recommendations['moderate'].append({
                'issue': 'Consistencia baja',
                'description': f"Consistencia de datos: {quality['consistency']}%",
                'action': 'Revisar formato y tipos de datos'
            })
        
        # Recomendaciones opcionales
        numeric_cols = len(self.df.select_dtypes(include=[np.number]).columns)
        if numeric_cols > 0:
            recommendations['optional'].append({
                'issue': 'Normalización de datos',
                'description': 'Considerar normalización para columnas numéricas',
                'action': 'Aplicar StandardScaler o MinMaxScaler'
            })
        
        categorical_cols = len(self.df.select_dtypes(include=['object']).columns)
        if categorical_cols > 0:
            recommendations['optional'].append({
                'issue': 'Encoding de variables categóricas',
                'description': 'Variables categóricas requieren encoding para ML',
                'action': 'Aplicar One-Hot Encoding o Label Encoding'
            })
        
        return recommendations
    
    def analyze_complete(self):
        """
        Ejecuta análisis completo del dataset
        """
        try:
            basic_info = self.get_basic_info()
            missing_data = self.analyze_missing_data()
            duplicates = self.analyze_duplicates()
            data_quality = self.calculate_data_quality()
            outliers = self.detect_outliers()
            correlations = self.calculate_correlations()
            column_stats = self.get_column_statistics()
            recommendations = self.generate_recommendations()
            
            return {
                'basic_info': basic_info,
                'missing_data': missing_data,
                'duplicates': duplicates,
                'data_quality': data_quality,
                'outliers': outliers,
                'correlation_matrix': correlations['correlations'],
                'column_statistics': column_stats,
                'recommendations': recommendations,
                'analysis_status': 'success'
            }
            
        except Exception as e:
            return {
                'analysis_status': 'error',
                'error_message': str(e)
            }