import os
import sys
from startup import initialize_environment

def main():
    # Run startup checks
    initialize_environment()
    
    # Import app only after environment is verified
    from app import create_app
    
    app = create_app()
    app.run(debug=True)

if __name__ == '__main__':
    main() 