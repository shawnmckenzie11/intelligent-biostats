import socket
from contextlib import closing
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from startup import initialize_environment
from app import create_app

def find_free_port(start_port=5000, max_attempts=100):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.bind(('0.0.0.0', port))
                return port
            except socket.error:
                continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

def main():
    """Initialize and run the application."""
    try:
        # Initialize environment
        initialize_environment()
        
        # Create Flask app
        app = create_app()
        
        # Find available port
        port = find_free_port()
        print(f"Starting server on port {port}")
        
        # Run the app
        app.run(host='0.0.0.0', port=port, debug=True)
        
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 