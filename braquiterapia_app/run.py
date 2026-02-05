"""
Punto de entrada principal para la aplicación de Braquiterapia
"""
from app import create_app
import sys
import traceback

# Crear la aplicación
app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("🏥 SERVIDOR DE BRAQUITERAPIA")
    print("=" * 60)
    print(f"🌐 Servidor corriendo en: http://127.0.0.1:5000")
    print(f"🌐 También disponible en: http://0.0.0.0:5000")
    print("=" * 60)
    print("📝 Presiona Ctrl+C para detener el servidor")
    print("=" * 60)
    
    try:
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\n✅ Servidor detenido correctamente")
    except Exception as e:
        print("\n\n❌ Error al iniciar el servidor:")
        traceback.print_exc()
        sys.exit(1)
