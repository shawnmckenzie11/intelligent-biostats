from flask import Blueprint, request, jsonify
import pandas as pd
import io
from app.core.ai_engine import AIEngine

api = Blueprint('api', __name__)
ai_engine = AIEngine()

# Define global variable at module level
current_df = None

@api.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and return initial analysis."""
    try:
        global current_df
        data = request.json.get('data')
        df = pd.read_csv(io.StringIO(data))
        
        # Store DataFrame in memory
        current_df = df
        
        info = {
            'success': True,
            'info': {
                'rows': len(df),
                'columns': len(df.columns),
                'column_types': df.dtypes.to_dict(),
                'preview': df.head().to_dict()
            }
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@api.route('/modify-data', methods=['POST'])
def modify_data():
    """Handle AI-powered data modification requests."""
    try:
        global current_df
        modification = request.json.get('modification')
        print(f"Received modification request: {modification}")
        
        if current_df is None:
            raise ValueError("No data has been uploaded yet")
            
        # Use AI engine to interpret and apply modification
        modified_df = ai_engine.modify_data(current_df, modification)
        
        # Update stored DataFrame
        current_df = modified_df
        
        # Convert to dictionary format for preview
        preview_dict = {}
        for column in modified_df.columns:
            preview_dict[column] = modified_df[column].head().tolist()
            
        response = {
            'success': True,
            'preview': preview_dict,
            'message': f'Successfully applied modification: {modification}'
        }
        print("Sending response:", response)
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in modify_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@api.route('/analyze-options', methods=['GET'])
def get_analysis_options():
    """Get available analysis options based on current data."""
    try:
        global current_df
        # Use AI engine to determine appropriate analyses
        options = ai_engine.get_analysis_options(current_df)
        
        return jsonify({
            'success': True,
            'options': options
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@api.route('/analyze', methods=['POST'])
def analyze_data():
    """Perform statistical analysis."""
    pass

@api.route('/recommendations', methods=['GET'])
def get_recommendations():
    """Get AI recommendations."""
    pass
