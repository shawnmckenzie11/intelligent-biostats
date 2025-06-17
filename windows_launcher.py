import sys
import os
import subprocess
import webbrowser
import time
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

def setup_environment():
    """Set up the application environment."""
    # Get the base directory (where the executable is located)
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent

    # Create necessary directories
    for dir_name in ['uploads', 'temp', 'logs']:
        dir_path = base_dir / dir_name
        dir_path.mkdir(exist_ok=True)

    return base_dir

def run_application():
    """Run the main application."""
    try:
        base_dir = setup_environment()
        
        # Start the Flask application
        if getattr(sys, 'frozen', False):
            # Running as executable
            python_exe = sys.executable
            run_script = str(base_dir / 'run.py')
        else:
            # Running in development
            python_exe = sys.executable
            run_script = str(Path(__file__).parent / 'run.py')

        # Start the Flask server
        process = subprocess.Popen(
            [python_exe, run_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for the server to start
        time.sleep(2)  # Give the server time to start
        
        # Open the default web browser
        webbrowser.open('http://localhost:5000')

        # Keep the application running
        while True:
            output = process.stdout.readline()
            if output:
                logging.info(output.strip())
            if process.poll() is not None:
                break

    except Exception as e:
        logging.error(f"Error running application: {str(e)}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == '__main__':
    run_application() 