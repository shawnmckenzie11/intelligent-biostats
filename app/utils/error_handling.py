from flask import jsonify, current_app
import logging
import traceback

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base class for API errors."""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv

def setup_error_handling(app):
    """Setup error handling for the application."""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        logger.error(f"API Error: {error.message} - Status: {error.status_code}")
        return response
    
    @app.errorhandler(404)
    def handle_not_found(error):
        logger.warning(f"404 Not Found: {request.path}")
        return jsonify({
            'message': 'Resource not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(500)
    def handle_server_error(error):
        logger.error(f"500 Server Error: {str(error)}\n{traceback.format_exc()}")
        return jsonify({
            'message': 'Internal server error',
            'status_code': 500
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.error(f"Unexpected Error: {str(error)}\n{traceback.format_exc()}")
        return jsonify({
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500 