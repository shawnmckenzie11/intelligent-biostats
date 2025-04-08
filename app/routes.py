from flask import Blueprint, render_template, jsonify, request
from .core.data_manager import EnhancedDataFrame, DataPointFlag
import pandas as pd
import numpy as np
import logging

main = Blueprint('main', __name__)
data_manager = EnhancedDataFrame()
logger = logging.getLogger(__name__)

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
            'column_types': data_manager.metadata.get('column_types', {}),
            'flag_counts': {
                col: {
                    flag.value: int(np.sum(data_manager.point_flags[:, idx] == flag))
                    for flag in DataPointFlag
                }
                for idx, col in enumerate(data_manager.data.columns)
            }
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
            
        col_idx = data_manager.data.columns.get_loc(column_name)
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
            
        # Add flag information
        if data_manager.point_flags is not None:
            flags = data_manager.point_flags[:, col_idx]
            stats['flags'] = {
                flag.value: {
                    'count': int(np.sum(flags == flag)),
                    'indices': np.where(flags == flag)[0].tolist()
                }
                for flag in DataPointFlag
            }
            
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@main.route('/api/point-flags', methods=['POST'])
def get_point_flags():
    """Get flags for specific data points."""
    try:
        if data_manager.data is None:
            return jsonify({'success': False, 'error': 'No data loaded'})
            
        data = request.get_json()
        if not data or 'points' not in data:
            return jsonify({'success': False, 'error': 'No points specified'})
            
        points = data['points']
        results = []
        
        for point in points:
            row_idx = point.get('row')
            col_name = point.get('column')
            
            if row_idx is None or col_name is None:
                continue
                
            if col_name not in data_manager.data.columns:
                continue
                
            col_idx = data_manager.data.columns.get_loc(col_name)
            flag = data_manager.get_point_flags(row_idx, col_idx)
            
            results.append({
                'row': row_idx,
                'column': col_name,
                'value': str(data_manager.data.iloc[row_idx, col_idx]),
                'flag': flag.value
            })
            
        return jsonify({'success': True, 'flags': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@main.route('/api/update-outlier-flags', methods=['POST'])
def update_outlier_flags():
    try:
        data = request.get_json()
        if not data or 'update_flags' not in data:
            return jsonify({'success': False, 'error': 'Invalid request data'})
            
        if data['update_flags']:
            data_manager._update_numeric_IQR_outlier_flags()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'No update requested'})
            
    except Exception as e:
        logger.error(f"Error updating outlier flags: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}) 