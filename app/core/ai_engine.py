import pandas as pd
import re

class AIEngine:
    """Manages AI recommendations and learning for statistical analyses."""
    
    def __init__(self):
        self.analysis_history = []
        self.recommendations = {}
        
    def modify_data(self, df, modification_request):
        """
        Interpret and apply data modifications based on natural language request.
        """
        print(f"Processing modification request: {modification_request}")
        
        # Convert request to lowercase for easier parsing
        request = modification_request.lower()
        
        try:
            # Handle different types of modifications
            if 'remove' in request or 'delete' in request:
                if 'column' in request:
                    df = self._handle_column_deletion(df, request)
                elif 'row' in request or 'rows' in request:
                    df = self._handle_row_deletion(df, request)
                    
            print(f"Modified DataFrame shape: {df.shape}")
            return df
            
        except Exception as e:
            print(f"Error in modify_data: {str(e)}")
            raise
            
    def _handle_column_deletion(self, df, request):
        """Handle requests to delete columns."""
        # Extract column names from the request
        columns = df.columns.tolist()
        
        for column in columns:
            if column.lower() in request:
                df = df.drop(columns=[column])
                print(f"Dropped column: {column}")
                
        return df
        
    def _handle_row_deletion(self, df, request):
        """Handle requests to delete rows."""
        if 'every second row' in request or 'every 2nd row' in request:
            df = df.iloc[::2].copy()
            print("Kept every second row")
        elif 'first' in request:
            match = re.search(r'first (\d+)', request)
            if match:
                num = int(match.group(1))
                df = df.iloc[num:].copy()
                print(f"Dropped first {num} rows")
        elif 'last' in request:
            match = re.search(r'last (\d+)', request)
            if match:
                num = int(match.group(1))
                df = df.iloc[:-num].copy()
                print(f"Dropped last {num} rows")
                
        return df
        
    def get_analysis_options(self, df):
        """Get available analysis options based on data structure."""
        print("Generating analysis options")
        
        # Example analysis options
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
