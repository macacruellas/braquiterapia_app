/**
 * JavaScript para la aplicación de Braquiterapia
 */

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initRTCheckbox();
    initSessionSelector();
    scrollToResult();
});

/**
 * Tras un POST (carga de archivo / cálculo), hace scroll al bloque de
 * resultados más reciente para que el usuario no vuelva al inicio de la página.
 * Prioridad: resumen > paso2 (HDR) > paso1 (Eclipse/manual).
 */
function scrollToResult() {
    const target =
        document.getElementById('resultado-resumen') ||
        document.getElementById('resultado-paso2') ||
        document.getElementById('resultado-paso1');

    if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

/**
 * Maneja el checkbox de RT local vs manual
 */
function initRTCheckbox() {
    const checkbox = document.getElementById('chk_rtx_local');
    if (!checkbox) return;
    
    const paso1Block = document.getElementById('bloque-paso1');
    const manualBlock = document.getElementById('bloque-manual');
    const manualModeInput = document.getElementById('manual_mode');
    
    function updateUI() {
        const isOnSite = checkbox.checked;
        
        if (paso1Block) {
            paso1Block.style.display = isOnSite ? 'block' : 'none';
        }
        
        if (manualBlock) {
            manualBlock.style.display = isOnSite ? 'none' : 'block';
        }
        
        if (manualModeInput) {
            manualModeInput.value = isOnSite ? '0' : '1';
        }
    }
    
    checkbox.addEventListener('change', updateUI);
    
    // Estado inicial: desmarcado (muestra Manual)
    checkbox.checked = false;
    updateUI();
}

/**
 * Maneja el selector de número de sesiones HDR
 */
function initSessionSelector() {
    const select = document.getElementById('n_sesiones');
    if (!select) return;
    
    const sessionBlocks = [
        document.getElementById('sesion-1'),
        document.getElementById('sesion-2'),
        document.getElementById('sesion-3')
    ];
    
    function updateVisibility() {
        const numSessions = parseInt(select.value, 10);
        
        sessionBlocks.forEach((block, index) => {
            if (!block) return;
            
            const isVisible = (index < numSessions);
            block.style.display = isVisible ? 'block' : 'none';
            
            // Manejar el atributo required del input file
            const fileInput = block.querySelector('input[type="file"]');
            if (fileInput) {
                fileInput.required = isVisible;
                
                // Limpiar el valor si no es visible
                if (!isVisible) {
                    try {
                        fileInput.value = '';
                    } catch(e) {
                        // Algunos navegadores no permiten limpiar file inputs
                    }
                }
            }
        });
    }
    
    select.addEventListener('change', updateVisibility);
    updateVisibility(); // Llamar una vez al inicio
}

/**
 * Muestra el siguiente campo de fecha oculto (máx. 4).
 */
function agregarFecha() {
    const rows = document.querySelectorAll('.fecha-row');
    for (let row of rows) {
        if (row.style.display === 'none') {
            row.style.display = 'flex';
            const visible = [...rows].filter(r => r.style.display !== 'none').length;
            if (visible >= 4) {
                const btn = document.getElementById('btn-agregar-fecha');
                if (btn) btn.style.display = 'none';
            }
            return;
        }
    }
}

/**
 * Oculta y limpia el campo de fecha de la fila indicada.
 */
function removeFecha(btn) {
    const row = btn.closest('.fecha-row');
    const input = row.querySelector('input[type="date"]');
    if (input) input.value = '';
    row.style.display = 'none';
    const addBtn = document.getElementById('btn-agregar-fecha');
    if (addBtn) addBtn.style.display = 'inline-block';
}

/**
 * Valida un formulario antes de enviar
 * @param {HTMLFormElement} form - Formulario a validar
 * @returns {boolean} - true si es válido
 */
function validateForm(form) {
    const requiredInputs = form.querySelectorAll('[required]');
    
    for (let input of requiredInputs) {
        if (!input.value || input.value.trim() === '') {
            alert(`Por favor complete el campo: ${input.name}`);
            input.focus();
            return false;
        }
    }
    
    return true;
}

/**
 * Muestra un indicador de carga
 */
function showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loading-indicator';
    loadingDiv.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
                    background: rgba(0,0,0,0.7); display: flex; align-items: center; 
                    justify-content: center; z-index: 9999;">
            <div style="background: white; padding: 30px; border-radius: 12px; 
                        text-align: center; color: #333;">
                <div style="font-size: 24px; margin-bottom: 10px;">⏳</div>
                <div>Procesando archivo...</div>
            </div>
        </div>
    `;
    document.body.appendChild(loadingDiv);
}

/**
 * Oculta el indicador de carga
 */
function hideLoading() {
    const loadingDiv = document.getElementById('loading-indicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}
