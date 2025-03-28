from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
import io
from app.core.ai_engine import AIEngine
from collections import OrderedDict

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
        
        # Convert to dictionary format, preserving column order
        preview_dict = OrderedDict()
        for column in df.columns:
            # Handle NaN values and convert to Python native types
            preview_dict[str(column)] = [
                None if pd.isna(x) else x 
                for x in df[column].head().tolist()
            ]
        
        info = {
            'success': True,
            'info': {
                'rows': len(df),
                'columns': len(df.columns),
                'column_types': df.dtypes.to_dict(),
                'preview': preview_dict
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
        modified_df, was_modified = ai_engine.modify_data(current_df, modification)
        
        # Only update stored DataFrame if changes were made
        if was_modified:
            current_df = modified_df
            # Convert to dictionary format for preview, maintaining column order
            preview_dict = OrderedDict()
            for column in modified_df.columns:
                # Handle NaN values and convert to Python native types
                preview_dict[str(column)] = [
                    None if pd.isna(x) else x 
                    for x in modified_df[column].head().tolist()
                ]
        else:
            preview_dict = None  # Don't send preview if no changes
            
        response = {
            'success': True,
            'preview': preview_dict if was_modified else None,
            'message': 'Modifications applied successfully!' if was_modified else 'No changes were made to the data'
        }
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
