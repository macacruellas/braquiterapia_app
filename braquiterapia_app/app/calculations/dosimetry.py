"""
Módulo de cálculos dosimétricos para braquiterapia
"""
import math


def eqd2_from_total_with_fraction(D_total, d_per_fx, alpha_beta):
    """
    Calcula EQD2 a partir de una dosis total y dosis por fracción.
    
    Formula: EQD2 = D_total * (1 + d/αβ) / (1 + 2/αβ)
    
    Args:
        D_total: Dosis total en Gy
        d_per_fx: Dosis por fracción en Gy
        alpha_beta: Relación α/β (3 para OAR, 10 para CTV)
    
    Returns:
        float: EQD2 en Gy
    """
    return (D_total * (1.0 + d_per_fx / alpha_beta)) / (1.0 + 2.0 / alpha_beta)


def eqd2_from_single_fraction(dose, alpha_beta):
    """
    Calcula EQD2 para una única fracción.
    
    Formula: EQD2 = (d + d²/αβ) / (1 + 2/αβ)
    
    Args:
        dose: Dosis de la fracción en Gy
        alpha_beta: Relación α/β
    
    Returns:
        float: EQD2 en Gy
    """
    return (dose + dose * dose / alpha_beta) / (1.0 + 2.0 / alpha_beta)


def solve_hdr_dose_per_session(eqd2_remaining, num_sessions, alpha_beta):
    """
    Resuelve la ecuación cuadrática para encontrar la dosis máxima por sesión HDR.
    
    Dado el EQD2 restante y el número de sesiones, calcula cuánta dosis
    se puede dar por sesión sin exceder el límite.
    
    Args:
        eqd2_remaining: EQD2 restante disponible en Gy
        num_sessions: Número de sesiones HDR planificadas
        alpha_beta: Relación α/β
    
    Returns:
        float: Dosis máxima por sesión en Gy
    """
    if eqd2_remaining <= 0 or num_sessions <= 0:
        return 0.0
    
    # EQD2 por sesión
    t = eqd2_remaining / float(num_sessions)
    
    # Resolver la ecuación cuadrática: d²/αβ + d - t(1 + 2/αβ) = 0
    A = 1.0 / alpha_beta
    C = -t * (1.0 + 2.0 / alpha_beta)
    
    discriminant = 1.0 - 4.0 * A * C
    if discriminant < 0:
        return 0.0
    
    # Tomar la raíz positiva
    dose = (-1.0 + math.sqrt(discriminant)) / (2.0 * A)
    return max(0.0, dose)


def calculate_remaining_dose(limit, eqd2_used):
    """
    Calcula la dosis restante disponible.
    
    Args:
        limit: Límite de dosis en EQD2 (Gy)
        eqd2_used: EQD2 ya utilizada (Gy)
    
    Returns:
        float: Dosis restante en Gy (0 si ya se excedió)
    """
    return max(0.0, limit - eqd2_used)


def total_dose_from_fractions(doses):
    """
    Suma las dosis de múltiples fracciones.
    
    Args:
        doses: Lista de dosis en Gy
    
    Returns:
        float: Dosis total
    """
    return sum(doses)


def calculate_bed(dose, alpha_beta):
    """
    Calcula la Dosis Biológica Efectiva (BED).
    
    Formula: BED = d * (1 + d/αβ)
    
    Args:
        dose: Dosis física en Gy
        alpha_beta: Relación α/β
    
    Returns:
        float: BED en Gy
    """
    return dose * (1.0 + dose / alpha_beta)
