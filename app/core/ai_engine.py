import pandas as pd
import re
from collections import OrderedDict
import numpy as np
import traceback
from typing import Tuple, List, Dict, Any
import warnings
from scipy import stats

# Suppress warnings
warnings.filterwarnings('ignore')

class AIEngine:
    """Manages AI recommendations and learning for statistical analyses."""
    
    def __init__(self):
        """Initialize the AI Engine with necessary imports and configurations."""
        # Ensure single initialization
        if not hasattr(self, '_initialized'):
            # Initialize core attributes
            self.analysis_history = []
            self.recommendations = {}
            
            # Import required packages
            self._import_required_packages()
            
            self._initialized = True
    
    def _import_required_packages(self):
        """Import all required packages for statistical analysis."""
        try:
            global pd, np, stats
            import pandas as pd
            import numpy as np
            from scipy import stats
        except ImportError as e:
            print(f"Error importing required packages: {str(e)}")
            raise
        
    def modify_data(self, df, modification_request):
        """
        Handle column deletion based on user specification.
        Returns tuple: (modified_dataframe, was_modified)
        """
        print("\n=== Starting Column Deletion ===")
        print(f"Original request: {modification_request}")
        print(f"Original DataFrame shape: {df.shape}")
        print(f"Original columns: {list(df.columns)}")
        
        # Store original data
        original_shape = df.shape
        was_modified = False
        
        try:
            modified_df = df.copy()
            columns_to_delete = set()
            
            # Split by commas and process each part
            parts = [p.strip() for p in modification_request.split(',')]
            for part in parts:
                # Handle numeric column specifications
                if any(c.isdigit() for c in part):
                    # Handle range format (e.g., "4-7" or "9+")
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        columns_to_delete.update(range(start-1, end))  # Convert to 0-based index
                    elif '+' in part:
                        start = int(part.replace('+', ''))
                        columns_to_delete.update(range(start-1, len(modified_df.columns)))
                    else:
                        # Single column number
                        col_num = int(part)
                        if 0 < col_num <= len(modified_df.columns):
                            columns_to_delete.add(col_num-1)  # Convert to 0-based index
                
                # Handle column name specifications
                elif any(c.isalpha() for c in part):
                    # Handle range format (e.g., "dept - time")
                    if '-' in part:
                        start_col, end_col = [c.strip() for c in part.split('-')]
                        if start_col in modified_df.columns and end_col in modified_df.columns:
                            start_idx = modified_df.columns.get_loc(start_col)
                            end_idx = modified_df.columns.get_loc(end_col)
                            columns_to_delete.update(range(start_idx, end_idx + 1))
                    else:
                        # Single column name
                        if part in modified_df.columns:
                            columns_to_delete.add(modified_df.columns.get_loc(part))
            
            # Convert column indices to names and drop columns
            if columns_to_delete:
                columns_to_drop = [modified_df.columns[i] for i in sorted(columns_to_delete)]
                print(f"Dropping columns: {columns_to_drop}")
                modified_df = modified_df.drop(columns=columns_to_drop)
                was_modified = True
            
            print(f"Final DataFrame shape: {modified_df.shape}")
            print(f"Final columns: {list(modified_df.columns)}")
            print(f"Was modified: {was_modified}")
            print("=== Column Deletion Complete ===\n")
            
            return modified_df, was_modified
            
        except Exception as e:
            print(f"Error in column deletion: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise
        
    def check_requirements_met(self, df, requirements_text):
        """Check if the dataset meets the requirements for a specific analysis."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        binary_cols = [col for col in df.columns if df[col].nunique() == 2]
        
        requirements = requirements_text.lower()
        
        # Check different requirement patterns
        if "any type of data" in requirements:
            return True
        if "one numeric variable" in requirements and len(numeric_cols) >= 1:
            return True
        if "two numeric variables" in requirements and len(numeric_cols) >= 2:
            return True
        if "multiple numeric variables" in requirements and len(numeric_cols) >= 2:
            return True
        if "three or more numeric variables" in requirements and len(numeric_cols) >= 3:
            return True
        if "one binary variable" in requirements and len(binary_cols) >= 1:
            return True
        if "one categorical variable" in requirements and len(categorical_cols) >= 1:
            return True
        if "two categorical variables" in requirements and len(categorical_cols) >= 2:
            return True
        if "one numeric variable and one binary grouping variable" in requirements:
            return len(numeric_cols) >= 1 and len(binary_cols) >= 1
        if "one binary outcome and one or more numeric predictors" in requirements:
            return len(binary_cols) >= 1 and len(numeric_cols) >= 1
        
        return False

    def get_analysis_options(self, df):
        """Get available analysis options based on data structure."""
        
        # Define all possible options
        all_options = [
            {
                'id': 'one_sample_t',
                'name': 'One Sample T-Test',
                'description': 'Test if a sample mean differs from a hypothesized value.',
                'requirements': 'One numeric variable'
            },
            {
                'id': 'one_sample_median',
                'name': 'One Sample Median Test',
                'description': 'Test if a sample median differs from a hypothesized value.',
                'requirements': 'One numeric variable'
            },
            {
                'id': 'binomial',
                'name': 'Binomial Test',
                'description': 'Test if the proportion in a binary variable differs from a hypothesized value.',
                'requirements': 'One binary variable'
            },
            {
                'id': 'chi_square',
                'name': 'Chi-Square Goodness of Fit',
                'description': 'Test if categorical variable frequencies match expected proportions.',
                'requirements': 'One categorical variable'
            },
            {
                'id': 'correlation',
                'name': 'Correlation Analysis',
                'description': 'Examine relationships between numerical variables.',
                'requirements': 'Two numeric variables'
            },
            {
                'id': 'simple_regression',
                'name': 'Simple Linear Regression',
                'description': 'Predict one numeric variable from another.',
                'requirements': 'Two numeric variables (predictor and outcome)'
            },
            {
                'id': 'multiple_regression',
                'name': 'Multiple Regression',
                'description': 'Predict a numeric outcome using multiple predictors.',
                'requirements': 'Multiple numeric variables'
            },
            {
                'id': 'ttest_independent',
                'name': 'Independent Samples T-Test',
                'description': 'Compare means between two independent groups.',
                'requirements': 'One numeric variable and one binary grouping variable'
            },
            {
                'id': 'logistic_regression',
                'name': 'Logistic Regression',
                'description': 'Predict binary outcomes using numeric predictors.',
                'requirements': 'One binary outcome and one or more numeric predictors'
            },
            {
                'id': 'chi_square_independence',
                'name': 'Chi-Square Test of Independence',
                'description': 'Test relationship between two categorical variables.',
                'requirements': 'Two categorical variables'
            },
            {
                'id': 'factor_analysis',
                'name': 'Factor Analysis',
                'description': 'Identify underlying factors in multiple numeric variables.',
                'requirements': 'Three or more numeric variables'
            },
            {
                'id': 'manova',
                'name': 'MANOVA',
                'description': 'Test effects on multiple dependent variables simultaneously.',
                'requirements': 'Multiple numeric dependent variables and categorical predictors'
            }
        ]
        
        # Check requirements and sort options
        available_options = []
        unavailable_options = []
        
        for option in all_options:
            if self.check_requirements_met(df, option['requirements']):
                option['requirements_met'] = True
                available_options.append(option)
            else:
                option['requirements_met'] = False
                unavailable_options.append(option)
        
        # Combine lists with available options first
        return available_options + unavailable_options

    def get_distribution_insights(self, df):
        """Analyze distribution characteristics of numeric columns."""
        insights = {}
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            data = df[col].dropna()
            
            # Calculate basic statistics
            mean = data.mean()
            std = data.std()
            skewness = stats.skew(data)
            kurtosis = stats.kurtosis(data)
            
            # Perform normality test (Shapiro-Wilk)
            _, p_value = stats.shapiro(data)
            is_normal = p_value > 0.05
            
            # Check for outliers using IQR method
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            outliers = data[(data < (Q1 - 1.5 * IQR)) | (data > (Q3 + 1.5 * IQR))]
            has_outliers = len(outliers) > 0
            
            # Determine distribution type
            distribution_type = "Normal" if is_normal else "Non-normal"
            if not is_normal:
                if abs(skewness) > 1:
                    distribution_type = "Skewed"
                elif abs(kurtosis) > 2:
                    distribution_type = "Heavy-tailed"
            
            # Generate recommendations based on distribution characteristics
            recommendations = []
            
            # Normality recommendations
            if not is_normal:
                recommendations.append({
                    'type': 'normality',
                    'message': f'Data is not normally distributed (p={p_value:.3f}). Consider using non-parametric tests.',
                    'suggested_tests': ['Mann-Whitney U test', 'Wilcoxon signed-rank test', 'Kruskal-Wallis test']
                })
            
            # Skewness recommendations
            if abs(skewness) > 1:
                recommendations.append({
                    'type': 'skewness',
                    'message': f'Data shows significant skewness ({skewness:.2f}). Consider data transformation.',
                    'suggested_tests': ['Log transformation', 'Square root transformation', 'Box-Cox transformation']
                })
            
            # Kurtosis recommendations
            if abs(kurtosis) > 2:
                recommendations.append({
                    'type': 'kurtosis',
                    'message': f'Data shows significant kurtosis ({kurtosis:.2f}). Consider robust statistical methods.',
                    'suggested_tests': ['Trimmed means', 'Winsorized means', 'Robust regression']
                })
            
            # Outlier recommendations
            if has_outliers:
                recommendations.append({
                    'type': 'outliers',
                    'message': f'Found {len(outliers)} outliers. Consider investigating their impact.',
                    'suggested_tests': ['Outlier analysis', 'Robust statistical methods', 'Sensitivity analysis']
                })
            
            # Store insights
            insights[col] = {
                'distribution_type': distribution_type,
                'normality': 'Normal' if is_normal else 'Non-normal',
                'skewness': f'{skewness:.2f}',
                'kurtosis': f'{kurtosis:.2f}',
                'outliers': f'{len(outliers)} outliers' if has_outliers else 'No outliers',
                'recommendations': recommendations
            }
        
        return insights

    def get_analysis_recommendations(self, df):
        """Get comprehensive analysis recommendations based on data characteristics."""
        recommendations = []
        
        # Get column types
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        boolean_cols = [col for col in df.columns if df[col].nunique() == 2]
        timeseries_cols = df.select_dtypes(include=['datetime64']).columns
        
        # Sample size recommendations
        n_samples = len(df)
        if n_samples < 30:
            recommendations.append({
                'type': 'sample_size',
                'message': 'Small sample size detected. Consider increasing sample size or using non-parametric tests.',
                'suggested_tests': ['Non-parametric tests', 'Bootstrap methods', 'Exact tests']
            })
        
        # Missing data recommendations
        missing_data = df.isnull().sum()
        if missing_data.any():
            recommendations.append({
                'type': 'missing_data',
                'message': 'Missing data detected. Consider imputation or complete case analysis.',
                'suggested_tests': ['Multiple imputation', 'Complete case analysis', 'Missing data pattern analysis']
            })
        
        # Correlation recommendations
        if len(numeric_cols) >= 2:
            recommendations.append({
                'type': 'correlation',
                'message': 'Multiple numeric variables present. Consider correlation analysis.',
                'suggested_tests': ['Pearson correlation', 'Spearman correlation', 'Correlation matrix']
            })
        
        # Categorical analysis recommendations
        if len(categorical_cols) >= 2:
            recommendations.append({
                'type': 'categorical',
                'message': 'Multiple categorical variables present. Consider contingency analysis.',
                'suggested_tests': ['Chi-square test', 'Fisher\'s exact test', 'Cramer\'s V']
            })
        
        # Binary outcome recommendations
        if len(boolean_cols) >= 1 and len(numeric_cols) >= 1:
            recommendations.append({
                'type': 'binary_outcome',
                'message': 'Binary outcome with numeric predictors detected. Consider logistic regression.',
                'suggested_tests': ['Logistic regression', 'ROC analysis', 'Classification metrics']
            })
        
        # Time series recommendations
        if len(timeseries_cols) >= 1:
            recommendations.append({
                'type': 'timeseries',
                'message': 'Time series data detected. Consider time series analysis.',
                'suggested_tests': ['Trend analysis', 'Seasonality analysis', 'Autocorrelation']
            })
        
        return recommendations
