import socket
from contextlib import closing
import sys
import os
import time
from datetime import datetime

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

def log_timing(message, start_time):
    duration = time.time() - start_time
    print(f"⏱️  {message}: {duration:.2f} seconds")
    if duration > 5:  # Warning threshold for individual steps
        print(f"⚠️  Warning: {message} took longer than 5 seconds")

def main():
    total_start = time.time()
    
    try:
        # Import dotenv
        dotenv_start = time.time()
        from dotenv import load_dotenv
        log_timing("Dotenv import", dotenv_start)
        
        # Load environment variables
        env_start = time.time()
        load_dotenv()
        log_timing("Environment loading", env_start)
        
        # Import Flask app
        flask_start = time.time()
        from app import create_app
        log_timing("Flask import", flask_start)
        
        # Create app
        create_start = time.time()
        app = create_app()
        log_timing("App creation", create_start)
        
        # Run app
        run_start = time.time()
        print(f"\n🚀 Starting application at {datetime.now()}")
        app.run(debug=True)
        log_timing("App startup", run_start)
        
    except ImportError as e:
        print(f"Error: {e}")
        print("Please make sure all dependencies are installed correctly.")
        print("Try running: ./scripts/start.sh")
        exit(1)
    finally:
        log_timing("Total application startup", total_start)

if __name__ == '__main__':
    main() 