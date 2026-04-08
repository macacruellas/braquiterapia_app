"""
Rutas principales de la aplicación
"""
from flask import Blueprint, render_template
from config.settings import DEFAULT_FX_RT, DEFAULT_N_HDR, LIMITS_EQD2

bp = Blueprint('main', __name__)


@bp.route("/", methods=["GET"])
def home():
    """
    Página principal de la aplicación.
    Muestra el formulario inicial para configurar el tratamiento.
    """
    return render_template(
        'home.html',
        fx_rt=DEFAULT_FX_RT,
        n_hdr=DEFAULT_N_HDR,
        step1=False,
        limits=LIMITS_EQD2,
        ctv_volume_total=None,
        ctv_d90_gy=None,
        ctv_d90_cgy=None
    )
