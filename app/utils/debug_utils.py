import logging
import uuid
from functools import wraps
from flask import g, request, current_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_debug_features(app):
    """Setup debugging features that don't interfere with existing functionality."""
    
    # Request tracking
    @app.before_request
    def before_request():
        g.request_id = str(uuid.uuid4())
        logger.info(f"Request started - ID: {g.request_id} - Path: {request.path} - Method: {request.method}")
    
    @app.after_request
    def after_request(response):
        response.headers['X-Request-ID'] = g.request_id
        logger.info(f"Request completed - ID: {g.request_id} - Status: {response.status_code}")
        return response
    
    # Route documentation storage
    if not hasattr(app, 'route_docs'):
        app.route_docs = {}

def log_route_access(f):
    """Decorator to log route access without modifying the route's behavior."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Log the request
            logger.info(f"Route accessed: {request.path}")
            if request.args:
                logger.debug(f"Query params: {request.args}")
            if request.json:
                logger.debug(f"Request body: {request.json}")
            
            # Call the original function
            result = f(*args, **kwargs)
            
            # Log the response status
            if isinstance(result, tuple) and len(result) > 1:
                logger.info(f"Response status: {result[1]}")
            return result
            
        except Exception as e:
            logger.error(f"Error in route {request.path}: {str(e)}")
            raise
    
    return decorated_function

def document_route(description=None, params=None, returns=None):
    """Decorator to store route documentation without modifying behavior."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Store documentation
            if not hasattr(current_app, 'route_docs'):
                current_app.route_docs = {}
            current_app.route_docs[request.path] = {
                'description': description,
                'params': params,
                'returns': returns,
                'function': f.__name__
            }
            return f(*args, **kwargs)
        return wrapper
    return decorator 