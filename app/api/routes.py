from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
import io
from app.core.ai_engine import AIEngine
from collections import OrderedDict
import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive 'Agg'
import matplotlib.pyplot as plt
import seaborn as sns
import base64

api = Blueprint('api', __name__)

# Define global variable at module level
current_df = None

# Add this check to prevent duplicate initialization
if not hasattr(api, '_initialized'):
    ai_engine = AIEngine()
    api._initialized = True

@api.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and return initial analysis."""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({
                'success': False,
                'error': 'File must be a CSV'
            }), 400

        # Read CSV in chunks using pandas
        global current_df
        current_df = pd.read_csv(file, chunksize=10000)
        current_df = pd.concat(current_df, ignore_index=True)
        
        # Create preview dict from first 5 rows
        preview_dict = OrderedDict()
        preview_df = current_df.head()
        for column in preview_df.columns:
            preview_dict[str(column)] = [
                None if pd.isna(x) else x 
                for x in preview_df[column].tolist()
            ]
        
        # Convert dtypes to strings to make them JSON serializable
        column_types = {
            str(col): str(dtype) 
            for col, dtype in current_df.dtypes.items()
        }
        
        return jsonify({
            'success': True,
            'info': {
                'rows': len(current_df),
                'columns': len(current_df.columns),
                'column_types': column_types,
                'preview': preview_dict
            }
        })
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

@api.route('/descriptive-stats', methods=['GET'])
def get_descriptive_stats():
    """Get descriptive statistics for the current dataset."""
    try:
        global current_df
        if current_df is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
            
        stats = {
            'file_stats': {
                'rows': len(current_df),
                'columns': len(current_df.columns),
                'memory_usage': f"{current_df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB"
            },
            'column_types': {
                'numeric': len(current_df.select_dtypes(include=[np.number]).columns),
                'categorical': len(current_df.select_dtypes(include=['object', 'category']).columns),
                'boolean': len([col for col in current_df.columns if current_df[col].nunique() == 2]),
                'datetime': len(current_df.select_dtypes(include=['datetime64']).columns),
                'columns': current_df.columns.tolist()
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

def generate_plot(data, column_name, plot_type):
    """Generate a plot and return it as a base64 encoded string."""
    plt.figure(figsize=(8, 6))
    
    try:
        if plot_type == 'histogram':
            sns.histplot(data=data, x=column_name, kde=True)
            plt.title(f'Distribution of {column_name}')
        elif plot_type == 'barplot':
            value_counts = data[column_name].value_counts()
            sns.barplot(x=value_counts.index, y=value_counts.values)
            plt.title(f'Value Distribution of {column_name}')
            plt.xticks(rotation=45)
        
        # Convert plot to base64 string
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode()
    finally:
        plt.close()  # Ensure the figure is closed even if an error occurs

@api.route('/column-data/<column_name>', methods=['GET'])
def get_column_data(column_name):
    """Get detailed data and statistics for a specific column."""
    try:
        global current_df
        if current_df is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
            
        if column_name not in current_df.columns:
            return jsonify({
                'success': False,
                'error': 'Column not found'
            }), 400
            
        # Get column data and statistics
        column_data = current_df[column_name]
        
        # Determine column type
        col_type = None
        if pd.api.types.is_numeric_dtype(column_data):
            col_type = 'numeric'
            if column_data.nunique() < 20:  # threshold for discrete
                col_type = 'discrete'
        elif column_data.nunique() == 2:
            col_type = 'boolean'
        elif pd.api.types.is_datetime64_any_dtype(column_data):
            col_type = 'timeseries'
        else:
            col_type = 'categorical'
        
        # Get basic statistics
        stats = {
            'Type': col_type,
            'Missing Values': str(column_data.isna().sum()),
            'Unique Values': str(column_data.nunique())
        }
        
        # Add type-specific statistics
        if col_type in ['numeric', 'discrete']:
            stats.update({
                'Mean': f"{column_data.mean():.2f}",
                'Median': f"{column_data.median():.2f}",
                'Std Dev': f"{column_data.std():.2f}",
                'Min': f"{column_data.min():.2f}",
                'Max': f"{column_data.max():.2f}"
            })
        elif col_type == 'categorical':
            value_counts = column_data.value_counts()
            stats['Most Common'] = f"{value_counts.index[0]} ({value_counts.iloc[0]} times)"
            stats['Value Distribution'] = value_counts.head(5).to_dict()
        elif col_type == 'boolean':
            value_counts = column_data.value_counts()
            stats['True Count'] = str(value_counts.get(True, 0))
            stats['False Count'] = str(value_counts.get(False, 0))
        elif col_type == 'timeseries':
            stats.update({
                'Start Date': str(column_data.min()),
                'End Date': str(column_data.max()),
                'Date Range': f"{column_data.max() - column_data.min()}"
            })
        
        # Generate appropriate plot based on column type
        plot_data = None
        if col_type in ['numeric', 'discrete']:
            plot_data = generate_plot(current_df, column_name, 'histogram')
        else:
            plot_data = generate_plot(current_df, column_name, 'barplot')
        
        return jsonify({
            'success': True,
            'column_data': {
                'stats': stats,
                'plot': plot_data
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
