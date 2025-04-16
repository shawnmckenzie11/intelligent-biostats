from flask import Blueprint, render_template, jsonify, request, current_app, g
from .core.data_manager import DataManager, DataPointFlag
import pandas as pd
import numpy as np
import logging
import os
import threading
import time

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
            # Update progress to show we're starting final calculations
            data_manager.update_progress(96, 'Calculating final descriptive statistics...')
            time.sleep(0.5)
            
            data_manager.update_progress(97, 'Processing column statistics...')
            data_manager.calculate_descriptive_stats()
            time.sleep(0.5)
            
            data_manager.update_progress(98, 'Finalizing calculations...')
            stats = data_manager.get_column_descriptive_stats()
            time.sleep(0.5)
            
        if stats is None:
            data_manager.update_progress(100, 'Complete', True)
            return jsonify({'success': False, 'error': 'Failed to calculate descriptive statistics'})
            
        # Add flag counts
        data_manager.update_progress(99, 'Adding flag information...')
        stats['flag_counts'] = {
            col: {
                flag.value: int(np.sum(data_manager.point_flags[:, idx] == flag))
                for flag in DataPointFlag
            }
            for idx, col in enumerate(data_manager.data.columns)
        }
        
        # Mark as complete
        data_manager.update_progress(100, 'Complete', True)
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        # Mark as complete with error
        data_manager.update_progress(100, f'Error: {str(e)}', True)
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

@main.route('/api/start-descriptive-stats', methods=['GET'])
def start_descriptive_stats():
    """Start the descriptive statistics calculation process."""
    try:
        data_manager = get_data_manager()
        if data_manager.data is None:
            return jsonify({'success': False, 'error': 'No data loaded'})
        
        logger.debug("Starting descriptive stats calculation")
        
        # Initialize progress tracking using thread-safe method
        data_manager.update_progress(5, 'Starting analysis...')
        logger.debug("Initialized stats progress tracking")
        
        # Start calculation in a background thread
        def calculate_stats():
            try:
                logger.debug("Starting statistics calculation in background thread")
                
                # Get data manager in thread context
                with current_app.app_context():
                    dm = get_data_manager()
                    
                    # Analyze column types (20%)
                    logger.debug("Starting column type analysis")
                    dm.update_progress(15, 'Analyzing column types...')
                    time.sleep(0.5)  # Brief pause to ensure progress is visible
                    dm.analyze_column_types()
                    dm.update_progress(20, 'Column types analyzed')
                    time.sleep(0.5)
                    
                    # Calculate basic statistics (40%)
                    logger.debug("Starting basic statistics calculation")
                    dm.update_progress(30, 'Calculating basic statistics...')
                    time.sleep(0.5)
                    dm.calculate_basic_stats()
                    dm.update_progress(40, 'Basic statistics calculated')
                    time.sleep(0.5)
                    
                    # Analyze distributions (60%)
                    logger.debug("Starting distribution analysis")
                    dm.update_progress(50, 'Analyzing distributions...')
                    time.sleep(0.5)
                    dm.analyze_distributions()
                    dm.update_progress(60, 'Distribution analysis complete')
                    time.sleep(0.5)
                    
                    # Detect outliers (80%)
                    logger.debug("Starting outlier detection")
                    dm.update_progress(70, 'Detecting outliers...')
                    time.sleep(0.5)
                    dm.detect_outliers()
                    dm.update_progress(80, 'Outlier detection complete')
                    time.sleep(0.5)
                    
                    # Calculate final stats with intermediate updates
                    logger.debug("Starting final stats calculation")
                    dm.update_progress(85, 'Processing column metadata...')
                    time.sleep(1.0)  # Longer pause during intensive calculation
                    
                    # Break down final calculation into more granular steps
                    dm.update_progress(87, 'Analyzing data quality...')
                    time.sleep(1.0)
                    
                    dm.update_progress(90, 'Calculating column statistics...')
                    time.sleep(1.0)
                    
                    dm.update_progress(93, 'Processing categorical data...')
                    time.sleep(1.0)
                    
                    dm.update_progress(95, 'Finalizing calculations...')
                    time.sleep(1.0)
                    
                    logger.debug("Starting final descriptive stats calculation")
                    dm.calculate_descriptive_stats()
                    logger.debug("Descriptive stats calculation completed")
                    
                    # Mark as complete
                    dm.update_progress(100, 'Complete', True)
                    logger.debug("Progress marked as complete")
                    
            except Exception as e:
                logger.error(f"Error in background calculation: {str(e)}", exc_info=True)
                with current_app.app_context():
                    dm = get_data_manager()
                    with dm._progress_lock:
                        dm.stats_progress = {
                            'error': str(e),
                            'is_complete': True
                        }
        
        # Start the calculation thread
        thread = threading.Thread(target=calculate_stats)
        thread.daemon = True  # Make thread daemon so it doesn't block app shutdown
        thread.start()
        logger.debug("Started background calculation thread")
        
        return jsonify({
            'success': True,
            'message': 'Started statistics calculation'
        })
        
    except Exception as e:
        logger.error(f"Error starting stats calculation: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/descriptive-stats-progress', methods=['GET'])
def get_descriptive_stats_progress():
    """Get the current progress of descriptive statistics calculation."""
    try:
        data_manager = get_data_manager()
        if not hasattr(data_manager, 'stats_progress'):
            return jsonify({
                'success': False,
                'error': 'No calculation in progress'
            }), 400
            
        progress = data_manager.stats_progress
        if 'error' in progress:
            return jsonify({
                'success': False,
                'error': progress['error']
            }), 500
            
        return jsonify({
            'success': True,
            'progress': {
                'percent': progress['percent'],
                'current_task': progress['current_task'],
                'is_complete': progress['is_complete']
            }
        })
        
    except Exception as e:
        logger.error(f"Error checking progress: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 