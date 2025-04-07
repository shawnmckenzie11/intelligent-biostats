import uuid
from flask import g, request
import logging

logger = logging.getLogger(__name__)

def setup_request_tracking(app):
    """Add request ID tracking to the application."""
    @app.before_request
    def before_request():
        # Generate a unique request ID
        g.request_id = str(uuid.uuid4())
        # Add request ID to logger context
        logger.info(f"Request started - ID: {g.request_id} - Path: {request.path} - Method: {request.method}")
    
    @app.after_request
    def after_request(response):
        # Add request ID to response headers
        response.headers['X-Request-ID'] = g.request_id
        logger.info(f"Request completed - ID: {g.request_id} - Status: {response.status_code}")
        return response 