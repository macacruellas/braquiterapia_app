"""
Configuración general de la aplicación de Braquiterapia
"""
import os

# ====== Límites fijos de dosis en EQD2 (Gy) ======
LIMITS_EQD2 = {
    "VEJIGA": 85.0,
    "RECTO": 75.0,
    "SIGMOIDE": 75.0,
    "INTESTINO": 75.0
}

# ====== Parámetros alfa/beta para cálculos ======
ALPHA_BETA_OAR = 3.0  # Órganos en riesgo
ALPHA_BETA_CTV = 10.0  # Volumen blanco clínico

# ====== Configuración de archivos ======
ALLOWED_EXTENSIONS = {'txt', 'dvh', 'csv', 'log', 'dat', 'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# ====== Valores por defecto ======
DEFAULT_FX_RT = 25  # Número de fracciones de RT externa
DEFAULT_N_HDR = 3   # Número de sesiones HDR

# ====== Configuración de Flask ======
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# ====== Rutas de plantillas ======
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_CARTON = os.path.join(BASE_DIR, "app", "templates", "Cartón dosimétrico.xlsx")
TEMPLATE_INFORME = os.path.join(BASE_DIR, "app", "templates", "Plantilla informe medico.xlsx")
