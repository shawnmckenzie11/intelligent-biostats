import pandas as pd
import re
from collections import OrderedDict
import numpy as np

class AIEngine:
    """Manages AI recommendations and learning for statistical analyses."""
    
    def __init__(self):
        self.analysis_history = []
        self.recommendations = {}
        
    def modify_data(self, df, modification_request):
        """
        Interpret and apply data modifications based on natural language request.
        Returns tuple: (modified_dataframe, was_modified)
        """
        print("\n=== Starting Data Modification ===")
        print(f"Original request: {modification_request}")
        print(f"Original DataFrame shape: {df.shape}")
        print(f"Original columns: {list(df.columns)}")
        
        # Store original column order and data
        original_columns = list(df.columns)
        was_modified = False
        
        # Convert request to lowercase for easier parsing
        request = modification_request.lower()
        print(f"Lowercase request: {request}")
        
        try:
            modified_df = df.copy()
            original_shape = modified_df.shape
            original_columns_set = set(modified_df.columns)
            
            # Handle row modifications first
            if any(word in request for word in ['row', 'rows']):
                print("Detected row modification request")
                
                # Handle row ranges (e.g., "rows 4-9" or "rows 4 to 9")
                range_match = re.search(r'rows? (\d+)[-\s](?:to\s)?(\d+)', request)
                if range_match:
                    start_row = int(range_match.group(1)) - 1  # Convert to 0-based index
                    end_row = int(range_match.group(2))
                    print(f"Removing rows {start_row + 1} to {end_row}")
                    modified_df = pd.concat([
                        modified_df.iloc[:start_row],
                        modified_df.iloc[end_row:]
                    ]).reset_index(drop=True)
                
                # Handle "every second/other row"
                elif any(phrase in request for phrase in ['every second', 'every 2nd', 'every other']):
                    print("Attempting to keep every second row")
                    modified_df = modified_df.iloc[::2].copy()
                    print(f"After row modification - Shape: {modified_df.shape}")
                
                # Handle "rows after X"
                elif 'after' in request:
                    match = re.search(r'rows? after (\d+)', request)
                    if match:
                        start_row = int(match.group(1))
                        print(f"Removing rows after {start_row}")
                        modified_df = modified_df.iloc[:start_row].copy()
            
            # Handle column modifications
            if 'after column' in request or 'columns after' in request:
                print("Detected 'after column' request")
                match = re.search(r'(?:after )?columns? (\d+)\+?', request) or re.search(r'(?:after )?columns? (\d+)', request)
                if match:
                    col_num = int(match.group(1))
                    print(f"Found column number: {col_num}")
                    if col_num < len(modified_df.columns):
                        columns_to_drop = modified_df.columns[col_num:]
                        print(f"Dropping columns: {list(columns_to_drop)}")
                        modified_df = modified_df.drop(columns=columns_to_drop)
            
            # Handle column range deletion
            elif re.search(r'columns? \d+[-\s](?:to\s)?\d+', request):
                print("Detected column range request")
                range_match = re.search(r'columns? (\d+)[-\s](?:to\s)?(\d+)', request)
                if range_match:
                    start_col = int(range_match.group(1)) - 1
                    end_col = int(range_match.group(2))
                    if start_col < len(modified_df.columns):
                        columns_to_drop = modified_df.columns[start_col:end_col]
                        print(f"Dropping columns: {list(columns_to_drop)}")
                        modified_df = modified_df.drop(columns=columns_to_drop)
            
            # Handle specific column deletion
            elif any(word in request for word in ['column', 'columns']):
                print("Detected column deletion request")
                # Try exact column names first
                for column in original_columns:
                    if column.lower() in request:
                        print(f"Found exact column match: {column}")
                        modified_df = modified_df.drop(columns=[column])
                
                # Try numeric column reference
                match = re.search(r'column (\d+)', request)
                if match:
                    col_num = int(match.group(1)) - 1  # Convert to 0-based index
                    print(f"Found column number: {col_num + 1}")
                    if 0 <= col_num < len(modified_df.columns):
                        col_name = modified_df.columns[col_num]
                        print(f"Dropping column {col_num + 1}: {col_name}")
                        modified_df = modified_df.drop(columns=[col_name])
            
            # Check if any modifications were actually made
            was_modified = (
                modified_df.shape != original_shape or 
                set(modified_df.columns) != original_columns_set or
                not modified_df.equals(df)
            )
            
            print(f"Final DataFrame shape: {modified_df.shape}")
            print(f"Final columns: {list(modified_df.columns)}")
            print(f"Was modified: {was_modified}")
            print("=== Modification Complete ===\n")
            
            return modified_df, was_modified
            
        except Exception as e:
            print(f"Error in modify_data: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
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
                'id': 'descriptive',
                'name': 'Descriptive Statistics',
                'description': 'Basic statistical measures including mean, median, and standard deviation.',
                'requirements': 'Any type of data'
            },
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
