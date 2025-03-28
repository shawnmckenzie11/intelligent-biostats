import sys
import subprocess
import pkg_resources
import importlib

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
    """Check and install required packages."""
    required = get_required_packages()
    installed = {pkg.key for pkg in pkg_resources.working_set}
    
    missing = []
    for package in required:
        name = package.split('==')[0]
        if name.lower() not in installed:
            missing.append(package)
    
    if missing:
        print("Installing missing packages:", missing)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("Successfully installed missing packages.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")
            sys.exit(1)

def check_system_dependencies():
    """Check system-level dependencies."""
    # Add any system-level dependency checks here
    pass

def initialize_environment():
    """Initialize the application environment."""
    print("Initializing Intelligent Biostats...")
    check_python_version()
    check_system_dependencies()
    check_and_install_packages() 