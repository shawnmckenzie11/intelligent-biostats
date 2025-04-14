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

logger = logging.getLogger(__name__)

class ColumnType(Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    TIMESERIES = "timeseries"
    DISCRETE = "discrete"
    ORDINAL = "ordinal"
    CENSORED = "censored"

@dataclass
class ColumnMetadata:
    name: str
    type: ColumnType
    missing_count: int
    unique_values: int
    outlier_count: int
    validation_rules: Dict[str, Any]
    statistical_properties: Dict[str, Any]

class DataManager:
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
        self.data: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}
        self.current_file: Optional[str] = None
        self.modifications_history: List[Dict[str, Any]] = []
        self.column_metadata: Dict[str, ColumnMetadata] = {}
        self.validation_rules: Dict[str, List[Dict[str, Any]]] = {}
        self.cached_statistics: Dict[str, Any] = {}
        self._state_logger = StateLogger()
        self.point_flags: Optional[np.ndarray] = None  # Will be (n_rows, n_cols) array of DataPointFlag
        self._descriptive_stats: Optional[Dict[str, Any]] = None  # Cache for descriptive statistics
        
    def reset(self) -> None:
        """Reset the DataManager to its initial state."""
        self.data = None
        self.metadata = {}
        self.current_file = None
        self.modifications_history = []
        self.column_metadata = {}
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
            self._validate_data()
            self.initialize_metadata()
            
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
    
    def initialize_metadata(self) -> None:
        """Initialize metadata when data is first loaded."""
        if self.data is None:
            return
        
        # Set basic metadata
        self.metadata = {
            'file_stats': {
                'filename': self.current_file,
                'rows': len(self.data),
                'columns': len(self.data.columns),
                'memory_usage': f"{self.data.memory_usage(deep=True).sum() / (1024*1024):.2f} MB"
            },
            'column_types': self._analyze_column_types(),
            'data_quality': self._assess_data_quality()
        }
        
        # Update point flags
        self._update_point_flags()
    
    def _update_metadata(self) -> None:
        """Update metadata after data changes."""
        if self.data is None:
            return
        
        # Update basic metadata
        self.metadata = {
            'file_stats': {
                'filename': self.current_file,
                'rows': len(self.data),
                'columns': len(self.data.columns),
                'memory_usage': f"{self.data.memory_usage(deep=True).sum() / (1024*1024):.2f} MB"
            },
            'column_types': self._analyze_column_types(),
            'data_quality': self._assess_data_quality()
        }
        
        # Update column metadata (which may trigger additional updates)
        self._update_column_metadata()
        
        # Update point flags
        self._update_point_flags()
    
    def _update_column_metadata(self) -> None:
        """Update metadata for each column."""
        if self.data is None:
            return
        
        for col in self.data.columns:
            col_type = self._determine_column_type(self.data[col])
            col_idx = self.data.columns.get_loc(col)
            
            # Get counts from point flags array
            col_flags = self.get_column_flags(col_idx)
            missing_count = np.sum(col_flags == DataPointFlag.MISSING)
            outlier_count = np.sum(col_flags == DataPointFlag.OUTLIER)
            
            self.column_metadata[col] = ColumnMetadata(
                name=col,
                type=col_type,
                missing_count=int(missing_count),
                unique_values=int(self.data[col].nunique()),
                outlier_count=int(outlier_count),
                validation_rules=self._get_validation_rules(col, col_type),
                statistical_properties=self._calculate_statistical_properties(col, col_type)
            )
    
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
                'distribution_type': self._determine_distribution(column, col_type, ignore_flags)
            })
            
        return properties
    
    def _determine_distribution(self, column: str, col_type: ColumnType, ignore_flags: bool = False) -> Dict[str, Any]:
        """Determine the statistical distribution of a numerical column.
        
        Args:
            column: Name of the column to analyze
            col_type: Type of the column
            ignore_flags: If True, ignore values flagged as outliers or missing
            
        Returns:
            Dictionary containing distribution information including:
            - distribution_type: The identified distribution type
            - parameters: Distribution-specific parameters
            - goodness_of_fit: Goodness of fit metrics
            - confidence: Confidence level in the identification
        """
        if self.data is None or column not in self.data.columns:
            return {
                'distribution_type': 'unknown',
                'error': 'Column not found or no data loaded'
            }
        
        if col_type not in [ColumnType.NUMERIC, ColumnType.DISCRETE]:
            return {
                'distribution_type': 'non_numeric',
                'error': 'Distribution analysis only applicable to numeric data'
            }
        
        try:
            # Get the data series
            series = self.data[column].copy()
            
            # If ignoring flags, remove flagged values
            if ignore_flags and self.point_flags is not None:
                col_idx = self.data.columns.get_loc(column)
                valid_mask = self.point_flags[:, col_idx] == DataPointFlag.NORMAL
                series = series[valid_mask]
            
            # Remove any remaining NaN values
            series = series.dropna()
            
            if len(series) < 30:
                return {
                    'distribution_type': 'insufficient_data',
                    'error': 'Insufficient data points for distribution analysis'
                }
            
            # Calculate basic statistics
            mean = series.mean()
            std = series.std()
            skewness = series.skew()
            kurtosis = series.kurtosis()
            
            # Initialize result dictionary
            result = {
                'distribution_type': 'unknown',
                'parameters': {},
                'goodness_of_fit': {},
                'confidence': 0.0
            }
            
            # Test for normal distribution
            if abs(skewness) < 0.5 and abs(kurtosis) < 2:
                # Perform Shapiro-Wilk test for normality
                shapiro_stat, shapiro_p = stats.shapiro(series)
                
                if shapiro_p > 0.05:  # Cannot reject null hypothesis of normality
                    result['distribution_type'] = 'normal'
                    result['parameters'] = {
                        'mean': float(mean),
                        'std': float(std)
                    }
                    result['goodness_of_fit'] = {
                        'shapiro_wilk_stat': float(shapiro_stat),
                        'shapiro_wilk_p': float(shapiro_p)
                    }
                    result['confidence'] = 1.0 - shapiro_p
                    return result
            
            # Test for log-normal distribution
            if skewness > 0:  # Positive skew suggests log-normal
                log_series = np.log(series[series > 0])
                if len(log_series) > 30:  # Ensure enough data points
                    log_shapiro_stat, log_shapiro_p = stats.shapiro(log_series)
                    if log_shapiro_p > 0.05:
                        result['distribution_type'] = 'log_normal'
                        result['parameters'] = {
                            'mu': float(log_series.mean()),
                            'sigma': float(log_series.std())
                        }
                        result['goodness_of_fit'] = {
                            'shapiro_wilk_stat': float(log_shapiro_stat),
                            'shapiro_wilk_p': float(log_shapiro_p)
                        }
                        result['confidence'] = 1.0 - log_shapiro_p
                        return result
            
            # Test for exponential distribution
            if skewness > 1 and kurtosis > 6:  # Exponential-like characteristics
                exp_scale = 1.0 / mean
                ks_stat, ks_p = stats.kstest(series, 'expon', args=(0, 1/exp_scale))
                if ks_p > 0.05:
                    result['distribution_type'] = 'exponential'
                    result['parameters'] = {
                        'scale': float(1/exp_scale)
                    }
                    result['goodness_of_fit'] = {
                        'ks_stat': float(ks_stat),
                        'ks_p': float(ks_p)
                    }
                    result['confidence'] = 1.0 - ks_p
                    return result
            
            # Test for uniform distribution
            if abs(skewness) < 0.5 and abs(kurtosis) < 1.8:  # Uniform-like characteristics
                ks_stat, ks_p = stats.kstest(series, 'uniform', args=(series.min(), series.max() - series.min()))
                if ks_p > 0.05:
                    result['distribution_type'] = 'uniform'
                    result['parameters'] = {
                        'min': float(series.min()),
                        'max': float(series.max())
                    }
                    result['goodness_of_fit'] = {
                        'ks_stat': float(ks_stat),
                        'ks_p': float(ks_p)
                    }
                    result['confidence'] = 1.0 - ks_p
                    return result
            
            # If no specific distribution is identified, classify based on skewness and kurtosis
            if skewness > 1:
                result['distribution_type'] = 'right_skewed'
            elif skewness < -1:
                result['distribution_type'] = 'left_skewed'
            elif kurtosis > 3:
                result['distribution_type'] = 'heavy_tailed'
            elif kurtosis < 1.8:
                result['distribution_type'] = 'light_tailed'
            else:
                result['distribution_type'] = 'unknown'
            
            # Add descriptive statistics
            result['descriptive_stats'] = {
                'skewness': float(skewness),
                'kurtosis': float(kurtosis),
                'mean': float(mean),
                'std': float(std)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error determining distribution for column {column}: {str(e)}")
            return {
                'distribution_type': 'error',
                'error': str(e)
            }
    
    def _validate_data(self) -> None:
        """Validate the data against defined rules."""
        if self.data is None:
            return
        
        validation_results = {
            'errors': [],
            'warnings': [],
            'passed': True
        }
        
        for col, metadata in self.column_metadata.items():
            # Check missing values
            if metadata.missing_count > 0 and not metadata.validation_rules['missing_allowed']:
                validation_results['errors'].append(f"Column {col} has missing values but they are not allowed")
            
            # Type-specific validation
            if metadata.type == ColumnType.NUMERIC:
                self._validate_numeric_column(col, metadata, validation_results)
            elif metadata.type == ColumnType.CATEGORICAL:
                self._validate_categorical_column(col, metadata, validation_results)
                
        self.metadata['validation_results'] = validation_results
    
    def _validate_numeric_column(self, column: str, metadata: ColumnMetadata, results: Dict[str, Any]) -> None:
        """Validate a numeric column."""
        series = self.data[column]
        rules = metadata.validation_rules
        
        if 'min_value' in rules and series.min() < rules['min_value']:
            results['errors'].append(f"Column {column} has values below minimum allowed")
        if 'max_value' in rules and series.max() > rules['max_value']:
            results['errors'].append(f"Column {column} has values above maximum allowed")
        if not rules['allow_negative'] and (series < 0).any():
            results['errors'].append(f"Column {column} has negative values but they are not allowed")
    
    def _validate_categorical_column(self, column: str, metadata: ColumnMetadata, results: Dict[str, Any]) -> None:
        """Validate a categorical column."""
        series = self.data[column]
        rules = metadata.validation_rules
        
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
        """Get data and statistics for a specific column."""
        if self.data is None or column_name not in self.data.columns:
            return None, "Column not found"
            
        try:
            column_data = self.data[column_name]
            column_type = self.metadata['column_types']['column_types_list'][list(self.data.columns).index(column_name)]
            
            # Get basic statistics based on column type
            stats = {
                'Type': column_type,
                'Missingues': str(column_data.isna().sum()),
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
                    
            # Update metadata after flagging outliers
            self._update_metadata()
            
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
        """Get flags for all points in a row."""
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
            if not isinstance(column_to_delete, list):
                column_to_delete = [column_to_delete]
                
            print("\n=== BEFORE COLUMN DELETION ===")
            print("Original columns:", self.data.columns.tolist())
            print("Columns to delete:", column_to_delete)
                
            # Convert any numeric indices to column names
            column_to_delete = [
                self.data.columns[col] if isinstance(col, int) else col 
                for col in column_to_delete
            ]
            print("\nAfter converting indices:")
            print("Columns to delete:", column_to_delete)
                
            # Validate columns exist
            missing_cols = [col for col in column_to_delete if col not in self.data.columns]
            if missing_cols:
                return False, f"Columns not found: {', '.join(missing_cols)}", None
                
            # Get the original column order
            original_columns = self.data.columns.tolist()
            print("\nOriginal column order:", original_columns)
            
            # Remove the columns to delete from the original order
            remaining_columns = [col for col in original_columns if col not in column_to_delete]
            print("\nRemaining columns in order:", remaining_columns)
            
            # Drop columns and reorder to maintain original order using reindex
            print("\nBefore drop and reindex:")
            print("DataFrame columns:", self.data.columns.tolist())
            
            self.data = self.data.drop(columns=column_to_delete)
            print("\nAfter drop:")
            print("DataFrame columns:", self.data.columns.tolist())
            
            self.data = self.data.reindex(columns=remaining_columns)
            print("\nAfter reindex:")
            print("DataFrame columns:", self.data.columns.tolist())
            
            # Update metadata
            self._update_metadata()
            
            # Get preview
            preview = self.get_data_preview()
            print("\n=== AFTER COLUMN DELETION ===")
            print("Final DataFrame columns:", self.data.columns.tolist())
            print("Preview columns:", list(preview.keys()))
            
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
        """Calculate and store descriptive statistics for all columns in the dataset.
        
        This method should be called after loading data to pre-calculate statistics
        for better performance with large files.
        """
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
        
        for i, col in enumerate(self.data.columns):
            try:
                # Get column data and type
                col_data = self.data[col]
                
                # Determine column type
                if pd.api.types.is_numeric_dtype(col_data):
                    if col_data.nunique() < 20:  # threshold for discrete
                        column_types_list.append('discrete')
                    else:
                        column_types_list.append('numeric')
                        # Calculate skewness and kurtosis for numeric columns
                        skewness = col_data.skew()
                        kurtosis = col_data.kurtosis()
                        distribution_analysis[col] = {
                            'skewness': float(skewness),
                            'kurtosis': float(kurtosis),
                            'transformation_suggestion': self._get_transformation_suggestion(skewness, kurtosis)
                        }
                        
                        # Calculate outliers for numeric columns
                        mean = col_data.mean()
                        std = col_data.std()
                        q1 = col_data.quantile(0.25)
                        q3 = col_data.quantile(0.75)
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
                        outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                        outlier_info[col] = {
                            'count': int(len(outliers)),
                            'percentage': float(len(outliers) / len(col_data) * 100)
                        }
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    column_types_list.append('timeseries')
                    # Calculate datetime statistics
                    datetime_stats[col] = {
                        'start_date': str(col_data.min()),
                        'end_date': str(col_data.max()),
                        'range': str(col_data.max() - col_data.min()),
                        'time_interval': self._calculate_time_interval(col_data)
                    }
                else:
                    # For non-numeric, non-datetime columns
                    if col_data.nunique() == 2:
                        # Check if the values are actually boolean-like
                        unique_values = col_data.dropna().unique()
                        if all(val in [True, False, 'True', 'False', 'true', 'false', '1', '0', 1, 0] for val in unique_values):
                            column_types_list.append('boolean')
                            # Calculate boolean statistics
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
                        # Calculate categorical statistics
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
                
                # Count missing values
                missing_count = col_data.isna().sum()
                if missing_count > 0:
                    missing_values_by_column[col] = int(missing_count)
                    
            except Exception as e:
                logger.error(f"Error processing column {col}: {str(e)}", exc_info=True)
                continue
        
        # Store the calculated statistics
        self._descriptive_stats = {
            'file_stats': self.get_file_statistics(),
            'column_types': {
                'numeric': len([col for col, type_ in zip(self.data.columns, column_types_list) if type_ == 'numeric']),
                'categorical': len([col for col, type_ in zip(self.data.columns, column_types_list) if type_ == 'categorical']),
                'boolean': len([col for col, type_ in zip(self.data.columns, column_types_list) if type_ == 'boolean']),
                'datetime': len([col for col, type_ in zip(self.data.columns, column_types_list) if type_ == 'timeseries']),
                'columns': self.data.columns.tolist(),
                'column_types_list': column_types_list
            },
            'missing_values_by_column': missing_values_by_column,
            'distribution_analysis': distribution_analysis,
            'outlier_info': outlier_info,
            'categorical_stats': categorical_stats,
            'boolean_stats': boolean_stats,
            'datetime_stats': datetime_stats
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
