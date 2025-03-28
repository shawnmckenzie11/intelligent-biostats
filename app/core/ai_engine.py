import pandas as pd
import re
from collections import OrderedDict

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
        
    def get_analysis_options(self, df):
        """Get available analysis options based on data structure."""
        options = [
            {
                'id': 'descriptive',
                'name': 'Descriptive Statistics',
                'description': 'Basic statistical measures including mean, median, and standard deviation.'
            },
            {
                'id': 'ttest',
                'name': 'T-Test Analysis',
                'description': 'Compare means between two groups.'
            },
            {
                'id': 'correlation',
                'name': 'Correlation Analysis',
                'description': 'Examine relationships between numerical variables.'
            }
        ]
        
        return options
