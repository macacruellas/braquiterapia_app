"""
Parser para archivos DVH de Eclipse
"""
import re
from app.utils.helpers import normalize_roi_token
from app.utils.roi_mapping import map_roi


def normalize_eclipse_labels(text: str) -> str:
    """
    Normaliza etiquetas de archivos Eclipse en español a inglés estándar.
    
    Esto permite procesar archivos exportados de Eclipse en español
    con la misma lógica que los archivos en inglés.
    
    Args:
        text: Contenido del archivo DVH
    
    Returns:
        str: Texto con etiquetas normalizadas
    """
    # Reglas de normalización ES → EN
    norm_rules = [
        (r'^\s*Estructura\s*:', 'Structure:', re.I),
        (r'^\s*Estado\s+de\s+la\s+aprobación\s*:', 'Approval Status:', re.I),
        (r'^\s*Nombre\s+de\s+paciente\s*:', 'Patient Name          :', re.I),
        (r'^\s*ID\s+paciente\s*:', 'Patient ID          :', re.I),
        (r'^\s*Descripción\s*:', 'Description          :', re.I),
        (r'^\s*Dosis\s*\[\s*cGy\s*\]', 'Dose [cGy]', re.I),
        (r'Dosis\s+relativa\s*\[\s*%\s*\]', 'Relative dose [%]', re.I),
        (r'Volumen\s+de\s+estructura\s*\[\s*cm³\s*\]', 'Structure Volume [cm³]', re.I),
    ]
    
    lines = text.splitlines()
    output_lines = []
    
    for line in lines:
        normalized_line = line
        for pattern, replacement, flags in norm_rules:
            normalized_line = re.sub(pattern, replacement, normalized_line, flags=flags)
        output_lines.append(normalized_line)
    
    return "\n".join(output_lines)


def parse_eclipse_dvh(text: str) -> dict:
    """
    Parsea un archivo DVH de Eclipse y extrae las curvas dosis-volumen.
    
    Args:
        text: Contenido del archivo DVH
    
    Returns:
        dict: {nombre_estructura: [(dosis_Gy, volumen_cc), ...], ...}
    
    Example:
        >>> with open('dvh.txt') as f:
        ...     data = parse_eclipse_dvh(f.read())
        >>> data['Bladder']
        [(0.0, 50.0), (1.0, 49.5), (2.0, 48.2), ...]
    """
    structures = {}
    
    # Buscar bloques de cada estructura
    for match in re.finditer(
        r"Structure:\s*(.+?)\n(.*?)(?=\nStructure:|\Z)", 
        text, 
        re.S
    ):
        structure_name = match.group(1).strip()
        block = match.group(2)
        
        # Verificar que tenga datos de DVH
        if not re.search(r"Dose\s*\[(?:cGy|Gy)\].*Structure Volume", block, re.I):
            continue
        
        # Detectar si la dosis está en cGy o Gy
        dose_in_cgy = bool(re.search(r"Dose\s*\[cGy\]", block, re.I))
        
        # Extraer pares (dosis, volumen)
        data_points = []
        for line in block.splitlines():
            # Buscar líneas con números
            if not re.search(r"\d", line):
                continue
            
            # Extraer todos los números de la línea
            numbers = re.findall(r"[-+]?\d*[\.,]?\d+", line)
            
            # Necesitamos al menos 3 columnas: Dosis, %, Volumen
            if len(numbers) >= 3:
                dose = float(numbers[0].replace(",", "."))
                volume = float(numbers[2].replace(",", "."))
                
                # Convertir cGy a Gy si es necesario
                if dose_in_cgy:
                    dose /= 100.0
                
                data_points.append((dose, volume))
        
        if data_points:
            structures[structure_name] = data_points
    
    return structures


def parse_patient_metadata(text: str) -> tuple:
    """
    Extrae metadatos del paciente del archivo DVH.
    
    Args:
        text: Contenido del archivo DVH
    
    Returns:
        tuple: (nombre_paciente, id_paciente)
    
    Example:
        >>> text = "Patient Name: García, Juan\\nPatient ID: 12345"
        >>> parse_patient_metadata(text)
        ('García, Juan', '12345')
    """
    patient_name = None
    patient_id = None
    
    # Buscar nombre del paciente
    # Regex mejorada para evitar capturar "Patient ID"
    name_match = re.search(
        r'(?:Patient\s*Name|Nombre\s+de\s+paciente|\bPatient\b(?!\s*ID))\s*:\s*([^\r\n]+)',
        text,
        re.I
    )
    if name_match:
        raw_name = name_match.group(1).strip()
        # Limpiar paréntesis y comas finales
        clean_name = re.sub(r'\s*\([^)]*\)', '', raw_name).strip()
        clean_name = re.sub(r'\s*,\s*$', '', clean_name)
        patient_name = clean_name if clean_name else raw_name
    
    # Buscar ID del paciente
    id_match = re.search(
        r'(?:Patient\s*ID|ID\s+paciente)\s*:\s*([^\r\n]+)',
        text,
        re.I
    )
    if id_match:
        raw_id = id_match.group(1).strip()
        # Extraer solo el ID numérico/alfanumérico principal
        id_number_match = re.search(r'[\w-]+', raw_id)
        patient_id = id_number_match.group(0) if id_number_match else raw_id
    
    return patient_name, patient_id


def dose_at_volume(dvh_data: list, target_volume_cc: float) -> float:
    """
    Interpola la dosis a un volumen específico en cc.
    
    Args:
        dvh_data: Lista de tuplas (dosis_Gy, volumen_cc)
        target_volume_cc: Volumen objetivo en cc
    
    Returns:
        float o None: Dosis en Gy, o None si no hay datos
    
    Example:
        >>> dvh = [(0, 50), (1, 45), (2, 40), (3, 35)]
        >>> dose_at_volume(dvh, 42.5)  # Interpola entre 1 y 2 Gy
        1.5
    """
    if not dvh_data:
        return None
    
    for i, (dose, volume) in enumerate(dvh_data):
        if volume <= target_volume_cc:
            # Si es el primer punto, no hay interpolación
            if i == 0:
                return dose
            
            # Interpolación lineal
            dose_prev, volume_prev = dvh_data[i - 1]
            if volume_prev == volume:
                return dose
            
            fraction = (target_volume_cc - volume_prev) / (volume - volume_prev)
            interpolated_dose = dose_prev + (dose - dose_prev) * fraction
            return interpolated_dose
    
    # Si no encontramos, devolvemos None
    return None


def parse_eclipse_file(file_storage) -> dict:
    """
    Lee y parsea un archivo DVH de Eclipse completo desde Flask FileStorage.
    
    Args:
        file_storage: Objeto FileStorage de Flask
    
    Returns:
        dict: {
            'structures': {nombre: [(dose, vol), ...]},
            'patient_name': str o None,
            'patient_id': str o None
        }
    """
    # Leer contenido con encoding latin1 (común en Eclipse)
    raw_text = file_storage.read().decode("latin1", errors="ignore")
    
    # Normalizar etiquetas ES → EN
    normalized_text = normalize_eclipse_labels(raw_text)
    
    # Parsear estructuras
    structures = parse_eclipse_dvh(normalized_text)
    
    # Extraer metadatos del paciente
    patient_name, patient_id = parse_patient_metadata(normalized_text)
    
    return {
        'structures': structures,
        'patient_name': patient_name,
        'patient_id': patient_id
    }
