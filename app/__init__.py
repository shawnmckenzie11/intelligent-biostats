from flask import Flask
from config.settings import DevelopmentConfig
import logging
import os

def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def verify_directories():
    """Ensure required directories exist."""
    required_dirs = [
        'uploads',  # For uploaded files
        'logs',     # For log files
        'temp'      # For temporary files
    ]
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)

def create_app(config_class=DevelopmentConfig):
    """Create and configure the Flask application."""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting application initialization...")
        
        # Create Flask app
        app = Flask(__name__, 
                   template_folder='frontend/templates',
                   static_folder='frontend/static')
        app.config.from_object(config_class)
        
        # Verify required directories
        verify_directories()
        
        # Register blueprints
        from app.api.routes import api
        from app.routes import main
        
        app.register_blueprint(api, url_prefix='/api')
        app.register_blueprint(main)  # This handles the root URL
        
        logger.info("Application initialization completed successfully")
        return app
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
