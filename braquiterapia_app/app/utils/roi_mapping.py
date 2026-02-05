"""
Definición de aliases para Regiones de Interés (ROI)
Mapea nombres en inglés/español a nombres estandarizados
"""
import re

# ====== Aliases ROI EN/ES ======
ALIASES = {
    "VEJIGA": [
        re.compile(r"\bbladder\b", re.I),
        re.compile(r"\bvejig", re.I)
    ],
    
    "RECTO": [
        re.compile(r"\brectum\b", re.I),
        re.compile(r"\brecto\b", re.I)
    ],
    
    # === INTESTINO GRUESO (SIGMOIDE / COLON) ===
    "SIGMOIDE": [
        re.compile(r"\bsigmoid\b", re.I),
        re.compile(r"\bsigmoide\b", re.I),
        re.compile(r"\bsigma\b", re.I),
        re.compile(r"\bcolon\b", re.I),
        re.compile(r"\bcolon[_\s-]*sigmoid[eo]\b", re.I),
        re.compile(r"\brecto[_\s-]*sigmoid[eo]\b", re.I),
        re.compile(r"\brectosigmoid[eo]\b", re.I),
        re.compile(r"\bintestino\s+grueso\b", re.I),
        re.compile(r"\bbowel[_\s-]?large\b", re.I),
    ],
    
    # === INTESTINO DELGADO (SMALL BOWEL) ===
    "INTESTINO": [
        re.compile(r"\bbowel[_\s-]?small\b", re.I),
        re.compile(r"\bsmall\s*bowel\b", re.I),
        re.compile(r"\bintestino\s+delgado\b", re.I),
        re.compile(r"\bintestino(?!\s+grueso)\b", re.I),
        re.compile(r"\bduoden(?:o|um)\b", re.I),
        re.compile(r"\byeyun(?:o|um)\b", re.I),
        re.compile(r"\bíle(?:on|um)\b", re.I),
    ],
    
    # === CTV ===
    "CTV": [
        re.compile(r"\bCTV\b", re.I),
        re.compile(r"\bCTV[_\s-]*HR\b", re.I),
        re.compile(r"\bHR[_\s-]*CTV\b", re.I),
        re.compile(r"\bCTVHR\b", re.I),
        re.compile(r"\bCTV[_\s-]*(uterus|utero|útero)\b", re.I),
        re.compile(r"\bvolumen\s*cl[ií]nico", re.I)
    ]
}


def map_roi(roi_name):
    """
    Mapea un nombre de ROI a su categoría estandarizada.
    
    Args:
        roi_name: Nombre del ROI (puede estar en inglés o español)
    
    Returns:
        str o None: Categoría estandarizada o None si no se encuentra
    
    Examples:
        >>> map_roi("Bladder")
        'VEJIGA'
        >>> map_roi("sigmoid colon")
        'SIGMOIDE'
        >>> map_roi("small bowel")
        'INTESTINO'
    """
    low = roi_name.lower()
    
    # Buscar en aliases con regex
    for category, patterns in ALIASES.items():
        if any(pattern.search(low) for pattern in patterns):
            return category
    
    # Búsqueda simple por substring (fallback)
    for category in ("VEJIGA", "RECTO", "SIGMOIDE", "INTESTINO", "CTV"):
        if category.lower() in low:
            return category
    
    return None


def get_display_name(roi_key):
    """
    Obtiene el nombre de visualización en español para una categoría de ROI.
    
    Args:
        roi_key: Clave de la categoría (VEJIGA, RECTO, etc.)
    
    Returns:
        str: Nombre formateado para mostrar
    """
    display_names = {
        "VEJIGA": "Vejiga",
        "RECTO": "Recto",
        "SIGMOIDE": "Sigmoide",
        "INTESTINO": "Intestino",
        "CTV": "CTV"
    }
    return display_names.get(roi_key, roi_key)


def get_all_categories():
    """
    Devuelve todas las categorías de ROI disponibles.
    
    Returns:
        list: Lista de categorías
    """
    return list(ALIASES.keys())
