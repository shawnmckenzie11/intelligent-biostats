"""
Data Manager Module

This module provides enhanced data management capabilities for biostatistical analysis.
It extends pandas DataFrame functionality with metadata tracking and advanced data
manipulation features.

Key Features:
- Enhanced DataFrame with metadata
- Automatic data type detection
- Data modification tracking
- Column-specific analysis
"""

import pandas as pd
import os
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, Union

class EnhancedDataFrame:
    """
    Enhanced Pandas DataFrame with metadata for biostatistical analysis.
    
    This class extends pandas DataFrame functionality by adding metadata tracking
    and advanced data manipulation features. It maintains information about the
    data's structure, types, and modifications.
    
    Attributes:
        data (pd.DataFrame): The underlying pandas DataFrame
        metadata (dict): Dictionary containing metadata about the data
    """
    
    def __init__(self):
        """
        Initialize an empty EnhancedDataFrame.
        
        Creates a new instance with no data and empty metadata.
        """
        self.data = None
        self.metadata = {}
        
    def load_data(self, file_path: str) -> None:
        """
        Load data from a file and compute basic statistics.
        
        Args:
            file_path (str): Path to the data file
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file format is not supported
        """
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
    
    def _analyze_column_types(self) -> Dict[str, int]:
        """
        Analyze and categorize columns, returning column types and counts.
        
        Returns:
            Dict[str, int]: Dictionary mapping column types to their counts
            
        Note:
            Column types include: numeric, boolean, categorical, timeseries, discrete
        """
        if self.data is None:
            return {}
            
        # Initialize tracking dicts
        column_types_list = []  # List of types in same order as columns
        type_counts = {    # Counts of each type
            'numeric': 0,
            'boolean': 0, 
            'categorical': 0,
            'timeseries': 0,
            'discrete': 0
        }
        
        for col in self.data.columns:
            col_type = None
            # Check if numeric
            if pd.api.types.is_numeric_dtype(self.data[col]):
                col_type = 'numeric'
                type_counts['numeric'] += 1
                
                # Check if discrete
                if self.data[col].nunique() < 20:  # threshold for discrete
                    col_type = 'discrete'
                    type_counts['discrete'] += 1
                    type_counts['numeric'] -= 1  # Adjust count since it's discrete
            
            # Check if boolean
            elif self.data[col].nunique() == 2:
                col_type = 'boolean'
                type_counts['boolean'] += 1
            
            # Check if potential datetime
            elif self._is_datetime(self.data[col]):
                col_type = 'timeseries'
                type_counts['timeseries'] += 1
            
            # Remaining are categorical
            else:
                col_type = 'categorical'
                type_counts['categorical'] += 1
            
            column_types_list.append(col_type)
        
        return {
            'column_types_list': column_types_list,  # List of types in column order
            'type_counts': type_counts,              # Count of each type
            'total_columns': len(self.data.columns)
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

    def modify_data(self, modification_request):
        """Apply modifications to the data and update metadata."""
        if self.data is None:
            return False, "No data loaded"
            
        try:
            # Store original state
            original_data = self.data.copy()
            
            # Apply modifications using the AI engine
            from .ai_engine import AIEngine
            ai_engine = AIEngine()
            modified_df, was_modified = ai_engine.modify_data(self.data, modification_request)
            
            if was_modified:
                # Update the data
                self.data = modified_df
                
                # Update metadata
                self.metadata['file_stats'].update({
                    'rows': len(self.data),
                    'columns': len(self.data.columns)
                })
                
                # Re-analyze column types
                self.metadata['column_types'] = self._analyze_column_types()
                
                # Add modification history
                if 'modification_history' not in self.metadata:
                    self.metadata['modification_history'] = []
                self.metadata['modification_history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'request': modification_request,
                    'changes': {
                        'rows': len(self.data) - len(original_data),
                        'columns': len(self.data.columns) - len(original_data.columns)
                    }
                })
                
                return True, "Modifications applied successfully"
            else:
                return False, "No modifications were made"
                
        except Exception as e:
            return False, f"Error applying modifications: {str(e)}"

    def get_column_data(self, column_name):
        """Get data and statistics for a specific column."""
        if self.data is None or column_name not in self.data.columns:
            return None, "Column not found"
            
        try:
            column_data = self.data[column_name]
            column_type = self.metadata['column_types']['column_types_list'][list(self.data.columns).index(column_name)]
            
            # Get basic statistics based on column type
            stats = {
                'Type': column_type,
                'Missing Values': str(column_data.isna().sum()),
                'Unique Values': str(column_data.nunique())
            }
            
            # Add type-specific statistics
            if column_type == 'numeric' or column_type == 'discrete':
                stats.update({
                    'Mean': f"{column_data.mean():.2f}",
                    'Median': f"{column_data.median():.2f}",
                    'Std Dev': f"{column_data.std():.2f}",
                    'Min': f"{column_data.min():.2f}",
                    'Max': f"{column_data.max():.2f}"
                })
            elif column_type == 'categorical':
                value_counts = column_data.value_counts()
                stats['Most Common'] = f"{value_counts.index[0]} ({value_counts.iloc[0]} times)"
                stats['Value Distribution'] = value_counts.head(5).to_dict()
            elif column_type == 'boolean':
                value_counts = column_data.value_counts()
                stats['True Count'] = str(value_counts.get(True, 0))
                stats['False Count'] = str(value_counts.get(False, 0))
            elif column_type == 'timeseries':
                stats.update({
                    'Start Date': str(column_data.min()),
                    'End Date': str(column_data.max()),
                    'Date Range': f"{column_data.max() - column_data.min()}"
                })
            
            # Get sample data (first 10 rows)
            sample_data = column_data.head(10).tolist()
            
            return {
                'stats': stats,
                'sample_data': sample_data
            }, None
            
        except Exception as e:
            return None, f"Error getting column data: {str(e)}"
