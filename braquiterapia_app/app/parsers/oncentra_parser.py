"""
Parser para archivos DVH de Oncentra
"""
import re
from app.parsers.eclipse_parser import parse_patient_metadata


def parse_oncentra_dvh(text: str) -> dict:
    """
    Parsea un archivo DVH de Oncentra y extrae las curvas dosis-volumen.
    
    Args:
        text: Contenido del archivo DVH de Oncentra
    
    Returns:
        dict: {nombre_roi: [(dosis_Gy, volumen_cc), ...], ...}
    
    Example:
        >>> with open('oncentra_dvh.txt') as f:
        ...     data = parse_oncentra_dvh(f.read())
        >>> data['Bladder']
        [(0.0, 50.0), (1.0, 49.5), (2.0, 48.2), ...]
    """
    structures = {}
    
    # Buscar bloques ROI: (tolerante a separadores como ****, ----)
    for match in re.finditer(
        r"ROI:\s*([^\r\n]+)\s*(.*?)(?=\nROI:|\Z)",
        text,
        re.S | re.I
    ):
        roi_name = match.group(1).strip()
        block = match.group(2)
        
        # Extraer pares (dosis, volumen)
        data_points = []
        for line in block.splitlines():
            # Extraer todos los números de la línea
            numbers = re.findall(r"[-+]?\d*[\.,]?\d+", line)
            
            # Tomar las dos últimas columnas como (dosis, volumen)
            if len(numbers) >= 2:
                dose = float(numbers[-2].replace(",", "."))
                volume = float(numbers[-1].replace(",", "."))
                data_points.append((dose, volume))
        
        if data_points:
            structures[roi_name] = data_points
    
    return structures


def dose_at_percent_volume(dvh_data: list, target_percent: float) -> tuple:
    """
    Calcula la dosis a un porcentaje específico del volumen (ej: D90, D95).
    
    Args:
        dvh_data: Lista de tuplas (dosis_Gy, volumen_cc) ordenadas por dosis
        target_percent: Porcentaje del volumen objetivo (90 para D90, 95 para D95)
    
    Returns:
        tuple: (dosis_Gy, volumen_total_cc, volumen_objetivo_cc) o (None, None, None)
    
    Example:
        >>> dvh = [(0, 100), (1, 95), (2, 85), (3, 70)]
        >>> dose_at_percent_volume(dvh, 90)  # D90
        (1.5, 100, 90)  # 1.5 Gy cubre el 90% del volumen
    """
    if not dvh_data:
        return None, None, None
    
    # Ordenar por dosis ascendente
    data_sorted = sorted(dvh_data, key=lambda x: x[0])
    
    # Volumen total (máximo)
    total_volume = max(vol for _, vol in data_sorted)
    
    # Volumen objetivo
    target_volume = total_volume * (target_percent / 100.0)
    
    # Buscar interpolación
    for i in range(1, len(data_sorted)):
        dose_prev, vol_prev = data_sorted[i - 1]
        dose_curr, vol_curr = data_sorted[i]
        
        # El volumen disminuye al aumentar la dosis
        if (vol_prev >= target_volume >= vol_curr) or (vol_curr >= target_volume >= vol_prev):
            if vol_curr == vol_prev:
                return dose_curr, total_volume, target_volume
            
            # Interpolación lineal
            fraction = (target_volume - vol_prev) / (vol_curr - vol_prev)
            interpolated_dose = dose_prev + (dose_curr - dose_prev) * fraction
            return interpolated_dose, total_volume, target_volume
    
    # Si no encontramos interpolación exacta, buscar el punto más cercano
    closest_idx = min(
        range(len(data_sorted)),
        key=lambda i: abs(data_sorted[i][1] - target_volume)
    )
    closest_dose = data_sorted[closest_idx][0]
    
    return closest_dose, total_volume, target_volume


def parse_oncentra_file(file_storage, target_organs=None, ctv_percentile=90.0):
    """
    Lee y parsea un archivo DVH de Oncentra completo desde Flask FileStorage.
    
    Args:
        file_storage: Objeto FileStorage de Flask
        target_organs: Lista de órganos a extraer D2cc (ej: ['VEJIGA', 'RECTO'])
        ctv_percentile: Percentil para CTV (90 para D90, 95 para D95)
    
    Returns:
        dict: {
            'oar_d2cc': {organo: dosis_Gy, ...},
            'ctv_d90': float o None,
            'patient_name': str o None,
            'patient_id': str o None
        }
    """
    from app.utils.roi_mapping import map_roi
    from app.parsers.eclipse_parser import dose_at_volume
    
    if target_organs is None:
        target_organs = ["VEJIGA", "RECTO", "SIGMOIDE", "INTESTINO"]
    
    # Leer contenido
    text = file_storage.read().decode("latin1", errors="ignore")
    
    # Parsear estructuras
    structures = parse_oncentra_dvh(text)
    
    # Crear índice lowercase para búsqueda
    index = {name.lower(): name for name in structures.keys()}
    
    # Función auxiliar para buscar coincidencias
    def find_match(target_key):
        from app.utils.roi_mapping import ALIASES
        from app.utils.helpers import normalize_roi_token
        
        for low_name, orig_name in index.items():
            normalized = normalize_roi_token(low_name)
            if any(pattern.search(normalized) for pattern in ALIASES[target_key]):
                return orig_name
        return None
    
    # Extraer D2cc para órganos en riesgo
    oar_d2cc = {}
    for organ in target_organs:
        matched_name = find_match(organ)
        if matched_name:
            d2_dose = dose_at_volume(structures.get(matched_name, []), 2.0)
            if d2_dose is not None:
                oar_d2cc[organ] = round(float(d2_dose), 2)
    
    # Extraer D90 para CTV
    ctv_dose = None
    ctv_matched = find_match("CTV")
    if ctv_matched:
        d90, vol_total, vol_target = dose_at_percent_volume(
            structures.get(ctv_matched, []),
            ctv_percentile
        )
        if d90 is not None:
            ctv_dose = float(d90)
    
    # Extraer metadatos del paciente
    patient_name, patient_id = parse_patient_metadata(text)
    
    return {
        'oar_d2cc': oar_d2cc,
        'ctv_d90': ctv_dose,
        'patient_name': patient_name,
        'patient_id': patient_id
    }
