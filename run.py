import socket
from contextlib import closing
import sys
import os
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Modified virtual environment check to handle both development and executable environments
def is_running_in_executable():
    """Check if the application is running as a PyInstaller executable."""
    return getattr(sys, 'frozen', False)

# Only check for virtual environment if not running as executable
if not is_running_in_executable():
if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
        logger.warning("Not running in a virtual environment. Please run './activate_venv.sh python run.py'")
    sys.exit(1)

# Add the current directory to the Python path
if not is_running_in_executable():
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from startup import initialize_environment
from app import create_app

def find_free_port(start_port=5000, max_attempts=100):
    """Find an available port starting from start_port."""
    # First check if port is set in environment
    if 'FLASK_RUN_PORT' in os.environ:
        try:
            port = int(os.environ['FLASK_RUN_PORT'])
            # Verify the port is available
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                try:
                    sock.bind(('0.0.0.0', port))
                    logger.info(f"Using port from environment: {port}")
                    return port
                except socket.error as e:
                    logger.warning(f"Port {port} from environment is not available: {str(e)}")
        except ValueError:
            logger.warning(f"Invalid port in environment: {os.environ['FLASK_RUN_PORT']}")
    
    # If no port in environment or it's not available, find a free one
    for port in range(start_port, start_port + max_attempts):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.bind(('0.0.0.0', port))
                logger.info(f"Found available port: {port}")
                return port
            except socket.error as e:
                logger.debug(f"Port {port} is in use: {str(e)}")
                continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

def main():
    """Initialize and run the application."""
    try:
        logger.info("Initializing environment...")
        # Initialize environment
        initialize_environment()
        
        logger.info("Creating Flask application...")
        # Create Flask app
        app = create_app()
        
        # Find available port
        port = find_free_port()
        logger.info(f"Starting server on port {port}")
        logger.info(f"Server will be accessible at: http://localhost:{port}")
        logger.info(f"Server will be accessible at: http://127.0.0.1:{port}")
        
        # Run the app with more detailed logging
        logger.info("Starting Flask server...")
        try:
            # Ensure we're binding to all interfaces
            app.run(
                host='0.0.0.0',  # Listen on all interfaces
                port=port,
                debug=True,
                use_reloader=False,  # Disable reloader to prevent duplicate processes
                threaded=True  # Enable threading
            )
        except Exception as e:
            logger.error(f"Error starting Flask server: {str(e)}")
            logger.error("Traceback:")
            logger.error(traceback.format_exc())
            raise
        
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main() 