import pandas as pd

class EnhancedDataFrame:
    """Enhanced Pandas DataFrame with metadata for biostatistical analysis."""
    
    def __init__(self):
        self.data = None
        self.metadata = {}
        
    def load_data(self, file_path):
        """Load data from CSV file."""
        self.data = pd.read_csv(file_path)
        
    def add_metadata(self, key, value):
        """Add metadata information."""
        self.metadata[key] = value
