"""
Rutas para carga de archivos DVH y cálculos dosimétricos
"""
from flask import Blueprint, render_template, request
from app.parsers.eclipse_parser import parse_eclipse_file, dose_at_volume
from app.parsers.oncentra_parser import parse_oncentra_file
from app.calculations.dosimetry import (
    eqd2_from_total_with_fraction,
    eqd2_from_single_fraction,
    solve_hdr_dose_per_session
)
from app.utils.helpers import fnum, normalize_patient_name
from app.utils.roi_mapping import map_roi, ALIASES
from config.settings import LIMITS_EQD2, ALPHA_BETA_OAR, ALPHA_BETA_CTV

bp = Blueprint('dvh', __name__)


# Clase auxiliar para crear objetos tipo Row
class Row:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@bp.route("/cargar_dvh", methods=["POST"])
def cargar_dvh():
    """
    Procesa la carga del archivo DVH de RT externa (Eclipse) o entrada manual.
    Calcula EQD2 de RT externa y dosis máxima por sesión HDR permitida.
    """
    # Parámetros básicos
    fx_rt = int(fnum(request.form.get("fx_rt"), 25))
    n_hdr = int(fnum(request.form.get("n_hdr"), 3))
    
    # Detectar modo manual vs archivo
    manual_mode = (request.form.get("manual_mode") == "1")
    
    # Datos del paciente (modo manual)
    patient_name_manual = (request.form.get("patient_name_manual") or "").strip() or None
    patient_id_manual = (request.form.get("patient_id_manual") or "").strip() or None
    
    # Valores manuales de dosis
    manual_vals = {
        "VEJIGA": fnum(request.form.get("manual_VEJIGA"), None),
        "RECTO": fnum(request.form.get("manual_RECTO"), None),
        "SIGMOIDE": fnum(request.form.get("manual_SIGMOIDE"), None),
        "INTESTINO": fnum(request.form.get("manual_INTESTINO"), None),
    }
    manual_ctv_d95 = fnum(request.form.get("manual_CTV_D95"), None)
    
    # Límites personalizados
    def _clamp(x, lo=0.0, hi=500.0):
        try:
            if x is None:
                return None
            return max(lo, min(hi, float(x)))
        except:
            return None
    
    user_limits = {
        "VEJIGA": _clamp(fnum(request.form.get("limit_VEJIGA"), LIMITS_EQD2["VEJIGA"])),
        "RECTO": _clamp(fnum(request.form.get("limit_RECTO"), LIMITS_EQD2["RECTO"])),
        "SIGMOIDE": _clamp(fnum(request.form.get("limit_SIGMOIDE"), LIMITS_EQD2["SIGMOIDE"])),
        "INTESTINO": _clamp(fnum(request.form.get("limit_INTESTINO"), LIMITS_EQD2["INTESTINO"])),
    }
    
    # Asegurar valores por defecto
    for k, default_v in LIMITS_EQD2.items():
        if user_limits.get(k) is None:
            user_limits[k] = default_v
    
    # Variables de salida
    d2_autofill = {}
    patient_name, patient_id = None, None
    ctv_d95_gy = None
    
    if manual_mode:
        # ===== MODO MANUAL =====
        patient_name = patient_name_manual
        patient_id = patient_id_manual
        
        for organ in ("VEJIGA", "RECTO", "SIGMOIDE", "INTESTINO"):
            val = manual_vals.get(organ)
            d2_autofill[organ] = (round(val, 2) if (val is not None and val > 0) else None)
        
        if manual_ctv_d95 is not None and manual_ctv_d95 > 0:
            ctv_d95_gy = round(manual_ctv_d95, 2)
    
    else:
        # ===== MODO ARCHIVO (Eclipse) =====
        file = request.files.get("dvhfile")
        if not file or not file.filename:
            return render_template(
                'home.html',
                css="",
                fx_rt=fx_rt,
                n_hdr=n_hdr,
                step1=False,
                limits=user_limits,
                error="Error: No se seleccionó ningún archivo DVH."
            )
        
        # Parsear archivo Eclipse
        parsed_data = parse_eclipse_file(file)
        patient_name = parsed_data['patient_name']
        patient_id = parsed_data['patient_id']
        tables = parsed_data['structures']
        
        # Crear índice lowercase para búsqueda
        idx = {name.lower(): name for name in tables.keys()}
        
        def find_match(target: str):
            """Busca una estructura que coincida con los aliases del target"""
            from app.utils.helpers import normalize_roi_token
            for low, orig in idx.items():
                low_norm = normalize_roi_token(low)
                if any(p.search(low_norm) for p in ALIASES[target]):
                    return orig
            return None
        
        # Extraer D2cc para OARs
        for organ in ("VEJIGA", "RECTO", "SIGMOIDE", "INTESTINO"):
            nm = find_match(organ)
            d2 = dose_at_volume(tables.get(nm, []), 2.0) if nm else None
            d2_autofill[organ] = round(d2, 2) if d2 is not None else None
        
        # Extraer D95 para CTV
        nm_ctv = find_match("CTV")
        if nm_ctv:
            from app.parsers.oncentra_parser import dose_at_percent_volume
            d95, Vtot, Vtarget = dose_at_percent_volume(tables.get(nm_ctv, []), 95.0)
            if d95 is not None:
                ctv_d95_gy = round(d95, 2)
    
    # ===== CONSTRUIR RESULTADOS =====
    results = []
    
    for organ, label in [
        ("VEJIGA", "Vejiga"),
        ("RECTO", "Recto"),
        ("SIGMOIDE", "Sigmoide"),
        ("INTESTINO", "Intestino"),
    ]:
        D_ext = d2_autofill.get(organ)
        ab = ALPHA_BETA_OAR
        limit = user_limits[organ]
        d_rt = (D_ext / fx_rt) if (D_ext is not None and fx_rt > 0) else 0.0
        eqd2_ext = eqd2_from_total_with_fraction(D_ext, d_rt, ab) if D_ext is not None else 0.0
        rem = max(0.0, limit - eqd2_ext)
        dmax = solve_hdr_dose_per_session(rem, n_hdr, ab)
        
        results.append(Row(
            roi=label,
            D_ext=(f"{D_ext:.2f}" if D_ext is not None else None),
            fx_rt=fx_rt,
            d_rt=d_rt,
            ab=ab,
            eqd2_ext=eqd2_ext,
            hdr_prev=0.0,
            used=eqd2_ext,
            limit=limit,
            rem=rem,
            N=n_hdr,
            dmax_session=dmax,
            flag=("ok" if rem > 0 else "warn"),
            is_ctv_d95=False
        ))
    
    # Agregar CTV si existe
    if ctv_d95_gy is not None:
        d_per_fx_ctv = (ctv_d95_gy / fx_rt) if fx_rt > 0 else 0.0
        eqd2_ctv_ext = eqd2_from_total_with_fraction(ctv_d95_gy, d_per_fx_ctv, ALPHA_BETA_CTV)
        results.append(Row(
            roi="CTV",
            D_ext=f"{ctv_d95_gy:.2f}",
            fx_rt=fx_rt,
            d_rt=d_per_fx_ctv,
            ab=ALPHA_BETA_CTV,
            eqd2_ext=eqd2_ctv_ext,
            hdr_prev=0.0,
            used=0.0,
            limit=None,
            rem=None,
            N=n_hdr,
            dmax_session=None,
            flag=None,
            is_ctv_d95=True
        ))
    
    # Ordenar: CTV primero, luego Recto, Vejiga, Sigmoide, Intestino
    order_map = {"CTV": 0, "Recto": 1, "Vejiga": 2, "Sigmoide": 3, "Intestino": 4}
    results.sort(key=lambda r: order_map.get(getattr(r, "roi", ""), 999))
    
    return render_template(
        'home.html',
        fx_rt=fx_rt,
        n_hdr=n_hdr,
        step1=True,
        results=results,
        patient_name=patient_name,
        patient_id=patient_id,
        limits=user_limits,
        ctv_volume_total=None,
        ctv_d90_gy=None,
        ctv_d90_cgy=None
    )


@bp.route("/calcular_hdr", methods=["POST"])
def calcular_hdr():
    """
    Procesa los archivos DVH de braquiterapia (Oncentra) y calcula dosis totales.
    Genera el resumen dosimétrico completo (RT externa + HDR).
    """
    # Parámetros base
    fx_rt = int(fnum(request.form.get("fx_rt"), 25))
    n_hdr = int(fnum(request.form.get("n_hdr"), 3))
    
    # Recuperar datos del paciente
    patient_name = request.form.get("patient_name") or None
    patient_id = request.form.get("patient_id") or None
    
    # Límites por órgano
    limits_map = {
        "Vejiga": LIMITS_EQD2["VEJIGA"],
        "Recto": LIMITS_EQD2["RECTO"],
        "Sigmoide": LIMITS_EQD2["SIGMOIDE"],
        "Intestino": LIMITS_EQD2["INTESTINO"],
    }
    
    # Recuperar EBRT del Paso 1
    ebrt = []
    for i in range(4):
        roi = request.form.get(f"EBRT_{i}_roi")
        if not roi:
            continue
        limit_val = request.form.get(f"EBRT_{i}_limit")
        
        item = {
            "roi": roi,
            "eqd2": fnum(request.form.get(f"EBRT_{i}_eqd2")),
            "limit": (fnum(limit_val) if limit_val is not None and limit_val != "" else None),
            "dext": request.form.get(f"EBRT_{i}_dext") or None,
        }
        ebrt.append(item)
        
        # Actualizar limits_map
        lim = item.get("limit")
        if roi in limits_map and lim is not None:
            try:
                limits_map[roi] = float(lim)
            except:
                pass
    
    # CTV de EBRT
    ctv_d95_hidden = request.form.get("EBRT_CTV_D95")
    ctv_eqd2_hidden = request.form.get("EBRT_CTV_EQD2")
    
    # Generar results_preview para mostrar tabla EBRT
    results_preview = []
    for item in ebrt:
        roi = item["roi"]
        eqd2 = item["eqd2"]
        limit = item["limit"]
        dext = item["dext"]
        if limit is not None:
            rem = max(0.0, limit - eqd2)
            dmax = solve_hdr_dose_per_session(rem, n_hdr, ALPHA_BETA_OAR)
            flag = "ok" if rem > 0 else "warn"
        else:
            rem = dmax = flag = None
        
        results_preview.append(Row(
            roi=roi,
            D_ext=dext,
            fx_rt=fx_rt,
            d_rt=0.0,
            ab=ALPHA_BETA_OAR,
            eqd2_ext=eqd2,
            hdr_prev=0.0,
            used=eqd2,
            limit=limit,
            rem=rem,
            N=n_hdr,
            dmax_session=dmax,
            flag=flag,
            is_ctv_d95=False,
        ))
    
    # Agregar CTV a results_preview
    if ctv_d95_hidden:
        results_preview.append(Row(
            roi="CTV",
            D_ext=ctv_d95_hidden,
            fx_rt=fx_rt,
            d_rt=0.0,
            ab=ALPHA_BETA_CTV,
            eqd2_ext=(float(ctv_eqd2_hidden) if ctv_eqd2_hidden else None),
            hdr_prev=0.0,
            used=0.0,
            limit=None,
            rem=None,
            N=n_hdr,
            dmax_session=None,
            flag=None,
            is_ctv_d95=True
        ))
    
    # ===== LEER ARCHIVOS HDR (Oncentra) =====
    try:
        n_ses = int(request.form.get("n_sesiones", "1"))
        n_ses = max(1, min(3, n_ses))
    except:
        n_ses = 1
    
    hdr_d2_files = []
    ctv_d90_files = []
    
    for i in range(1, n_ses + 1):
        f = request.files.get(f"hdrfile_{i}")
        
        if not f or not f.filename.strip():
            msg = f"Error de archivo: Falta cargar el archivo de la sesión {i}."
            limits_caps = {
                "VEJIGA": limits_map.get("Vejiga", LIMITS_EQD2["VEJIGA"]),
                "RECTO": limits_map.get("Recto", LIMITS_EQD2["RECTO"]),
                "SIGMOIDE": limits_map.get("Sigmoide", LIMITS_EQD2["SIGMOIDE"]),
                "INTESTINO": limits_map.get("Intestino", LIMITS_EQD2["INTESTINO"]),
            }
            return render_template(
                'home.html',
                fx_rt=fx_rt,
                n_hdr=n_hdr,
                step1=True,
                results=results_preview,
                plan_real=[],
                plan_summary=[],
                patient_name=patient_name,
                patient_id=patient_id,
                limits=limits_caps,
                error=msg
            )
        
        # Parsear archivo Oncentra
        parsed = parse_oncentra_file(f)
        hdr_d2 = parsed['oar_d2cc']
        ctv_d90_gy = parsed['ctv_d90']
        hdr_name = parsed['patient_name']
        hdr_pid = parsed['patient_id']
        
        # Validar paciente
        if (patient_name or patient_id) and (hdr_name or hdr_pid):
            norm_patient_id = normalize_patient_name(patient_id or "")
            norm_hdr_pid = normalize_patient_name(hdr_pid or "")
            
            is_same_patient = True
            if norm_patient_id and norm_hdr_pid:
                if norm_patient_id != norm_hdr_pid:
                    is_same_patient = False
            elif normalize_patient_name(patient_name or "") != normalize_patient_name(hdr_name or ""):
                is_same_patient = False
            
            if not is_same_patient:
                msg = (
                    f"Error de Paciente: Los archivos no coinciden.\n\n"
                    f"El paciente del plan de RT Externa (Paso 1) es diferente al del archivo de Braquiterapia (Paso 2, Sesión {i}).\n\n"
                    f"Paciente (RT Externa): {patient_name or 'N/A'} (ID: {patient_id or 'N/A'})\n"
                    f"Paciente (Braquiterapia): {hdr_name or 'N/A'} (ID: {hdr_pid or 'N/A'})\n\n"
                    f"Por favor, verifique que sean del mismo paciente."
                )
                limits_caps = {
                    "VEJIGA": limits_map.get("Vejiga", LIMITS_EQD2["VEJIGA"]),
                    "RECTO": limits_map.get("Recto", LIMITS_EQD2["RECTO"]),
                    "SIGMOIDE": limits_map.get("Sigmoide", LIMITS_EQD2["SIGMOIDE"]),
                    "INTESTINO": limits_map.get("Intestino", LIMITS_EQD2["INTESTINO"]),
                }
                return render_template(
                    'home.html',
                    fx_rt=fx_rt,
                    n_hdr=n_hdr,
                    step1=True,
                    results=results_preview,
                    plan_real=[],
                    plan_summary=[],
                    patient_name=patient_name,
                    patient_id=patient_id,
                    limits=limits_caps,
                    error=msg
                )
        
        hdr_d2_files.append(hdr_d2)
        ctv_d90_files.append(ctv_d90_gy)
    
    # ===== CONSTRUIR PLAN HDR =====
    def pick_file_index(col_idx: int, n_sesiones: int) -> int:
        if n_sesiones <= 1:
            return 0
        if n_sesiones == 2:
            return 0 if col_idx == 0 else 1
        return col_idx if col_idx < n_sesiones else n_sesiones - 1
    
    plan = []
    
    # CTV (α/β = 10)
    any_ctv = any(d is not None for d in ctv_d90_files)
    if any_ctv:
        doses_ctv = []
        for j in range(n_hdr):
            idx = pick_file_index(j, len(ctv_d90_files))
            d = ctv_d90_files[idx] or 0.0
            doses_ctv.append(float(d))
        eqd2s_ctv = [eqd2_from_single_fraction(d, ALPHA_BETA_CTV) for d in doses_ctv]
        eqd2_hdr_ctv_total = sum(eqd2s_ctv)
        eqd2_ebrt_ctv = float(ctv_eqd2_hidden) if ctv_eqd2_hidden else 0.0
        
        plan.append(Row(
            roi="CTV",
            doses=doses_ctv,
            eqd2s=eqd2s_ctv,
            total_dose=sum(doses_ctv),
            eqd2_hdr_total=eqd2_hdr_ctv_total,
            eqd2_ebrt=eqd2_ebrt_ctv,
            eqd2_total=eqd2_ebrt_ctv + eqd2_hdr_ctv_total,
            limit=None,
            is_ctv=True
        ))
    
    # OARs (α/β = 3)
    order = [("RECTO", "Recto"), ("VEJIGA", "Vejiga"), ("SIGMOIDE", "Sigmoide"), ("INTESTINO", "Intestino")]
    for key, display in order:
        per_fx_doses = []
        for j in range(n_hdr):
            idx = pick_file_index(j, len(hdr_d2_files))
            dose = float(hdr_d2_files[idx].get(key, 0.0))
            per_fx_doses.append(dose)
        
        eqd2s = [eqd2_from_single_fraction(d, ALPHA_BETA_OAR) for d in per_fx_doses]
        total_dose = sum(per_fx_doses)
        eqd2_hdr_total = sum(eqd2s)
        eqd2_ebrt = next((item["eqd2"] for item in ebrt if item["roi"] == display), 0.0)
        eqd2_total = eqd2_ebrt + eqd2_hdr_total
        limit = limits_map.get(display, None)
        
        plan.append(Row(
            roi=display,
            doses=per_fx_doses,
            eqd2s=eqd2s,
            total_dose=total_dose,
            eqd2_hdr_total=eqd2_hdr_total,
            eqd2_ebrt=eqd2_ebrt,
            eqd2_total=eqd2_total,
            limit=limit,
            is_ctv=False
        ))
    
    # Resumen dosimétrico
    plan_summary = []
    for r in plan:
        is_ctv = getattr(r, "is_ctv", False)
        roi_name = "CTV" if is_ctv else r.roi
        plan_summary.append({
            "roi": roi_name,
            "eqd2_ebrt": r.eqd2_ebrt,
            "eqd2_hdr": r.eqd2_hdr_total,
            "eqd2_total": r.eqd2_total,
            "limit": (None if is_ctv else limits_map.get(roi_name)),
        })
    
    # Datos para exportación
    def _sf(x):
        try:
            if x is None:
                return None
            return float(x)
        except:
            return None
    
    export_data = {
        "patient_name": patient_name,
        "patient_id": patient_id,
        "fx_rt": fx_rt,
        "n_hdr": n_hdr,
        "summary": [
            {
                "roi": item["roi"],
                "eqd2_ebrt": _sf(item["eqd2_ebrt"]),
                "eqd2_hdr": _sf(item["eqd2_hdr"]),
                "eqd2_total": _sf(item["eqd2_total"]),
            }
            for item in plan_summary
        ],
        "ebrt": [
            {
                "roi": ("CTV" if getattr(r, "is_ctv_d95", False) else getattr(r, "roi", "")),
                "D_ext": _sf(getattr(r, "D_ext", None)),
                "eqd2_ext": _sf(getattr(r, "eqd2_ext", None))
            }
            for r in results_preview
        ],
        "hdr_fractions": [
            {
                "roi": getattr(r, "roi", ""),
                "doses": [_sf(x) for x in getattr(r, "doses", [])],
                "eqd2s": [_sf(x) for x in getattr(r, "eqd2s", [])],
            }
            for r in plan
        ],
    }
    
    limits_caps = {
        "VEJIGA": limits_map.get("Vejiga", LIMITS_EQD2["VEJIGA"]),
        "RECTO": limits_map.get("Recto", LIMITS_EQD2["RECTO"]),
        "SIGMOIDE": limits_map.get("Sigmoide", LIMITS_EQD2["SIGMOIDE"]),
        "INTESTINO": limits_map.get("Intestino", LIMITS_EQD2["INTESTINO"]),
    }
    
    return render_template(
        'home.html',
        fx_rt=fx_rt,
        n_hdr=n_hdr,
        step1=True,
        results=results_preview,
        plan_real=plan,
        plan_summary=plan_summary,
        patient_name=patient_name,
        patient_id=patient_id,
        limits=limits_caps,
        export_data=export_data,
    )
