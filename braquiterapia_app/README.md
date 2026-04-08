# 🏥 Sistema de Cálculo Dosimétrico para Braquiterapia

Sistema web desarrollado en Flask para el cálculo de dosis en tratamientos de braquiterapia ginecológica.

## 📋 Características

- ✅ Importación de archivos DVH desde Eclipse y Oncentra
- ✅ Cálculo automático de EQD2 para órganos en riesgo
- ✅ Validación de coincidencia de pacientes entre archivos
- ✅ Soporte para múltiples sesiones de braquiterapia
- ✅ Exportación de informes a Excel y PDF
- ✅ Interfaz moderna y responsive

## 🗂️ Estructura del Proyecto

```
braquiterapia_app/
│
├── run.py                      # Punto de entrada principal
├── requirements.txt            # Dependencias de Python
├── README.md                   # Este archivo
│
├── config/
│   └── settings.py            # Configuración global
│
└── app/
    ├── __init__.py            # Inicialización de Flask
    │
    ├── routes/                # Rutas de la aplicación
    │   ├── main_routes.py     # Ruta principal (home)
    │   ├── dvh_routes.py      # Carga y procesamiento DVH
    │   └── export_routes.py   # Exportación de informes
    │
    ├── parsers/               # Parsers de archivos
    │   ├── eclipse_parser.py  # Parser DVH Eclipse
    │   └── oncentra_parser.py # Parser DVH Oncentra
    │
    ├── calculations/          # Módulos de cálculo
    │   └── dosimetry.py       # Cálculos dosimétricos
    │
    ├── utils/                 # Utilidades
    │   ├── helpers.py         # Funciones auxiliares
    │   ├── roi_mapping.py     # Mapeo de ROIs
    │   └── file_handlers.py   # Manejo de archivos
    │
    ├── templates/             # Templates HTML
    │   ├── base.html          # Template base
    │   ├── home.html          # Página principal
    │   └── (plantillas Excel)
    │
    └── static/                # Archivos estáticos
        ├── css/
        │   └── styles.css     # Estilos CSS
        └── js/
            └── main.js        # JavaScript
```

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
cd braquiterapia_app
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar LibreOffice (para exportación PDF)

**Windows:**
- Instalar LibreOffice desde https://www.libreoffice.org/
- El sistema buscará automáticamente en las rutas estándar

**Linux:**
```bash
sudo apt-get install libreoffice
```

**Mac:**
```bash
brew install libreoffice
```

## ▶️ Ejecución

```bash
python run.py
```

Luego abrir en el navegador: http://127.0.0.1:5000

## 📖 Uso

### Paso 1: Cargar DVH de RT Externa

1. Seleccionar si el paciente se trató en el centro local
2. Si es local: cargar archivo DVH de Eclipse (.txt)
3. Si es externo: ingresar manualmente las dosis D2cc

### Paso 2: Cargar DVH de Braquiterapia

1. Seleccionar número de planes HDR
2. Cargar archivos DVH de Oncentra (.txt)
3. El sistema calculará automáticamente las dosis totales

### Paso 3: Exportar Informes

- **Cartón dosimétrico**: Resumen en formato PDF
- **Informe final**: Documento Excel editable

## 🔧 Configuración

Editar `config/settings.py` para modificar:

- Límites de dosis por órgano
- Valores α/β
- Número de fracciones por defecto

```python
LIMITS_EQD2 = {
    "VEJIGA": 85.0,
    "RECTO": 75.0,
    "SIGMOIDE": 75.0,
    "INTESTINO": 75.0
}
```

## 🧪 Testing

(Por implementar)

```bash
pytest tests/
```

## 📝 Próximas Mejoras

- [ ] Autenticación de usuarios
- [ ] Base de datos para historial
- [ ] API REST
- [ ] Tests unitarios completos
- [ ] Logging detallado
- [ ] Docker deployment

## 🤝 Contribuciones

Este proyecto está en desarrollo activo. Sugerencias y mejoras son bienvenidas.

## 📄 Licencia

Uso interno hospitalario.

## 👥 Autores

Desarrollado para el servicio de Radioterapia.

## 📞 Soporte

Para reportar bugs o solicitar funcionalidades, contactar al equipo de física médica.
