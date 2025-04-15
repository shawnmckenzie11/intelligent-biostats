from flask import Blueprint, render_template, jsonify, request, current_app
from .core.data_manager import DataManager, DataPointFlag
import pandas as pd
import numpy as np
import logging
import os

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

def get_data_manager():
    """Get the data manager instance from the Flask app context."""
    if not hasattr(current_app, 'data_manager'):
        current_app.data_manager = DataManager()
    return current_app.data_manager

@main.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@main.route('/api/descriptive-stats')
def get_descriptive_stats():
    """Get descriptive statistics for the dataset."""
    try:
        data_manager = get_data_manager()
        if data_manager.data is None:
            return jsonify({'success': False, 'error': 'No data loaded'})
            
        # Get descriptive stats
        stats = data_manager.get_column_descriptive_stats()
        if stats is None:
            data_manager.calculate_descriptive_stats()
            stats = data_manager.get_column_descriptive_stats()
            
        if stats is None:
            return jsonify({'success': False, 'error': 'Failed to calculate descriptive statistics'})
            
        # Add flag counts
        stats['flag_counts'] = {
            col: {
                flag.value: int(np.sum(data_manager.point_flags[:, idx] == flag))
                for flag in DataPointFlag
            }
            for idx, col in enumerate(data_manager.data.columns)
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@main.route('/api/column-stats/<column_name>')
def get_column_stats(column_name):
    """Get statistics for a specific column."""
    try:
        data_manager = get_data_manager()
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
                'Missingues': str(column_data.isna().sum())
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
        data_manager = get_data_manager()
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

@main.route('/api/update-column-flags', methods=['POST'])
def update_column_flags():
    try:
        data_manager = get_data_manager()
        data = request.get_json()
        logger.debug(f"Received update column flags request with data: {data}")
        
        if not data:
            logger.error("No JSON data received in request")
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        column = data.get('column')
        logger.debug(f"Available columns in data_manager: {data_manager.data.columns.tolist() if data_manager.data is not None else 'No data loaded'}")
        logger.debug(f"Looking for column: {column}")
        logger.debug(f"Column type: {type(column)}")
        
        if not column:
            logger.error("No column name provided in request")
            return jsonify({
                'success': False,
                'error': 'Column name is required'
            }), 400
            
        if data_manager.data is None:
            logger.error("No data loaded in data_manager")
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
            
        # Check if column exists using case-insensitive comparison
        actual_column = None
        for col in data_manager.data.columns:
            if col.lower() == column.lower():
                actual_column = col
                break
                
        if actual_column is None:
            logger.error(f"Column '{column}' not found in dataset. Available columns: {data_manager.data.columns.tolist()}")
            return jsonify({
                'success': False,
                'error': f"Column '{column}' not found in dataset"
            }), 400
            
        # Use the actual column name from here on
        column = actual_column
        
        try:
            min_value = float(data.get('min_value'))
            max_value = float(data.get('max_value'))
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid min_value or max_value: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Invalid min_value or max_value'
            }), 400
            
        if min_value >= max_value:
            logger.error(f"Invalid range: min_value ({min_value}) >= max_value ({max_value})")
            return jsonify({
                'success': False,
                'error': 'Minimum value must be less than maximum value'
            }), 400
            
        logger.debug(f"Attempting to add range flags for column {column} with range [{min_value}, {max_value}]")
        
        # Add new range flags
        flag_stats = data_manager.add_new_column_range_flags(column, min_value, max_value)
        logger.debug(f"Successfully updated flags. Stats: {flag_stats}")
        
        return jsonify({
            'success': True,
            'flag_stats': flag_stats
        })
    except Exception as e:
        logger.error(f"Error updating column flags: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@main.route('/api/update-column-stats', methods=['POST'])
def update_column_stats():
    try:
        data_manager = get_data_manager()
        data = request.get_json()
        column = data.get('column')
        
        # Update column statistics ignoring flags
        stats = data_manager.update_column_data_ignoring_flags(column)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@main.route('/api/column-data-and-flags', methods=['POST'])
def get_column_data_and_flags():
    """Get all data points and flags for a specific column."""
    try:
        data_manager = get_data_manager()
        data = request.get_json()
        
        logger.debug(f"Received request for column data and flags: {data}")
        
        if not data or 'column' not in data:
            logger.error("No column name provided in request")
            return jsonify({
                'success': False,
                'error': 'Column name is required'
            }), 400
            
        column = data.get('column')
        
        if data_manager.data is None:
            logger.error("No data loaded in data_manager")
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
            
        # Get column index from the row's data-column attribute
        column_idx = None
        for idx, col in enumerate(data_manager.data.columns):
            if col == column:
                column_idx = idx
                break
        
        if column_idx is None:
            logger.error(f"Column '{column}' not found. Available columns: {data_manager.data.columns.tolist()}")
            return jsonify({
                'success': False,
                'error': f"Column '{column}' not found in dataset"
            }), 400
            
        # Get column data and flags
        values = data_manager.data[column].tolist()
        flags = [flag.value for flag in data_manager.point_flags[:, column_idx]]
        
        logger.debug(f"Returning data for column '{column}':")
        logger.debug(f"Values: {values[:5]}... (showing first 5)")
        logger.debug(f"Flags: {flags[:5]}... (showing first 5)")
        
        return jsonify({
            'success': True,
            'column': column,
            'values': values,
            'flags': flags
        })
        
    except Exception as e:
        logger.error(f"Error getting column data and flags: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400 