"""
Funciones de utilidad general
"""
import re


def fnum(s, default=0.0):
    """
    Convierte un string a float, manejando errores.
    
    Args:
        s: String a convertir
        default: Valor por defecto si falla la conversión
    
    Returns:
        float: Número convertido o valor por defecto
    """
    if s is None:
        return default
    s = str(s).strip().replace(",", ".")
    if s == "":
        return default
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def normalize_roi_token(s: str) -> str:
    """
    Normaliza un nombre de ROI quitando prefijos numéricos.
    Ejemplo: "1_Vejiga" -> "vejiga"
    
    Args:
        s: String del ROI
    
    Returns:
        str: ROI normalizado en minúsculas
    """
    return re.sub(r'^\s*\d+[_\s\-]*', '', s.strip().lower())


def normalize_patient_name(name: str) -> str:
    """
    Normaliza el nombre de un paciente para comparaciones.
    
    Args:
        name: Nombre del paciente
    
    Returns:
        str: Nombre normalizado en mayúsculas sin espacios extras
    """
    if not name:
        return ""
    return name.strip().upper()


def parse_patient_name(full_name: str) -> tuple:
    """
    Separa un nombre completo en apellido y nombre.
    Maneja formato "Apellido, Nombre" y "Nombre Apellido"
    
    Args:
        full_name: Nombre completo del paciente
    
    Returns:
        tuple: (apellido, nombre)
    """
    full_name = full_name.strip()
    apellido = ""
    nombre = ""
    
    if "," in full_name:
        parts = [p.strip() for p in full_name.split(",", 1)]
        apellido, nombre = parts[0], parts[1]
    elif full_name:
        parts = full_name.split()
        apellido = parts[0]
        nombre = " ".join(parts[1:])
    
    return apellido, nombre


def safe_float(x):
    """
    Convierte a float de manera segura, devolviendo None si falla.
    
    Args:
        x: Valor a convertir
    
    Returns:
        float o None
    """
    try:
        if x is None:
            return None
        return float(x)
    except (ValueError, TypeError):
        return None


def round_2_decimals(x):
    """
    Redondea a 2 decimales si es posible.
    
    Args:
        x: Número a redondear
    
    Returns:
        float redondeado o valor original
    """
    try:
        if x is None:
            return None
        return round(float(x), 2)
    except (ValueError, TypeError):
        return x
