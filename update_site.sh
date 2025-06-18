#!/bin/bash

# Log file for tracking updates
LOG_FILE="$HOME/update.log"

# Function to log messages with timestamps
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOG_FILE"
}

# Start update process
log_message "Starting update process"

# Change to project directory
cd "$HOME/intelligent-biostats" || {
    log_message "Error: Failed to change to project directory"
    exit 1
}

# Activate virtual environment
source venv/bin/activate || {
    log_message "Error: Failed to activate virtual environment"
    exit 1
}

# Pull latest changes
log_message "Pulling latest changes from GitHub"
git pull origin main >> "$LOG_FILE" 2>&1 || {
    log_message "Error: Failed to pull changes from GitHub"
    exit 1
}

# Update dependencies
log_message "Updating dependencies"
pip install -r requirements.txt >> "$LOG_FILE" 2>&1 || {
    log_message "Error: Failed to update dependencies"
    exit 1
}

# Touch WSGI file to trigger reload
touch /var/www/projectjapan_pythonanywhere_com_wsgi.py || {
    log_message "Error: Failed to touch WSGI file"
    exit 1
}

# Log successful completion
log_message "Update completed successfully" 