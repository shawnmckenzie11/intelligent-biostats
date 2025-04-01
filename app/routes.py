from flask import Blueprint, render_template, jsonify
from .core.data_manager import EnhancedDataFrame
import pandas as pd

main = Blueprint('main', __name__)
data_manager = EnhancedDataFrame()

@main.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@main.route('/api/descriptive-stats')
def get_descriptive_stats():
    """Get descriptive statistics for the dataset."""
    try:
        if data_manager.data is None:
            return jsonify({'success': False, 'error': 'No data loaded'})
            
        stats = {
            'file_stats': data_manager.metadata.get('file_stats', {}),
            'column_types': data_manager.metadata.get('column_types', {})
        }
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@main.route('/api/column-stats/<column_name>')
def get_column_stats(column_name):
    """Get statistics for a specific column."""
    try:
        if data_manager.data is None:
            return jsonify({'success': False, 'error': 'No data loaded'})
            
        if column_name not in data_manager.data.columns:
            return jsonify({'success': False, 'error': 'Column not found'})
            
        column_data = data_manager.data[column_name]
        stats = {}
        
        # Calculate statistics based on column type
        if pd.api.types.is_numeric_dtype(column_data):
            stats = {
                'Mean': f"{column_data.mean():.2f}",
                'Median': f"{column_data.median():.2f}",
                'Std Dev': f"{column_data.std():.2f}",
                'Min': f"{column_data.min():.2f}",
                'Max': f"{column_data.max():.2f}",
                'Missing Values': str(column_data.isna().sum())
            }
        else:
            stats = {
                'Unique Values': str(column_data.nunique()),
                'Most Common': str(column_data.mode().iloc[0]),
                'Missing Values': str(column_data.isna().sum())
            }
            
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}) 