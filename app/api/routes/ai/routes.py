from flask import Blueprint, request, jsonify
from app.core.ai_engine import AIEngine
from app.core.database import AnalysisHistoryDB

ai_bp = Blueprint('ai', __name__)

# Initialize components
ai_engine = AIEngine()
db = AnalysisHistoryDB()

@ai_bp.route('/recommend', methods=['GET'])
def get_recommendations():
    """Get AI-powered analysis recommendations."""
    try:
        if current_df is None:
            return jsonify({'error': 'No data loaded'}), 400
            
        recommendations = ai_engine.get_recommendations(current_df)
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/insights', methods=['POST'])
def get_ai_insights():
    """Get AI-generated insights about the data."""
    try:
        if current_df is None:
            return jsonify({'error': 'No data loaded'}), 400
            
        context = request.json.get('context', {})
        insights = ai_engine.get_insights(current_df, context)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/learn', methods=['POST'])
def train_model():
    """Train the AI model with new data."""
    try:
        if current_df is None:
            return jsonify({'error': 'No data loaded'}), 400
            
        training_params = request.json
        if not training_params:
            return jsonify({'error': 'No training parameters provided'}), 400
            
        result = ai_engine.train(current_df, training_params)
        
        return jsonify({
            'success': True,
            'message': 'Model trained successfully',
            'metrics': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 