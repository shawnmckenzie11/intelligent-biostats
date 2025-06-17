#!/bin/bash

# Navigate to the project directory
cd ~/intelligent-biostats

# Pull the latest changes from git
git pull origin main

# Activate the virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Reload the web app
touch /var/www/projectjapan_pythonanywhere_com_wsgi.py

echo "Site updated successfully!" 