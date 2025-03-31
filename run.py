import os
import sys
from startup import initialize_environment

def main():
    # Only run startup checks in the main process
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        initialize_environment()
    
    # Import app only after environment is verified
    from app import create_app
    app = create_app()
    app.run(debug=True, port=5001)

if __name__ == '__main__':
    main() 