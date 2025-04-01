import pandas as pd
import os
import numpy as np
from datetime import datetime

class EnhancedDataFrame:
    """Enhanced Pandas DataFrame with metadata for biostatistical analysis."""
    
    def __init__(self):
        self.data = None
        self.metadata = {}
        
    def load_data(self, file_path):
        """Load data and compute basic statistics."""
        self.data = pd.read_csv(file_path)
        self.metadata = {
            'file_stats': {
                'filename': os.path.basename(file_path),
                'filesize': f"{os.path.getsize(file_path) / (1024*1024):.2f} MB",
                'rows': len(self.data),
                'columns': len(self.data.columns)
            },
            'column_types': self._analyze_column_types()
        }
    
    def _analyze_column_types(self):
        """Analyze and categorize columns."""
        if self.data is None:
            return {}
            
        stats = {
            'numeric': [],
            'boolean': [],
            'categorical': [],
            'timeseries': [],
            'discrete': []
        }
        
        for col in self.data.columns:
            # Check if numeric
            if pd.api.types.is_numeric_dtype(self.data[col]):
                stats['numeric'].append(col)
                # Check if discrete
                if self.data[col].nunique() < 20:  # threshold for discrete
                    stats['discrete'].append(col)
            
            # Check if boolean
            elif self.data[col].nunique() == 2:
                stats['boolean'].append(col)
            
            # Check if potential datetime
            elif self._is_datetime(self.data[col]):
                stats['timeseries'].append(col)
            
            # Remaining are categorical
            else:
                stats['categorical'].append(col)
        
        return {
            'numeric_count': len(stats['numeric']),
            'boolean_count': len(stats['boolean']),
            'categorical_count': len(stats['categorical']),
            'timeseries_count': len(stats['timeseries']),
            'discrete_count': len(stats['discrete']),
            'columns': stats
        }
    
    def _is_datetime(self, series):
        """Check if a series contains datetime values."""
        try:
            pd.to_datetime(series)
            return True
        except:
            return False
    
    def add_metadata(self, key, value):
        """Add metadata information."""
        self.metadata[key] = value
