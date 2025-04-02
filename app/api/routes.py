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
        elif plot_type == 'density':
            sns.kdeplot(data=data, x=column_name, fill=True)
            plt.title(f'Density Plot of {column_name}')
        elif plot_type == 'boxplot':
            sns.boxplot(y=data[column_name])
            plt.title(f'Box Plot of {column_name}')
        elif plot_type == 'qqplot':
            from scipy import stats
            stats.probplot(data[column_name].dropna(), dist="norm", plot=plt)
            plt.title(f'Q-Q Plot of {column_name}')
        elif plot_type == 'barplot':
            value_counts = data[column_name].value_counts()
            sns.barplot(x=value_counts.index, y=value_counts.values)
            plt.title(f'Value Distribution of {column_name}')
            plt.xticks(rotation=45)
        elif plot_type == 'pie':
            value_counts = data[column_name].value_counts()
            plt.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%')
            plt.title(f'Distribution of {column_name}')
        elif plot_type == 'dotplot':
            value_counts = data[column_name].value_counts()
            plt.plot(value_counts.index, value_counts.values, 'o-')
            plt.title(f'Dot Plot of {column_name}')
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
        
        # Generate appropriate plots based on column type
        plots = {}
        if col_type in ['numeric', 'discrete']:
            plots = {
                'histogram': generate_plot(current_df, column_name, 'histogram'),
                'density': generate_plot(current_df, column_name, 'density'),
                'boxplot': generate_plot(current_df, column_name, 'boxplot'),
                'qqplot': generate_plot(current_df, column_name, 'qqplot')
            }
        else:
            plots = {
                'barplot': generate_plot(current_df, column_name, 'barplot'),
                'pie': generate_plot(current_df, column_name, 'pie'),
                'dotplot': generate_plot(current_df, column_name, 'dotplot')
            }
        
        return jsonify({
            'success': True,
            'column_data': {
                'stats': stats,
                'plots': plots
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@api.route('/smart-recommendations', methods=['GET'])
def get_smart_recommendations():
    """Get prioritized statistical recommendations based on data characteristics."""
    try:
        global current_df
        if current_df is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
            
        # Get column types
        numeric_cols = current_df.select_dtypes(include=[np.number]).columns
        categorical_cols = current_df.select_dtypes(include=['object', 'category']).columns
        boolean_cols = [col for col in current_df.columns if current_df[col].nunique() == 2]
        
        # For large datasets, limit analysis to most relevant columns
        MAX_COLS_PER_TYPE = 20  # Maximum number of columns to analyze per type
        
        # Select most relevant numeric columns (those with highest variance)
        if len(numeric_cols) > MAX_COLS_PER_TYPE:
            variances = current_df[numeric_cols].var()
            numeric_cols = variances.nlargest(MAX_COLS_PER_TYPE).index
        
        # Select most relevant categorical columns (those with most unique values)
        if len(categorical_cols) > MAX_COLS_PER_TYPE:
            unique_counts = current_df[categorical_cols].nunique()
            categorical_cols = unique_counts.nlargest(MAX_COLS_PER_TYPE).index
        
        # Get distribution insights only for selected numeric columns
        distribution_insights = ai_engine.get_distribution_insights(current_df[numeric_cols])
        
        # Organize recommendations by priority and strength
        recommendations = {
            'critical_issues': [],  # Issues that must be addressed before analysis
            'high_priority': [],    # Strong recommendations based on data characteristics
            'suggested_analyses': [], # Recommended analyses based on data structure
            'data_quality': [],     # Data quality considerations
            'methodological_notes': [] # General methodological considerations
        }
        
        # Process critical issues first
        missing_data = current_df.isnull().sum()
        if missing_data.any():
            # Only show top 5 columns with missing data
            top_missing = missing_data[missing_data > 0].nlargest(5)
            recommendations['critical_issues'].append({
                'type': 'missing_data',
                'message': 'Missing data detected. This must be addressed before analysis.',
                'details': {
                    'affected_columns': top_missing.index.tolist(),
                    'missing_counts': top_missing.to_dict(),
                    'total_columns_with_missing': len(missing_data[missing_data > 0])
                },
                'suggested_tests': ['Multiple imputation', 'Complete case analysis'],
                'references': ['Rubin, D.B. (1976). Inference and Missing Data']
            })
        
        # Process high priority recommendations
        n_samples = len(current_df)
        if n_samples < 30:
            recommendations['high_priority'].append({
                'type': 'sample_size',
                'message': 'Small sample size detected. This may affect statistical power.',
                'details': {
                    'sample_size': n_samples,
                    'minimum_recommended': 30
                },
                'suggested_tests': ['Power analysis', 'Non-parametric tests'],
                'references': ['Cohen, J. (1992). Statistical Power Analysis']
            })
        
        # Process distribution insights for numeric columns
        for col, insights in distribution_insights.items():
            if insights['distribution_type'] != "Normal":
                recommendations['high_priority'].append({
                    'type': 'distribution',
                    'message': f'Non-normal distribution detected in {col}.',
                    'details': {
                        'column': col,
                        'distribution_type': insights['distribution_type'],
                        'skewness': insights['skewness'],
                        'kurtosis': insights['kurtosis']
                    },
                    'suggested_tests': ['Non-parametric tests', 'Data transformation'],
                    'references': ['Box, G.E.P. & Cox, D.R. (1964). An Analysis of Transformations']
                })
        
        # Process suggested analyses based on data structure
        if len(numeric_cols) >= 2:
            recommendations['suggested_analyses'].append({
                'type': 'correlation',
                'message': 'Multiple numeric variables present. Consider correlation analysis.',
                'details': {
                    'variable_count': len(numeric_cols),
                    'analyzed_columns': numeric_cols.tolist()
                },
                'suggested_tests': ['Pearson correlation', 'Spearman correlation'],
                'references': ['Pearson, K. (1895). Notes on regression and inheritance']
            })
        
        if len(categorical_cols) >= 2:
            recommendations['suggested_analyses'].append({
                'type': 'categorical',
                'message': 'Multiple categorical variables present. Consider contingency analysis.',
                'details': {
                    'variable_count': len(categorical_cols),
                    'analyzed_columns': categorical_cols.tolist()
                },
                'suggested_tests': ['Chi-square test', 'Fisher\'s exact test'],
                'references': ['Fisher, R.A. (1922). On the interpretation of chi-square']
            })
        
        # Process data quality considerations
        constant_cols = [col for col in current_df.columns if current_df[col].nunique() == 1]
        if constant_cols:
            # Only show first 5 constant columns
            recommendations['data_quality'].append({
                'type': 'constant_variable',
                'message': f'Constant values detected in {len(constant_cols)} columns.',
                'details': {
                    'example_columns': constant_cols[:5],
                    'total_constant_columns': len(constant_cols)
                },
                'suggested_tests': ['Variable removal', 'Data validation'],
                'references': ['Tukey, J.W. (1977). Exploratory Data Analysis']
            })
        
        # Add methodological notes
        recommendations['methodological_notes'].append({
            'type': 'general',
            'message': 'Consider documenting all data transformations and statistical methods used.',
            'suggested_tests': ['Method documentation', 'Reproducibility check'],
            'references': ['Wilkinson, L. (1999). Statistical Methods in Psychology Journals']
        })
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
