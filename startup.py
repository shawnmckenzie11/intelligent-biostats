import sys
import subprocess
import pkg_resources
import os
from importlib.metadata import version, PackageNotFoundError
import importlib
from typing import List, Set
from dotenv import load_dotenv

def check_python_version():
    """Check if Python version meets requirements."""
    required_version = (3, 7)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        raise SystemError(
            f"Python {required_version[0]}.{required_version[1]} or higher is required. "
            f"You are using Python {current_version[0]}.{current_version[1]}"
        )

def get_required_packages():
    """Read requirements from requirements.txt."""
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def check_and_install_packages():
    """Check and install required packages from requirements.txt."""
    try:
        # Get installed packages
        installed = {pkg.key for pkg in pkg_resources.working_set}
        
        # Read requirements
        requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
        with open(requirements_path) as f:
            required = {line.strip().split('==')[0].split('>=')[0] 
                       for line in f if line.strip() and not line.startswith('#')}
        
        # Find missing packages
        missing = required - installed
        
        if missing:
            print(f"Installing missing packages: {missing}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
            print("Package installation complete.")
        else:
            print("All required packages are already installed.")
            
    except Exception as e:
        print(f"Error checking/installing packages: {str(e)}")
        raise

def check_system_dependencies():
    """Check system-level dependencies."""
    # Add any system-level dependency checks here
    pass

def initialize_environment():
    """Initialize the application environment."""
    if not hasattr(initialize_environment, '_initialized'):
        print("Initializing Intelligent Biostats...")
        
        # Load environment variables from .env file
        load_dotenv()
        
        check_python_version()
        check_system_dependencies()
        check_and_install_packages()
        initialize_environment._initialized = True 