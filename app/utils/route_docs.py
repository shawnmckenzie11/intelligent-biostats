from functools import wraps
from flask import request, current_app
import logging

logger = logging.getLogger(__name__)

def document_route(description=None, params=None, returns=None):
    """
    Decorator to document routes and their parameters.
    
    Args:
        description (str): Description of what the route does
        params (dict): Dictionary of parameter names and their descriptions
        returns (str): Description of what the route returns
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Log route access with parameters
            log_message = f"Route accessed: {request.path}"
            if params:
                log_message += f"\nParameters: {request.args.to_dict()}"
            if request.json:
                log_message += f"\nBody: {request.json}"
            logger.info(log_message)
            
            # Store route documentation
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