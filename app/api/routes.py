from flask import Blueprint, request, jsonify, render_template, current_app
import pandas as pd
import numpy as np
import io
from app.core.ai_engine import AIEngine
from app.core.database import AnalysisHistoryDB
from app.core.data_manager import DataManager, DataPointFlag
from collections import OrderedDict
import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive 'Agg'
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from scipy import stats
import json
from datetime import datetime
import logging

# Get the logger configured in app/__init__.py
logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

# Initialize components
if not hasattr(api, '_initialized'):
    ai_engine = AIEngine()
    db = AnalysisHistoryDB()
    api._initialized = True

@api.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and return initial analysis."""
    try:
        if 'file' not in request.files:
            logger.error("No file in request.files")
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']
        if not file.filename:
            logger.error("Empty filename")
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
            
        if not file.filename.endswith('.csv'):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({
                'success': False,
                'error': 'File must be a CSV'
            }), 400

        logger.info(f"Attempting to load file: {file.filename}")
        
        # Load data using data manager
        success, error = current_app.data_manager.load_data(file_obj=file)
        if not success:
            logger.error(f"Data manager load_data failed: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        # Verify data was loaded
        if current_app.data_manager.data is None or current_app.data_manager.data.empty:
            logger.error("Data manager has no data after load")
            return jsonify({
                'success': False,
                'error': 'Failed to load data - file may be empty or invalid'
            }), 400
        
        logger.info("File loaded successfully, getting preview")
        
        # Get data preview
        preview_dict = current_app.data_manager.get_data_preview()
        
        # Get column types from metadata
        column_types = {
            str(col): str(dtype) 
            for col, dtype in zip(current_app.data_manager.data.columns, 
                                current_app.data_manager.metadata['column_types']['column_types_list'])
        }
        
        logger.info("Returning success response")
        return jsonify({
            'success': True,
            'info': {
                'rows': len(current_app.data_manager.data),
                'columns': len(current_app.data_manager.data.columns),
                'column_types': column_types,
                'preview': preview_dict
            }
        })
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        }), 500

@api.route('/delete-columns-at-start', methods=['POST'])
def delete_columns_at_start():
    """Handle data modification requests."""
    try:
        if current_app.data_manager.data is None:
            return jsonify({
                'success': False,
                'error': 'No data has been uploaded yet'
            }), 400
            
        data = request.get_json()
        columns = data.get('columns')
        
        if not columns:
            return jsonify({
                'success': False,
                'error': 'No columns specified'
            }), 400
            
        # Delete the columns
        success, message, preview = current_app.data_manager.delete_columns(columns)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'preview': preview
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Error in delete_columns: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/analyze-options', methods=['GET'])
def get_analysis_options():
    """Get available analysis options based on current data."""
    try:
        if current_app.data_manager.data is None:
            return jsonify({
                'success': False,
                'error': 'No data has been uploaded yet'
            }), 400
            
        # Use AI engine to determine appropriate analyses
        options = ai_engine.get_analysis_options(current_app.data_manager.data)
        
        return jsonify({
            'success': True,
            'options': options
        })
    except Exception as e:
        logger.error(f"Error getting analysis options: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/analyze', methods=['POST'])
def analyze_data():
    """Perform statistical analysis."""
    try:
        if current_app.data_manager.data is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400

        data = request.json
        analysis_type = data.get('analysis_type')
        
        if analysis_type == 'one_sample_t':
            column = data.get('column')
            hypothesis_value = float(data.get('hypothesis_value'))
            confidence_level = float(data.get('confidence_level'))
            
            if column not in current_app.data_manager.data.columns:
                return jsonify({
                    'success': False,
                    'error': f'Column {column} not found'
                }), 400
                
            # Get the data for the selected column
            sample_data = current_app.data_manager.data[column].dropna()
            
            # Perform one-sample t-test
            t_statistic, p_value = stats.ttest_1samp(sample_data, hypothesis_value)
            
            # Calculate confidence interval
            ci = stats.t.interval(confidence_level, len(sample_data)-1, 
                                loc=sample_data.mean(), 
                                scale=stats.sem(sample_data))
            
            # Calculate standard error
            std_error = stats.sem(sample_data)
            
            results = {
                'statistic': float(t_statistic),
                'p_value': float(p_value),
                'sample_mean': float(sample_data.mean()),
                'std_error': float(std_error),
                'confidence_interval': [float(ci[0]), float(ci[1])],
                'degrees_of_freedom': len(sample_data) - 1
            }
            
            # Create conclusion
            conclusion = f"One-sample t-test on {column}: "
            if p_value < 0.05:
                conclusion += f"Significant difference from {hypothesis_value} (p={p_value:.3f}). "
            else:
                conclusion += f"No significant difference from {hypothesis_value} (p={p_value:.3f}). "
            conclusion += f"95% CI: [{ci[0]:.2f}, {ci[1]:.2f}]"
            
            # Store analysis in database
            db.add_analysis(
                input_file=current_app.data_manager.current_file or "Unknown",
                modifications=json.dumps(current_app.data_manager.modifications_history) if current_app.data_manager.modifications_history else None,
                test_name="One-Sample T-Test",
                test_details=results,
                conclusion=conclusion
            )
            
            return jsonify({
                'success': True,
                'results': results,
                'conclusion': conclusion
            })
            
        return jsonify({
            'success': False,
            'error': 'Invalid analysis type'
        }), 400
        
    except Exception as e:
        logger.error(f"Error performing analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/analysis-history', methods=['GET'])
def get_analysis_history():
    """Get the history of all analyses performed."""
    try:
        analyses = db.get_all_analyses()
        return jsonify({
            'success': True,
            'analyses': analyses
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@api.route('/recommendations', methods=['GET'])
def get_recommendations():
    """Get AI recommendations."""
    pass

@api.route('/descriptive-stats', methods=['GET'])
def get_descriptive_stats():
    """Get descriptive statistics for the current dataset."""
    try:
        logger.debug(f"Data manager state: {current_app.data_manager is None}")
        if current_app.data_manager is None:
            logger.error("Data manager is None")
            return jsonify({
                'success': False,
                'error': 'Data manager not initialized'
            }), 500
            
        if current_app.data_manager.data is None:
            logger.error("No data loaded in data manager")
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
            
        logger.debug(f"Data shape: {current_app.data_manager.data.shape if current_app.data_manager.data is not None else 'None'}")
        logger.debug(f"Data columns: {current_app.data_manager.data.columns.tolist() if current_app.data_manager.data is not None else 'None'}")
            
        # Get column types and missing values in a single pass
        column_types_list = []
        missing_values_by_column = {}
        distribution_analysis = {}  # New dictionary to store distribution analysis
        outlier_info = {}  # New dictionary to store outlier information
        
        for i, col in enumerate(current_app.data_manager.data.columns):
            try:
                # Determine column type
                if pd.api.types.is_numeric_dtype(current_app.data_manager.data[col]):
                    if current_app.data_manager.data[col].nunique() < 20:  # threshold for discrete
                        column_types_list.append('discrete')
                    else:
                        column_types_list.append('numeric')
                        # Calculate skewness and kurtosis for numeric columns
                        skewness = current_app.data_manager.data[col].skew()
                        kurtosis = current_app.data_manager.data[col].kurtosis()
                        distribution_analysis[col] = {
                            'skewness': float(skewness),
                            'kurtosis': float(kurtosis),
                            'transformation_suggestion': get_transformation_suggestion(skewness, kurtosis)
                        }
                        
                        # Calculate outliers for numeric columns
                        mean = current_app.data_manager.data[col].mean()
                        std = current_app.data_manager.data[col].std()
                        q1 = current_app.data_manager.data[col].quantile(0.25)
                        q3 = current_app.data_manager.data[col].quantile(0.75)
                        iqr = q3 - q1
                        
                        # Determine distribution type and set appropriate thresholds
                        if abs(skewness) < 0.5 and abs(kurtosis) < 2:  # Normal
                            lower_bound = mean - 3 * std
                            upper_bound = mean + 3 * std
                        elif abs(skewness) > 1:  # Skewed
                            lower_bound = q1 - 1.5 * iqr
                            upper_bound = q3 + 1.5 * iqr
                        else:  # Heavy-tailed
                            lower_bound = q1 - 2.5 * iqr
                            upper_bound = q3 + 2.5 * iqr
                        
                        # Count outliers
                        outliers = current_app.data_manager.data[col][(current_app.data_manager.data[col] < lower_bound) | (current_app.data_manager.data[col] > upper_bound)]
                        outlier_info[col] = {
                            'count': int(len(outliers)),
                            'percentage': float(len(outliers) / len(current_app.data_manager.data[col]) * 100)
                        }
                elif pd.api.types.is_datetime64_any_dtype(current_app.data_manager.data[col]):
                    column_types_list.append('timeseries')
                else:
                    # For non-numeric, non-datetime columns
                    if current_app.data_manager.data[col].nunique() == 2:
                        # Check if the values are actually boolean-like
                        unique_values = current_app.data_manager.data[col].dropna().unique()
                        if all(val in [True, False, 'True', 'False', 'true', 'false', '1', '0', 1, 0] for val in unique_values):
                            column_types_list.append('boolean')
                        else:
                            column_types_list.append('categorical')
                    else:
                        column_types_list.append('categorical')
                
                # Count missing values
                missing_count = current_app.data_manager.data[col].isna().sum()
                if missing_count > 0:
                    missing_values_by_column[col] = int(missing_count)
            except Exception as e:
                logger.error(f"Error processing column {col}: {str(e)}", exc_info=True)
                continue
            
        # Calculate total missing values
        missing_values = sum(missing_values_by_column.values())
            
        stats = {
            'file_stats': {
                'rows': len(current_app.data_manager.data),
                'columns': len(current_app.data_manager.data.columns),
                'memory_usage': f"{current_app.data_manager.data.memory_usage(deep=True).sum() / (1024*1024):.2f} MB",
                'missing_values': int(missing_values)
            },
            'column_types': {
                'numeric': len([col for col, type_ in zip(current_app.data_manager.data.columns, column_types_list) if type_ == 'numeric']),
                'categorical': len([col for col, type_ in zip(current_app.data_manager.data.columns, column_types_list) if type_ == 'categorical']),
                'boolean': len([col for col, type_ in zip(current_app.data_manager.data.columns, column_types_list) if type_ == 'boolean']),
                'datetime': len([col for col, type_ in zip(current_app.data_manager.data.columns, column_types_list) if type_ == 'timeseries']),
                'columns': current_app.data_manager.data.columns.tolist(),
                'column_types_list': column_types_list
            },
            'missing_values_by_column': missing_values_by_column,
            'distribution_analysis': distribution_analysis,
            'outlier_info': outlier_info  # Add outlier information to the response
        }
        
        logger.debug(f"Successfully generated stats: {stats}")
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error in get_descriptive_stats: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

def get_transformation_suggestion(skewness, kurtosis):
    """Determine appropriate transformation based on skewness and kurtosis values."""
    suggestions = []
    
    # Handle skewness
    if abs(skewness) > 1:
        if skewness > 1:
            suggestions.append("Log transformation (for strong positive skew)")
            if skewness > 2:
                suggestions.append("Consider reciprocal transformation for very severe positive skew")
            else:
                suggestions.append("Square root transformation as alternative")
        else:  # skewness < -1
            suggestions.append("Square transformation (for strong negative skew)")
            if skewness < -2:
                suggestions.append("Consider cube transformation for very severe negative skew")
            else:
                suggestions.append("Exponential transformation as alternative")
    elif 0.5 < abs(skewness) <= 1:
        if skewness > 0:
            suggestions.append("Square root transformation (for moderate positive skew)")
        else:
            suggestions.append("Square transformation (for moderate negative skew)")
    
    # Handle kurtosis
    if kurtosis > 3.5:
        suggestions.append("Box-Cox transformation (for heavy tails)")
        if kurtosis > 4:
            suggestions.append("Consider Yeo-Johnson transformation for very heavy tails")
    elif kurtosis < 2.5:
        suggestions.append("Consider checking for outliers (for light tails)")
    
    if not suggestions:
        return "No transformation needed - distribution appears normal"
    
    # Prioritize the most appropriate transformation
    if "Log transformation" in suggestions:
        return "Log transformation (recommended for positive skew)"
    elif "Square transformation" in suggestions:
        return "Square transformation (recommended for negative skew)"
    elif "Box-Cox transformation" in suggestions:
        return "Box-Cox transformation (recommended for heavy tails)"
    else:
        return " | ".join(suggestions)

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
        if current_app.data_manager.data is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
            
        if column_name not in current_app.data_manager.data.columns:
            return jsonify({
                'success': False,
                'error': 'Column not found'
            }), 400
            
        # Get column data and statistics
        column_data = current_app.data_manager.data[column_name]
        
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
            # Calculate basic statistics
            mean = column_data.mean()
            median = column_data.median()
            std = column_data.std()
            q1 = column_data.quantile(0.25)
            q3 = column_data.quantile(0.75)
            iqr = q3 - q1
            skewness = column_data.skew()
            kurtosis = column_data.kurtosis()
            
            # Determine distribution type
            distribution_type = get_distribution_type(column_data)
            
            # Initialize outlier flags array
            outlier_flags = np.zeros(len(column_data), dtype=bool)
            
            # Detect outliers based on distribution type
            if distribution_type == "Normal":
                # For normal distributions: use mean ± 3 SD
                lower_bound = mean - 3 * std
                upper_bound = mean + 3 * std
                outlier_flags = (column_data < lower_bound) | (column_data > upper_bound)
            elif distribution_type in ["Right-skewed", "Left-skewed"]:
                # For skewed distributions: use IQR method with adjusted thresholds
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outlier_flags = (column_data < lower_bound) | (column_data > upper_bound)
            elif distribution_type == "Heavy-tailed":
                # For heavy-tailed distributions: use more conservative approach
                lower_bound = q1 - 2.5 * iqr
                upper_bound = q3 + 2.5 * iqr
                outlier_flags = (column_data < lower_bound) | (column_data > upper_bound)
            
            # Count outliers
            outlier_count = outlier_flags.sum()
            
            stats.update({
                'Mean': f"{mean:.2f}",
                'Median': f"{median:.2f}",
                'Std Dev': f"{std:.2f}",
                'Min': f"{column_data.min():.2f}",
                'Max': f"{column_data.max():.2f}",
                'Range': f"{column_data.max() - column_data.min():.2f}",
                'Skewness': f"{skewness:.2f}",
                'Kurtosis': f"{kurtosis:.2f}",
                'Distribution': distribution_type,
                'Outliers': {
                    'count': int(outlier_count),
                    'percentage': f"{(outlier_count / len(column_data) * 100):.2f}%",
                    'flags': outlier_flags.tolist()
                }
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
                'histogram': generate_plot(current_app.data_manager.data, column_name, 'histogram'),
                'density': generate_plot(current_app.data_manager.data, column_name, 'density'),
                'boxplot': generate_plot(current_app.data_manager.data, column_name, 'boxplot'),
                'qqplot': generate_plot(current_app.data_manager.data, column_name, 'qqplot')
            }
        else:
            plots = {
                'barplot': generate_plot(current_app.data_manager.data, column_name, 'barplot'),
                'pie': generate_plot(current_app.data_manager.data, column_name, 'pie'),
                'dotplot': generate_plot(current_app.data_manager.data, column_name, 'dotplot')
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
        }), 500

def get_distribution_type(column_data):
    """Determine the type of distribution based on skewness and kurtosis."""
    skewness = column_data.skew()
    kurtosis = column_data.kurtosis()
    
    # Normal distribution: |skewness| < 0.5 and |kurtosis| < 2
    if abs(skewness) < 0.5 and abs(kurtosis) < 2:
        return "Normal"
    # Right-skewed: skewness > 1
    elif skewness > 1:
        return "Right-skewed"
    # Left-skewed: skewness < -1
    elif skewness < -1:
        return "Left-skewed"
    # Heavy-tailed: kurtosis > 3
    elif kurtosis > 3:
        return "Heavy-tailed"
    # Light-tailed: kurtosis < 1
    elif kurtosis < 1:
        return "Light-tailed"
    else:
        return "Non-normal"

@api.route('/smart-recommendations', methods=['GET'])
def get_smart_recommendations():
    """Get prioritized statistical recommendations based on data characteristics."""
    try:
        if current_app.data_manager.data is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
            
        # Get column types
        numeric_cols = current_app.data_manager.data.select_dtypes(include=[np.number]).columns
        categorical_cols = current_app.data_manager.data.select_dtypes(include=['object', 'category']).columns
        boolean_cols = [col for col in current_app.data_manager.data.columns if current_app.data_manager.data[col].nunique() == 2]
        
        # For large datasets, limit analysis to most relevant columns
        MAX_COLS_PER_TYPE = 20  # Maximum number of columns to analyze per type
        
        # Select most relevant numeric columns (those with highest variance)
        if len(numeric_cols) > MAX_COLS_PER_TYPE:
            variances = current_app.data_manager.data[numeric_cols].var()
            numeric_cols = variances.nlargest(MAX_COLS_PER_TYPE).index
        
        # Select most relevant categorical columns (those with most unique values)
        if len(categorical_cols) > MAX_COLS_PER_TYPE:
            unique_counts = current_app.data_manager.data[categorical_cols].nunique()
            categorical_cols = unique_counts.nlargest(MAX_COLS_PER_TYPE).index
        
        # Get distribution insights only for selected numeric columns
        distribution_insights = ai_engine.get_distribution_insights(current_app.data_manager.data[numeric_cols])
        
        # Organize recommendations by priority and strength
        recommendations = {
            'critical_issues': [],  # Issues that must be addressed before analysis
            'high_priority': [],    # Strong recommendations based on data characteristics
            'suggested_analyses': [], # Recommended analyses based on data structure
            'data_quality': [],     # Data quality considerations
            'methodological_notes': [] # General methodological considerations
        }
        
        # Process critical issues first
        missing_data = current_app.data_manager.data.isnull().sum()
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
        n_samples = len(current_app.data_manager.data)
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
        constant_cols = [col for col in current_app.data_manager.data.columns if current_app.data_manager.data[col].nunique() == 1]
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

@api.route('/ai-recommendations', methods=['POST'])
def get_ai_recommendations():
    try:
        data = request.get_json()
        current_analysis = data.get('current_analysis')
        analysis_history = data.get('analysis_history', [])
        data_stats = data.get('data_stats')

        # Prepare context for AI
        context = {
            'current_analysis': current_analysis,
            'analysis_history': analysis_history,
            'data_stats': data_stats
        }

        # Get recommendations from AI service
        recommendations = get_ai_insights(context)

        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def get_ai_insights(context):
    """Get AI-generated insights based on the current context."""
    # This is a placeholder for the actual AI integration
    # You would implement the OpenAI API call here
    recommendations = []

    # Example recommendations based on context
    if context['current_analysis']:
        recommendations.append({
            'type': 'ai',
            'title': 'AI Suggestion',
            'message': f"Based on your current {context['current_analysis']['type']} analysis, consider these additional insights...",
            'priority': 'medium',
            'action': 'View AI insights'
        })

    if context['data_stats']:
        recommendations.append({
            'type': 'ai',
            'title': 'Data Pattern Detected',
            'message': "The AI has identified interesting patterns in your data that might be worth exploring...",
            'priority': 'high',
            'action': 'Explore patterns'
        })

    return recommendations

@api.route('/update-boundary', methods=['POST'])
def update_boundary():
    """Update the boundary for a column and return updated outlier flags."""
    try:
        if current_app.data_manager.data is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400

        data = request.json
        column_name = data.get('column')
        boundary_type = data.get('type')  # 'min' or 'max'
        new_value = float(data.get('value'))

        if column_name not in current_app.data_manager.data.columns:
            return jsonify({
                'success': False,
                'error': 'Column not found'
            }), 400

        # Get the column data
        column_data = current_app.data_manager.data[column_name]

        # Initialize or get existing flags
        if 'outlier_flags' not in current_app.data_manager.data.attrs:
            current_app.data_manager.data.attrs['outlier_flags'] = {}

        if column_name not in current_app.data_manager.data.attrs['outlier_flags']:
            current_app.data_manager.data.attrs['outlier_flags'][column_name] = {
                'min': None,
                'max': None,
                'flags': np.zeros(len(column_data), dtype=bool)
            }

        # Update the boundary
        current_app.data_manager.data.attrs['outlier_flags'][column_name][boundary_type] = new_value

        # Update the flags
        flags = current_app.data_manager.data.attrs['outlier_flags'][column_name]['flags']
        if boundary_type == 'min':
            flags |= (column_data < new_value)
        else:  # max
            flags |= (column_data > new_value)

        # Count outliers
        outlier_count = int(flags.sum())
        outlier_percentage = float((outlier_count / len(column_data)) * 100)

        return jsonify({
            'success': True,
            'outlier_count': outlier_count,
            'outlier_percentage': outlier_percentage,
            'flags': flags.tolist()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@api.route('/update-outlier-flags', methods=['POST'])
def update_outlier_flags():
    """Update outlier flags for numeric columns."""
    try:
        if current_app.data_manager.data is None:
            return jsonify({
                'success': False,
                'error': 'No data has been uploaded yet'
            }), 400
            
        # Update outlier flags
        current_app.data_manager._update_numeric_IQR_outlier_flags()
        
        return jsonify({
            'success': True,
            'message': 'Outlier flags updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating outlier flags: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/log-event', methods=['POST'])
def log_event():
    """Handle logging of user events."""
    try:
        data = request.get_json()
        event = data.get('event')
        details = data.get('details', {})
        
        # Log the event using the state logger
        current_app.data_manager._state_logger.capture_state(
            current_app.data_manager.data,
            f"user_event: {event}",
            additional_info=details
        )
        
        return jsonify({
            'success': True,
            'message': 'Event logged successfully'
        })
        
    except Exception as e:
        logger.error(f"Error logging event: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/reset', methods=['POST'])
def reset_data_manager():
    """Reset the DataManager instance."""
    try:
        if hasattr(current_app, 'data_manager'):
            current_app.data_manager.reset()
            return jsonify({
                'success': True,
                'message': 'DataManager reset successfully'
            })
        return jsonify({
            'success': False,
            'error': 'DataManager not initialized'
        }), 400
    except Exception as e:
        logger.error(f"Error resetting DataManager: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/column-suggestions', methods=['POST'])
def column_suggestions():
    try:
        data = request.get_json()
        input_text = data.get('input', '')
        
        # Get current validation state
        state = current_app.column_selector.get_current_state()
        
        # Parse the input to update the state
        current_app.column_selector.parse_column_specification(input_text)
        state = current_app.column_selector.get_current_state()
        
        # Get suggestions based on input
        suggestions = []
        if input_text:
            # Get all column names
            all_columns = current_app.data_manager.data.columns.tolist()
            # Filter columns that match the input
            suggestions = [col for col in all_columns if input_text.lower() in col.lower()]
        
        return jsonify({
            'success': True,
            'columns': state['columns'],
            'error': state['error'],
            'is_valid': state['is_valid'],
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@api.route('/add-column', methods=['POST'])
def add_column():
    try:
        data = request.get_json()
        column = data.get('column')
        
        if not column:
            return jsonify({
                'success': False,
                'error': 'No column specified'
            })
            
        # Add the column to the current set
        current_app.column_selector._current_columns.add(column)
        
        # Get the updated state
        state = current_app.column_selector.get_current_state()
        
        return jsonify({
            'success': True,
            'columns': state['columns'],
            'error': state['error'],
            'is_valid': state['is_valid']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
