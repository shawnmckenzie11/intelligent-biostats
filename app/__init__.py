from flask import Flask
from app.config.settings import DevelopmentConfig
from app.core.data_manager import DataManager
from app.utils.column_selector import ColumnSelector
import logging
import os
from flask_cors import CORS

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
        CORS(app)
        
        # Verify required directories
        verify_directories()
        
        # Initialize data manager as a singleton
        if not hasattr(app, 'data_manager'):
            app.data_manager = DataManager()
            logger.info("Initialized data manager")
            
        # Initialize column selector
        if not hasattr(app, 'column_selector'):
            app.column_selector = ColumnSelector(app.data_manager)
            logger.info("Initialized column selector")
        
        # Setup non-intrusive debugging features
        from app.utils.debug_utils import setup_debug_features
        setup_debug_features(app)
        
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
