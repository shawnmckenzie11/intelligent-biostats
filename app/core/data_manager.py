import sys
import platform

from typing import Dict, List, Optional, Union, Any, Tuple
import pandas as pd
import os
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging
from app.utils.state_logger import StateLogger
from scipy import stats
from app.core.enums import DataPointFlag
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

logger = logging.getLogger(__name__)

class ColumnType(Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    TIMESERIES = "timeseries"
    DISCRETE = "discrete"
    ORDINAL = "ordinal"
    CENSORED = "censored"

class DataManager:
    """
    Enhanced Pandas DataFrame with metadata for biostatistical analysis.
    
    This class extends pandas DataFrame functionality by adding metadata tracking
    and advanced data manipulation features. It maintains information about the
    data's structure, types, and modifications.
    
    Attributes:
        data (pd.DataFrame): The underlying pandas DataFrame
        current_file (str): Name of the currently loaded file
        modifications_history (List[Dict[str, Any]]): History of modifications made to the data
        validation_rules (Dict[str, List[Dict[str, Any]]]): Rules for data validation
        cached_statistics (Dict[str, Any]): Cache for computed statistics
        point_flags (np.ndarray): Array of flags for each data point
        _descriptive_stats (Dict[str, Any]): Cache for descriptive statistics
    """
    
    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.current_file: Optional[str] = None
        self.modifications_history: List[Dict[str, Any]] = []
        self.validation_rules: Dict[str, List[Dict[str, Any]]] = {}
        self.cached_statistics: Dict[str, Any] = {}
        self._state_logger = StateLogger()
        self.point_flags: Optional[np.ndarray] = None  # Will be (n_rows, n_cols) array of DataPointFlag
        self._descriptive_stats: Optional[Dict[str, Any]] = None  # Cache for descriptive statistics
        
    def reset(self) -> None:
        """Reset the DataManager to its initial state."""
        self.data = None
        self.current_file = None
        self.modifications_history = []
        self.validation_rules = {}
        self.cached_statistics = {}
        self._state_logger = StateLogger()
        self.point_flags = None
        self._descriptive_stats = None  # Reset descriptive stats cache
        
    def load_data(self, file_path: Optional[str] = None, file_obj: Optional[Any] = None) -> Tuple[bool, Optional[str]]:
        """Load data from file path or file object and compute basic statistics."""
        try:
            # Reset state before loading new data
            self.reset()
            
            # Always create a new StateLogger instance for each load
            self._state_logger = StateLogger()
            
            if file_obj is not None:
                # Reset file pointer to beginning
                file_obj.seek(0)
                # Read the file content
                content = file_obj.read().decode('utf-8')
                # Create a StringIO object from the content
                from io import StringIO
                string_buffer = StringIO(content)
                # Read the CSV data
                self.data = pd.read_csv(string_buffer)
                self.current_file = file_obj.filename
            elif file_path is not None:
                self.data = pd.read_csv(file_path)
                self.current_file = os.path.basename(file_path)
            else:
                raise ValueError("Either file_path or file_obj must be provided")
                
            # Validate that data was loaded successfully
            if self.data is None or self.data.empty:
                raise ValueError("Failed to load data or file is empty")
                
            self.modifications_history = []
            self._initialize_point_flags()
            
            # Calculate descriptive statistics after loading data
            self.calculate_descriptive_stats()
            
            # Create a new log file for this CSV load
            if self.current_file:
                self._state_logger.on_csv_load(self.current_file)
            
            # Log state after all initialization is complete
            self._state_logger.capture_state(self, "load_data")
            return True, None
            
        except pd.errors.EmptyDataError:
            error_msg = "The file appears to be empty"
            logger.error(error_msg)
            self._state_logger.capture_state(None, f"load_error: {error_msg}")
            return False, error_msg
        except pd.errors.ParserError as e:
            error_msg = f"Error parsing CSV file: {str(e)}"
            logger.error(error_msg)
            self._state_logger.capture_state(None, f"load_error: {error_msg}")
            return False, error_msg
        except UnicodeDecodeError:
            error_msg = "Error decoding file - please ensure it's a valid UTF-8 encoded CSV"
            logger.error(error_msg)
            self._state_logger.capture_state(None, f"load_error: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error loading data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._state_logger.capture_state(None, f"load_error: {error_msg}")
            return False, error_msg
    
    def _determine_column_type(self, series: pd.Series) -> ColumnType:
        """Determine the most appropriate column type."""
        if pd.api.types.is_numeric_dtype(series):
            if series.nunique() < 20:
                return ColumnType.DISCRETE
            return ColumnType.NUMERIC
        elif pd.api.types.is_datetime64_any_dtype(series):
            return ColumnType.TIMESERIES
        elif series.nunique() == 2:
            return ColumnType.BOOLEAN
        elif self._is_ordinal(series):
            return ColumnType.ORDINAL
        elif self._is_censored(series):
            return ColumnType.CENSORED
        return ColumnType.CATEGORICAL
    
    def _is_ordinal(self, series: pd.Series) -> bool:
        """Check if a series contains ordinal data."""
        # Implementation for ordinal detection
        return False
    
    def _is_censored(self, series: pd.Series) -> bool:
        """Check if a series contains censored data."""
        # Implementation for censored data detection
        return False
    
    def _get_validation_rules(self, column: str, col_type: ColumnType) -> Dict[str, Any]:
        """Get validation rules for a column based on its type."""
        rules = {
            'required': True,
            'missing_allowed': True
        }
        
        if col_type == ColumnType.NUMERIC:
            rules.update({
                'min_value': self.data[column].min(),
                'max_value': self.data[column].max(),
                'allow_negative': True
            })
        elif col_type == ColumnType.CATEGORICAL:
            rules.update({
                'allowed_values': self.data[column].unique().tolist()
            })
            
        return rules
    
    def _calculate_statistical_properties(self, column: str, col_type: ColumnType, ignore_flags: bool = False) -> Dict[str, Any]:
        """Calculate statistical properties for a column."""
        properties = {}
        
        if col_type in [ColumnType.NUMERIC, ColumnType.DISCRETE]:
            series = self.data[column]
            properties.update({
                'mean': float(series.mean()),
                'median': float(series.median()),
                'std': float(series.std()),
                'skewness': float(series.skew()),
                'kurtosis': float(series.kurtosis()),
                'distribution_type': self._determine_distribution(series)
            })
            
        return properties
    
    def _determine_distribution(self, series: pd.Series) -> str:
        """Determine the type of distribution for a numeric series."""
        if len(series) < 30:
            return "Insufficient data"
            
        skewness = series.skew()
        kurtosis = series.kurtosis()
            
        # Test for normality using skewness and kurtosis
        if abs(skewness) < 0.5 and abs(kurtosis - 3) < 0.5:
            return "Normal"
        elif skewness > 1:
            return "Right-skewed"
        elif skewness < -1:
            return "Left-skewed"
        elif kurtosis > 4:
            return "Heavy-tailed"
        elif kurtosis < 2:
            return "Light-tailed"
        else:
            return "Non-normal"
    
    def _validate_data(self) -> Dict[str, Any]:
        """Validate the data against defined rules and return validation results."""
        if self.data is None:
            return {}
        
        validation_results = {
            'errors': [],
            'warnings': [],
            'passed': True
        }
        
        # Get descriptive stats
        stats = self.get_column_descriptive_stats()
        if stats is None:
            return validation_results
            
        for col in self.data.columns:
            col_type = stats['column_types']['column_types_list'][self.data.columns.get_loc(col)]
            
            # Check missing values
            if col in stats['missing_values_by_column']:
                validation_results['warnings'].append(f"Column {col} has {stats['missing_values_by_column'][col]} missing values")
            
            # Type-specific validation
            if col_type == 'numeric':
                self._validate_numeric_column(col, validation_results)
            elif col_type == 'categorical':
                self._validate_categorical_column(col, validation_results)
                
        return validation_results
    
    def _validate_numeric_column(self, column: str, results: Dict[str, Any]) -> None:
        """Validate a numeric column."""
        series = self.data[column]
        
        # Check for negative values if not allowed
        if not self.validation_rules.get(column, {}).get('allow_negative', True) and (series < 0).any():
            results['errors'].append(f"Column {column} has negative values but they are not allowed")
            
        # Check for values outside allowed range
        rules = self.validation_rules.get(column, {})
        if 'min_value' in rules and series.min() < rules['min_value']:
            results['errors'].append(f"Column {column} has values below minimum allowed")
        if 'max_value' in rules and series.max() > rules['max_value']:
            results['errors'].append(f"Column {column} has values above maximum allowed")
    
    def _validate_categorical_column(self, column: str, results: Dict[str, Any]) -> None:
        """Validate a categorical column."""
        series = self.data[column]
        rules = self.validation_rules.get(column, {})
        
        if 'allowed_values' in rules:
            invalid_values = series[~series.isin(rules['allowed_values'])].unique()
            if len(invalid_values) > 0:
                results['errors'].append(f"Column {column} has invalid values: {invalid_values}")
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Assess overall data quality."""
        if self.data is None:
            return {}
        
        quality_metrics = {
            'completeness': self._calculate_completeness(),
            'consistency': self._check_consistency(),
            'accuracy': self._assess_accuracy()
        }
        
        return quality_metrics
    
    def _calculate_completeness(self) -> float:
        """Calculate data completeness score."""
        if self.data is None:
            return 0.0
        return 1 - (self.data.isna().sum().sum() / (self.data.shape[0] * self.data.shape[1]))
    
    def _check_consistency(self) -> Dict[str, Any]:
        """Check data consistency."""
        consistency_issues = []
        
        # Check for duplicate rows
        duplicates = self.data.duplicated().sum()
        if duplicates > 0:
            consistency_issues.append(f"Found {duplicates} duplicate rows")
            
        # Check for inconsistent data types
        for col in self.data.columns:
            if self.data[col].dtype == 'object':
                try:
                    pd.to_numeric(self.data[col])
                    consistency_issues.append(f"Column {col} contains numeric values stored as strings")
                except:
                    pass
                    
        return {
            'issues': consistency_issues,
            'score': 1 - (len(consistency_issues) / len(self.data.columns))
        }
    
    def _assess_accuracy(self) -> Dict[str, Any]:
        """Assess data accuracy and identify potential issues."""
        return {
            'suspicious_values': self._find_suspicious_values(),
            'validation_errors': self._validate_data()
        }

    def _find_suspicious_values(self) -> Dict[str, Any]:
        """Identify potentially suspicious or anomalous values in the dataset."""
        suspicious_values = {}
        
        for col in self.data.columns:
            if pd.api.types.is_numeric_dtype(self.data[col]):
                # Calculate basic statistics
                mean = self.data[col].mean()
                std = self.data[col].std()
                q1 = self.data[col].quantile(0.25)
                q3 = self.data[col].quantile(0.75)
                iqr = q3 - q1
                
                # Define thresholds for suspicious values
                lower_threshold = q1 - 3 * iqr
                upper_threshold = q3 + 3 * iqr
                
                # Find values outside thresholds
                suspicious = self.data[col][(self.data[col] < lower_threshold) | (self.data[col] > upper_threshold)]
                if not suspicious.empty:
                    suspicious_values[col] = {
                        'count': len(suspicious),
                        'values': suspicious.tolist(),
                        'indices': suspicious.index.tolist()
                    }
        
        return suspicious_values
   
    def _detect_outliers(self) -> Dict[str, Any]:
        """Detect outliers in numeric columns using the IQR method.
        Returns:
            Dict mapping column names to outlier statistics:
            - count: Number of outliers detected
            - percentage: Percentage of values that are outliers
        """
        outliers = {}
        
        for col, metadata in self.column_metadata.items():
            if metadata.type in [ColumnType.NUMERIC, ColumnType.DISCRETE]:
                series = self.data[col]
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outlier_count = ((series < lower_bound) | (series > upper_bound)).sum()
                if outlier_count > 0:
                    outliers[col] = {
                        'count': int(outlier_count),
                        'percentage': float(outlier_count / len(series) * 100)
                    }
                    
        return outliers
    
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


    def get_column_data(self, column_name):
        """Get data and statistics for a specific column.
        
        Args:
            column_name (str): Name of the column to get data for
            
        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[str]]: Tuple containing:
                - Dictionary with column data and statistics if successful
                - Error message if unsuccessful
        """
        if self.data is None or column_name not in self.data.columns:
            return None, "Column not found"
            
        try:
            # Get descriptive stats
            stats = self.get_column_descriptive_stats()
            if stats is None:
                self.calculate_descriptive_stats()
                stats = self.get_column_descriptive_stats()
                
            if stats is None:
                return None, "Failed to calculate descriptive statistics"
                
            # Get column type
            col_idx = self.data.columns.get_loc(column_name)
            col_type = stats['column_types']['column_types_list'][col_idx]
            
            # Build basic statistics
            column_stats = {
                'Type': col_type,
                'Missing Values': str(stats['missing_values_by_column'].get(column_name, 0)),
                'Unique Values': str(self.data[column_name].nunique())
            }
            
            # Add type-specific statistics
            if col_type in ['numeric', 'discrete']:
                if column_name in stats['distribution_analysis']:
                    dist_stats = stats['distribution_analysis'][column_name]
                    column_stats.update({
                        'Mean': f"{dist_stats['descriptive_stats']['mean']:.2f}",
                        'Median': f"{dist_stats['descriptive_stats']['mean']:.2f}",
                        'Std Dev': f"{dist_stats['descriptive_stats']['std']:.2f}",
                        'Min': f"{dist_stats['descriptive_stats']['min']:.2f}",
                        'Max': f"{dist_stats['descriptive_stats']['max']:.2f}",
                        'Skewness': f"{dist_stats['skewness']:.2f}",
                        'Kurtosis': f"{dist_stats['kurtosis']:.2f}",
                        'Distribution': dist_stats['distribution_type']
                    })
                    
                if column_name in stats['outlier_info']:
                    column_stats['Outliers'] = {
                        'count': stats['outlier_info'][column_name]['count'],
                        'percentage': f"{stats['outlier_info'][column_name]['percentage']:.2f}%"
                    }
                    
            elif col_type == 'categorical':
                if column_name in stats['categorical_stats']:
                    cat_stats = stats['categorical_stats'][column_name]
                    column_stats.update({
                        'Most Common': f"{cat_stats['most_frequent']['value']} ({cat_stats['most_frequent']['count']} times)",
                        'Value Distribution': {
                            str(item['value']): item['count'] 
                            for item in cat_stats['value_distribution'][:5]
                        }
                    })
                    
            elif col_type == 'boolean':
                if column_name in stats['boolean_stats']:
                    bool_stats = stats['boolean_stats'][column_name]
                    column_stats.update({
                        'True Count': str(bool_stats['true_count']),
                        'False Count': str(bool_stats['false_count']),
                        'True Percentage': f"{bool_stats['true_percentage']:.2f}%"
                    })
                    
            elif col_type == 'timeseries':
                if column_name in stats['datetime_stats']:
                    time_stats = stats['datetime_stats'][column_name]
                    column_stats.update({
                        'Start Date': time_stats['start_date'],
                        'End Date': time_stats['end_date'],
                        'Date Range': time_stats['range'],
                        'Time Interval': time_stats['time_interval']
                    })
            
            # Get sample data (first 10 rows)
            sample_data = self.data[column_name].head(10).tolist()
            
            return {
                'stats': column_stats,
                'sample_data': sample_data
            }, None
            
        except Exception as e:
            return None, f"Error getting column data: {str(e)}"
            
    def get_data_preview(self):
        """Get a preview of the current data."""
        if self.data is None:
            return None
            
        preview_dict = {}
        preview_df = self.data.head()
        # Use the DataFrame's columns in their original order
        for column in self.data.columns:
            preview_dict[str(column)] = [
                None if pd.isna(x) else x 
                for x in preview_df[column].tolist()
            ]
        return {
            'data': preview_dict,
            'column_order': self.data.columns.tolist()
        }

    def _initialize_point_flags(self) -> None:
        """Initialize point flags array with NORMAL values."""
        if self.data is None:
            return
        self.point_flags = np.full(self.data.shape, DataPointFlag.NORMAL, dtype=object)
        
        # Log initial state with flag counts
        self._state_logger.capture_state(self, "initialize_flags", {
            "flag_counts": {
                col: {
                    flag.value: 0 for flag in DataPointFlag
                } for col in self.data.columns
            }
        })

    def _update_point_flags(self) -> None:
        """Update flags for all data points based on data validation."""
        if self.data is None:
            return
            
        # Update flags based on data values
        for col_idx, col in enumerate(self.data.columns):
            self._update_missing_and_unexpected_flags(col_idx, col)
            
            
    def _update_missing_and_unexpected_flags(self, col_idx: int, col: str) -> None:
        """Update flags for missing and unexpected type values in a column."""
        col_data = self.data[col]
        
        # Check for missing values
        missing_mask = col_data.isna()
        self.point_flags[missing_mask, col_idx] = DataPointFlag.MISSING
        
        # Check for unexpected types in numeric columns
        if pd.api.types.is_numeric_dtype(col_data):
            # For numeric columns, check for non-numeric strings
            non_numeric_mask = col_data.astype(str).str.match(r'[^0-9.-]') & ~missing_mask
            self.point_flags[non_numeric_mask, col_idx] = DataPointFlag.UNEXPECTED_TYPE
            
    def _update_numeric_IQR_outlier_flags(self) -> None:
        """Update flags for outlier values in numeric columns."""
        try:
            if self.data is None:
                logger.error("Cannot update outlier flags: no data loaded")
                return
                
            # Initialize point flags if not already done
            if self.point_flags is None:
                self._initialize_point_flags()
                
            for col_idx, col in enumerate(self.data.columns):
                col_data = self.data[col]
                
                # Only check outliers for numeric columns with non-missing values
                if pd.api.types.is_numeric_dtype(col_data) and len(col_data.dropna()) > 0:
                    q1 = col_data.quantile(0.25)
                    q3 = col_data.quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    missing_mask = col_data.isna()
                    outlier_mask = ((col_data < lower_bound) | (col_data > upper_bound)) & ~missing_mask
                    self.point_flags[outlier_mask, col_idx] = DataPointFlag.OUTLIER
            
            # Log state with updated flag counts
            self._state_logger.capture_state(self, "update_outlier_flags", {
                "flag_counts": {
                    col: {
                        flag.value: int(np.sum(self.point_flags[:, idx] == flag))
                        for flag in DataPointFlag
                    }
                    for idx, col in enumerate(self.data.columns)
                }
            })
            
        except Exception as e:
            logger.error(f"Error updating outlier flags: {str(e)}", exc_info=True)
            raise
    
    def get_point_flags(self, row_idx: int, col_idx: int) -> DataPointFlag:
        """Get the flag for a specific data point."""
        if self.point_flags is None:
            return DataPointFlag.NORMAL
        return self.point_flags[row_idx, col_idx]
        
    def get_column_flags(self, col_idx: int) -> np.ndarray:
        """Get flags for all points in a column."""
        if self.point_flags is None:
            return np.array([])
        return self.point_flags[:, col_idx]
        
    def get_row_flags(self, row_idx: int) -> np.ndarray:
        """Get flags for a specific row."""
        if self.point_flags is None:
            return np.array([])
        return self.point_flags[row_idx, :]

    
    def delete_row(self, row_index: int) -> Tuple[bool, Optional[str]]:
        """Delete a row from the DataFrame and update metadata."""
        try:
            if self.data is None:
                return False, "No data loaded"
                
            if row_index < 0 or row_index >= len(self.data):
                return False, f"Row index {row_index} out of bounds"
                
            # Delete the row
            self.data = self.data.drop(index=row_index)
            
            # Update all metadata recursively
            self._update_metadata()
            
            return True, None
        except Exception as e:
            logger.error(f"Error deleting row: {str(e)}")
            return False, str(e)
        
    def get_columns_by_type(self, dtypes: List[str]) -> List[str]:
        """Get column names that match the specified data types.
        
        Args:
            dtypes: List of data type strings to match (e.g. ['int64', 'float64'])
            
        Returns:
            List of column names with matching data types
        """
        if self.data is None:
            return []
            
        matching_cols = []
        for col in self.data.columns:
            if self.data[col].dtype.name in dtypes:
                matching_cols.append(col)
                
        return matching_cols

    def delete_columns(self, column_to_delete: List[str]) -> Tuple[bool, str, Dict[str, Any]]:
        """Process column deletion requests directly.
        
        Args:
            column_to_delete: List[str] - The names of the columns to delete
        Returns:
            tuple: (success, message, preview)
        """
        try:             
            # Convert any numeric indices to column names
            column_to_delete = [
                self.data.columns[col] if isinstance(col, int) else col 
                for col in column_to_delete
            ]
                
            # Validate columns exist
            missing_cols = [col for col in column_to_delete if col not in self.data.columns]
            if missing_cols:
                return False, f"Columns not found: {', '.join(missing_cols)}", None
                
            # Get the original column order
            original_columns = self.data.columns.tolist()
            # Remove the columns to delete from the original order
            remaining_columns = [col for col in original_columns if col not in column_to_delete]
            # Drop columns and reorder to maintain original order using reindex
            self.data = self.data.drop(columns=column_to_delete)
            self.data = self.data.reindex(columns=remaining_columns)
            
            # Update descriptive stats
            self.update_descriptive_stats()
            
            # Get preview
            preview = self.get_data_preview()
            
            return True, f"Successfully deleted columns: {', '.join(column_to_delete)}", preview
            
        except Exception as e:
            logger.error(f"Error deleting columns: {str(e)}", exc_info=True)
            return False, str(e), None

    def get_file_statistics(self) -> Dict[str, Any]:
        """Get basic file statistics about the dataset.
        
        Returns:
            Dict containing:
            - rows: Number of rows in dataset
            - columns: Number of columns in dataset 
            - memory_usage: Memory usage in MB
            - missing_values: Total count of missing values
        """
        if self.data is None:
            return None
            
        # Calculate total missing values across all columns
        missing_values = self.data.isna().sum().sum()
        
        return {
            'rows': len(self.data),
            'columns': len(self.data.columns),
            'memory_usage': f"{self.data.memory_usage(deep=True).sum() / (1024*1024):.2f} MB",
            'missing_values': int(missing_values)
        }

    def calculate_descriptive_stats(self) -> None:
        """Calculate and store descriptive statistics for all columns in the dataset."""
        if self.data is None:
            return
            
        # Initialize tracking variables
        column_types_list = []
        missing_values_by_column = {}
        distribution_analysis = {}
        outlier_info = {}
        categorical_stats = {}
        boolean_stats = {}
        datetime_stats = {}
        
        # Add file stats that were previously in metadata
        file_stats = {
            'filename': self.current_file,
            'rows': len(self.data),
            'columns': len(self.data.columns),
            'memory_usage': f"{self.data.memory_usage(deep=True).sum() / (1024*1024):.2f} MB",
            'missing_values': int(self.data.isna().sum().sum())
        }
        
        # Add data quality metrics
        quality_metrics = {
            'completeness': self._calculate_completeness(),
            'consistency': self._check_consistency(),
            'accuracy': self._assess_accuracy()
        }
        
        for i, col in enumerate(self.data.columns):
            try:
                col_data = self.data[col]
                
                if pd.api.types.is_numeric_dtype(col_data):
                    if col_data.nunique() < 20:
                        column_types_list.append('discrete')
                    else:
                        column_types_list.append('numeric')
                    
                    # Calculate descriptive stats for numeric columns
                    clean_data = col_data.dropna()
                    if len(clean_data) > 0:
                        skewness = clean_data.skew()
                        kurtosis = clean_data.kurtosis()
                        mean = clean_data.mean()
                        std = clean_data.std()
                        min_val = clean_data.min()
                        max_val = clean_data.max()
                        
                        distribution_analysis[col] = {
                            'skewness': float(skewness),
                            'kurtosis': float(kurtosis),
                            'descriptive_stats': {
                                'mean': float(mean),
                                'std': float(std),
                                'min': float(min_val),
                                'max': float(max_val)
                            },
                            'distribution_type': self._determine_distribution(clean_data)
                        }
                        
                        # Calculate outliers
                        q1 = clean_data.quantile(0.25)
                        q3 = clean_data.quantile(0.75)
                        iqr = q3 - q1
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        outliers = clean_data[(clean_data < lower_bound) | (clean_data > upper_bound)]
                        outlier_info[col] = {
                            'count': int(len(outliers)),
                            'percentage': float(len(outliers) / len(clean_data) * 100)
                        }
                        
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    column_types_list.append('timeseries')
                    clean_data = col_data.dropna()
                    if len(clean_data) > 0:
                        datetime_stats[col] = {
                            'start_date': str(clean_data.min()),
                            'end_date': str(clean_data.max()),
                            'range': str(clean_data.max() - clean_data.min()),
                            'time_interval': self._calculate_time_interval(clean_data)
                        }
                else:
                    if col_data.nunique() == 2:
                        unique_values = col_data.dropna().unique()
                        if all(val in [True, False, 'True', 'False', 'true', 'false', '1', '0', 1, 0] for val in unique_values):
                            column_types_list.append('boolean')
                            true_count = (col_data == True).sum() + (col_data == 'True').sum() + (col_data == 'true').sum() + (col_data == 1).sum() + (col_data == '1').sum()
                            false_count = (col_data == False).sum() + (col_data == 'False').sum() + (col_data == 'false').sum() + (col_data == 0).sum() + (col_data == '0').sum()
                            total = true_count + false_count
                            boolean_stats[col] = {
                                'true_count': int(true_count),
                                'false_count': int(false_count),
                                'true_percentage': float(true_count / total * 100) if total > 0 else 0
                            }
                        else:
                            column_types_list.append('categorical')
                    else:
                        column_types_list.append('categorical')
                        value_counts = col_data.value_counts()
                        categorical_stats[col] = {
                            'unique_count': int(col_data.nunique()),
                            'most_frequent': {
                                'value': str(value_counts.index[0]),
                                'count': int(value_counts.iloc[0])
                            },
                            'value_distribution': [
                                {'value': str(val), 'count': int(count)}
                                for val, count in value_counts.head(10).items()
                            ]
                        }
                
                missing_count = col_data.isna().sum()
                if missing_count > 0:
                    missing_values_by_column[col] = int(missing_count)
                    
            except Exception as e:
                logger.error(f"Error processing column {col}: {str(e)}", exc_info=True)
                continue
        
        # Store all metadata in _descriptive_stats
        self._descriptive_stats = {
            'file_stats': file_stats,
            'column_types': {
                'numeric': len([col for col, type_ in zip(self.data.columns, column_types_list) if type_ == 'numeric']),
                'categorical': len([col for col, type_ in zip(self.data.columns, column_types_list) if type_ == 'categorical']),
                'boolean': len([col for col, type_ in zip(self.data.columns, column_types_list) if type_ == 'boolean']),
                'datetime': len([col for col, type_ in zip(self.data.columns, column_types_list) if type_ == 'timeseries']),
                'columns': self.data.columns.tolist(),
                'column_types_list': column_types_list
            },
            'data_quality': quality_metrics,
            'missing_values_by_column': missing_values_by_column,
            'distribution_analysis': distribution_analysis,
            'outlier_info': outlier_info,
            'categorical_stats': categorical_stats,
            'boolean_stats': boolean_stats,
            'datetime_stats': datetime_stats,
            'validation_results': self._validate_data()
        }

    def _calculate_time_interval(self, series: pd.Series) -> str:
        """Calculate the typical time interval between values in a datetime series."""
        if len(series) < 2:
            return "Insufficient data"
            
        # Calculate time differences
        diffs = series.sort_values().diff().dropna()
        
        # Get the most common difference
        mode_diff = diffs.mode()
        if not mode_diff.empty:
            diff = mode_diff.iloc[0]
            if pd.Timedelta(days=1) <= diff < pd.Timedelta(days=2):
                return "Daily"
            elif pd.Timedelta(days=7) <= diff < pd.Timedelta(days=8):
                return "Weekly"
            elif pd.Timedelta(days=30) <= diff < pd.Timedelta(days=31):
                return "Monthly"
            elif pd.Timedelta(days=365) <= diff < pd.Timedelta(days=366):
                return "Yearly"
            else:
                return f"Custom interval: {diff}"
        return "Irregular intervals"

    def get_column_descriptive_stats(self) -> Dict[str, Any]:
        """Get the pre-calculated descriptive statistics for all columns.
        
        Returns:
            Dict containing the stored descriptive statistics, or None if not calculated.
        """
        if self._descriptive_stats is None:
            logger.warning("Descriptive statistics not calculated. Call calculate_descriptive_stats() first.")
            return None
        return self._descriptive_stats

    def _get_transformation_suggestion(self, skewness: float, kurtosis: float) -> str:
        """Determine appropriate transformation based on skewness and kurtosis values.
        
        Args:
            skewness: The skewness value of the distribution
            kurtosis: The kurtosis value of the distribution
            
        Returns:
            String containing transformation suggestions
        """
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

    def generate_plots(self, column_name: str) -> Dict[str, str]:
        """
        Generate plots for a specific column based on its data type.
        
        Args:
            column_name (str): Name of the column to generate plots for
        
        Returns:
            Dict[str, str]: Dictionary containing base64 encoded plot images
        """
        if self.data is None or column_name not in self.data.columns:
            raise ValueError(f"Column {column_name} not found in dataset")
            
        plots = {}
        column_data = self.data[column_name]
        is_numeric = pd.api.types.is_numeric_dtype(column_data)
        
        # Create figure with higher DPI for better quality
        plt.style.use('seaborn')
        
        if is_numeric:
            # Histogram
            fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
            sns.histplot(data=column_data.dropna(), kde=True, ax=ax)
            ax.set_title(f'Distribution of {column_name}')
            plots['histogram'] = self._fig_to_base64(fig)
            plt.close(fig)
            
            # Q-Q Plot
            fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
            stats.probplot(column_data.dropna(), dist="norm", plot=ax)
            ax.set_title(f'Q-Q Plot of {column_name}')
            plots['qqplot'] = self._fig_to_base64(fig)
            plt.close(fig)
            
            # Box Plot
            fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
            sns.boxplot(data=column_data.dropna(), ax=ax)
            ax.set_title(f'Box Plot of {column_name}')
            plots['boxplot'] = self._fig_to_base64(fig)
            plt.close(fig)
        else:
            # Bar Plot for categorical data
            value_counts = column_data.value_counts()
            fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
            value_counts.plot(kind='bar', ax=ax)
            ax.set_title(f'Value Counts for {column_name}')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plots['barplot'] = self._fig_to_base64(fig)
            plt.close(fig)
            
            # Pie Chart
            fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
            plt.pie(value_counts, labels=value_counts.index, autopct='%1.1f%%')
            ax.set_title(f'Distribution of {column_name}')
            plots['piechart'] = self._fig_to_base64(fig)
            plt.close(fig)
        
        return plots

    def _fig_to_base64(self, fig: plt.Figure) -> str:
        """
        Convert a matplotlib figure to base64 encoded string.
        
        Args:
            fig (plt.Figure): Matplotlib figure to convert
            
        Returns:
            str: Base64 encoded string of the figure
        """
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.getvalue()).decode()
        buf.close()
        return img_str

    def update_column_boundaries(self, column_name: str, min_value: float, max_value: float) -> Dict[str, float]:
        """
        Update the boundaries of a numeric column by filtering out values outside the specified range.
        
        Args:
            column_name (str): Name of the column to update
            min_value (float): New minimum value for the column
            max_value (float): New maximum value for the column
            
        Returns:
            Dict[str, float]: Dictionary containing the new statistics for the column
        """
        if self.data is None or column_name not in self.data.columns:
            raise ValueError(f"Column {column_name} not found in dataset")
            
        if not pd.api.types.is_numeric_dtype(self.data[column_name]):
            raise ValueError(f"Column {column_name} is not numeric")
            
        if min_value >= max_value:
            raise ValueError("Minimum value must be less than maximum value")
            
        # Create a mask for values within the specified range
        mask = (self.data[column_name] >= min_value) & (self.data[column_name] <= max_value)
        self.data.loc[~mask, column_name] = np.nan
        
        # Update point flags for this column
        col_idx = self.data.columns.get_loc(column_name)
        self._update_point_flags()
        
        # Return updated statistics for the column
        return self._calculate_statistical_properties(column_name, self._determine_column_type(self.data[column_name]))

    def update_descriptive_stats(self) -> None:
        """Update descriptive statistics after column deletion.
        
        This method efficiently updates _descriptive_stats by removing deleted columns
        and recalculating only the necessary metadata, reusing existing calculations
        where possible.
        """
        if self.data is None or self._descriptive_stats is None:
            # If no data or no existing stats, do a full calculation
            self.calculate_descriptive_stats()
            return
            
        # Get current columns
        current_columns = self.data.columns.tolist()
        
        # Update file stats
        self._descriptive_stats['file_stats'].update({
            'rows': len(self.data),
            'columns': len(self.data.columns),
            'memory_usage': f"{self.data.memory_usage(deep=True).sum() / (1024*1024):.2f} MB",
            'missing_values': int(self.data.isna().sum().sum())
        })
        
        # Filter column types list to keep only existing columns
        old_types = self._descriptive_stats['column_types']['column_types_list']
        old_columns = self._descriptive_stats['column_types']['columns']
        remaining_types = []
        
        # Create mapping of old columns to their types
        col_type_map = dict(zip(old_columns, old_types))
        
        # Keep only types for remaining columns
        for col in current_columns:
            if col in col_type_map:
                remaining_types.append(col_type_map[col])
            else:
                # If we find a new column, we need to determine its type
                col_data = self.data[col]
                if pd.api.types.is_numeric_dtype(col_data):
                    if col_data.nunique() < 20:
                        remaining_types.append('discrete')
                    else:
                        remaining_types.append('numeric')
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    remaining_types.append('timeseries')
                elif col_data.nunique() == 2:
                    remaining_types.append('boolean')
                else:
                    remaining_types.append('categorical')
        
        # Update column types
        self._descriptive_stats['column_types'] = {
            'numeric': len([t for t in remaining_types if t == 'numeric']),
            'categorical': len([t for t in remaining_types if t == 'categorical']),
            'boolean': len([t for t in remaining_types if t == 'boolean']),
            'datetime': len([t for t in remaining_types if t == 'timeseries']),
            'columns': current_columns,
            'column_types_list': remaining_types
        }
        
        # Update missing values by column
        self._descriptive_stats['missing_values_by_column'] = {
            col: int(count) for col, count in 
            self._descriptive_stats['missing_values_by_column'].items()
            if col in current_columns
        }
        
        # Update distribution analysis
        self._descriptive_stats['distribution_analysis'] = {
            col: stats for col, stats in 
            self._descriptive_stats['distribution_analysis'].items()
            if col in current_columns
        }
        
        # Update outlier info
        self._descriptive_stats['outlier_info'] = {
            col: info for col, info in 
            self._descriptive_stats['outlier_info'].items()
            if col in current_columns
        }
        
        # Update categorical stats
        self._descriptive_stats['categorical_stats'] = {
            col: stats for col, stats in 
            self._descriptive_stats['categorical_stats'].items()
            if col in current_columns
        }
        
        # Update boolean stats
        self._descriptive_stats['boolean_stats'] = {
            col: stats for col, stats in 
            self._descriptive_stats['boolean_stats'].items()
            if col in current_columns
        }
        
        # Update datetime stats
        self._descriptive_stats['datetime_stats'] = {
            col: stats for col, stats in 
            self._descriptive_stats['datetime_stats'].items()
            if col in current_columns
        }
        
        # Update point flags array
        if self.point_flags is not None:
            # Get indices of remaining columns
            remaining_indices = [old_columns.index(col) for col in current_columns if col in old_columns]
            # Update point flags array to keep only remaining columns
            self.point_flags = self.point_flags[:, remaining_indices]
            
        # Update data quality metrics
        self._descriptive_stats['data_quality'] = {
            'completeness': self._calculate_completeness(),
            'consistency': self._check_consistency(),
            'accuracy': self._assess_accuracy()
        }
        
        # Update validation results
        self._descriptive_stats['validation_results'] = self._validate_data()
