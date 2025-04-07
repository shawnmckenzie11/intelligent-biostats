from flask import Blueprint
from .data.routes import data_bp
from .analysis.routes import analysis_bp
from .ai.routes import ai_bp

# Create main blueprint
api_bp = Blueprint('api', __name__)

# Register blueprints
api_bp.register_blueprint(data_bp, url_prefix='/data')
api_bp.register_blueprint(analysis_bp, url_prefix='/analysis')
api_bp.register_blueprint(ai_bp, url_prefix='/ai')

# Export the main blueprint
__all__ = ['api_bp'] 