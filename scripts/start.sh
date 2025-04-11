#!/bin/bash

# Start timing
START_TIME=$(date +%s)

# Function to check if we're in a virtual environment
in_venv() {
    python -c 'import sys; print(sys.prefix != sys.base_prefix)' 2>/dev/null
}

# Function to print timing information
print_timing() {
    local stage=$1
    local start=$2
    local end=$(date +%s)
    local duration=$((end - start))
    echo "⏱️  $stage took $duration seconds"
    
    # Warning thresholds
    if [ "$stage" == "Total startup" ] && [ $duration -gt 30 ]; then
        echo "⚠️  Warning: Startup time exceeded 30 seconds"
    elif [ "$stage" == "Package installation" ] && [ $duration -gt 15 ]; then
        echo "⚠️  Warning: Package installation exceeded 15 seconds"
    fi
}

# Ensure we're in the virtual environment
VENV_START=$(date +%s)
if ! in_venv; then
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment..."
        python -m venv .venv
    fi
    source .venv/bin/activate
fi
print_timing "Virtual environment setup" $VENV_START

# Install/upgrade pip first
PIP_START=$(date +%s)
echo "Upgrading pip..."
python -m pip install --upgrade pip
print_timing "Pip upgrade" $PIP_START

# Install core dependencies
CORE_START=$(date +%s)
echo "Installing core dependencies..."
pip install --no-cache-dir python-dotenv==1.0.0
pip install --no-cache-dir Flask==2.3.3 Werkzeug==2.3.7 SQLAlchemy==2.0.27 flask-cors==4.0.0
print_timing "Core dependencies" $CORE_START

# Install data processing dependencies
DATA_START=$(date +%s)
echo "Installing data processing dependencies..."
pip install --no-cache-dir numpy==1.24.3 pandas==2.0.3 scipy==1.10.1
print_timing "Data processing dependencies" $DATA_START

# Install visualization dependencies
VIZ_START=$(date +%s)
echo "Installing visualization dependencies..."
pip install --no-cache-dir matplotlib==3.7.1 seaborn==0.12.2
print_timing "Visualization dependencies" $VIZ_START

# Install development tools
DEV_START=$(date +%s)
echo "Installing development tools..."
pip install --no-cache-dir pytest==8.0.2 pytest-cov==4.1.0 flake8==7.0.0 black==24.2.0 isort==5.13.2 watchdog==3.0.0
print_timing "Development tools" $DEV_START

# Install documentation tools
DOC_START=$(date +%s)
echo "Installing documentation tools..."
pip install --no-cache-dir Sphinx==7.2.6 sphinx-rtd-theme==2.0.0
print_timing "Documentation tools" $DOC_START

# Install utilities
UTIL_START=$(date +%s)
echo "Installing utilities..."
pip install --no-cache-dir requests==2.31.0
print_timing "Utilities" $UTIL_START

# Verify python-dotenv is installed
VERIFY_START=$(date +%s)
echo "Verifying python-dotenv installation..."
python -c "import dotenv" || {
    echo "Error: python-dotenv not properly installed"
    pip install --force-reinstall python-dotenv==1.0.0
}
print_timing "Verification" $VERIFY_START

# Start the application
APP_START=$(date +%s)
echo "Starting the application..."
python run.py
print_timing "Application startup" $APP_START

# Print total time
print_timing "Total startup" $START_TIME 