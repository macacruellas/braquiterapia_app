"""
Aplicación Flask para cálculos dosimétricos de Braquiterapia
"""
from flask import Flask
import os


def create_app():
    """
    Factory function para crear la aplicación Flask.
    
    Returns:
        Flask: Instancia de la aplicación configurada
    """
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object('config.settings')
    
    # Registrar blueprints (rutas)
    from app.routes import main_routes, dvh_routes, export_routes
    
    app.register_blueprint(main_routes.bp)
    app.register_blueprint(dvh_routes.bp)
    app.register_blueprint(export_routes.bp)
    
    # Configurar manejo de errores
    @app.errorhandler(404)
    def not_found(error):
        return "Página no encontrada", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return "Error interno del servidor", 500
    
    return app
