from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
import io
from app.core.database import AnalysisHistoryDB
from app.core.ai_engine import AIEngine
from app.config import OPENAI_API_KEY

data_bp = Blueprint('data', __name__)

# Initialize components
ai_engine = AIEngine()
db = AnalysisHistoryDB()

# Global variables
current_df = None
current_file = None
modifications_history = []

@data_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and initial data processing."""
    global current_df, current_file
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Read the file based on extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(file.read()))
        else:
            return jsonify({'error': 'Unsupported file format'}), 400
            
        current_df = df
        current_file = file.filename
        
        # Get initial data insights
        initial_insights = {
            'columns': list(df.columns),
            'shape': df.shape,
            'dtypes': df.dtypes.astype(str).to_dict(),
            'missing_values': df.isnull().sum().to_dict()
        }
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'insights': initial_insights
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/modify', methods=['POST'])
def modify_data():
    """Handle data modifications and transformations."""
    global current_df, modifications_history
    
    try:
        if current_df is None:
            return jsonify({'error': 'No data loaded'}), 400
            
        modification = request.json
        if not modification:
            return jsonify({'error': 'No modification specified'}), 400
            
        # Apply modification
        # Add your modification logic here
        
        modifications_history.append(modification)
        return jsonify({'success': True, 'message': 'Data modified successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/column/<column_name>', methods=['GET'])
def get_column_data(column_name):
    """Get detailed information about a specific column."""
    global current_df
    
    try:
        if current_df is None:
            return jsonify({'error': 'No data loaded'}), 400
            
        if column_name not in current_df.columns:
            return jsonify({'error': 'Column not found'}), 404
            
        column_data = current_df[column_name]
        stats = {
            'dtype': str(column_data.dtype),
            'unique_values': column_data.nunique(),
            'missing_values': column_data.isnull().sum(),
            'descriptive_stats': column_data.describe().to_dict()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 