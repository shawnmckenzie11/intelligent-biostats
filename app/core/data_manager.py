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
        
    def load_data(self, file_path: Optional[str] = None, file_obj: Optional[Any] = None) -> Tuple[bool, Optional[str]]:
        """Load data from file path or file object and compute basic statistics."""
        try:
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

    def modify_data(self, modification, ai_engine):
        """Apply modifications to the data using AI assistance."""
        try:
            # Check if modification is a column deletion request
            if isinstance(modification, (str, list)) and (isinstance(modification, str) or all(isinstance(x, str) for x in modification)):
                return self.process_delete_columns(modification)
                
            # For other modifications, use AI engine
            return ai_engine.process_modification(self, modification)
                
        except Exception as e:
            logger.error(f"Error modifying data: {str(e)}", exc_info=True)
            return False, str(e), None

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
            
    def get_data_preview(self):
        """Get a preview of the current data."""
        if self.data is None:
            return None
            
        preview_dict = {}
        preview_df = self.data.head()
        for column in preview_df.columns:
            preview_dict[str(column)] = [
                None if pd.isna(x) else x 
                for x in preview_df[column].tolist()
            ]
        return preview_dict

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

    def delete_column(self, column_name: str) -> Tuple[bool, Optional[str]]:
        """Delete a column from the DataFrame and update metadata."""
        try:
            if self.data is None:
                return False, "No data loaded"
                
            if column_name not in self.data.columns:
                return False, f"Column '{column_name}' not found"
                
            # Delete the column
            self.data = self.data.drop(columns=[column_name])
            
            # Update all metadata recursively
            self._update_metadata()
            
            return True, None
        except Exception as e:
            logger.error(f"Error deleting column: {str(e)}")
            return False, str(e)
            
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

    def process_delete_columns(self, columns_to_delete):
        """Process column deletion requests directly.
        
        Args:
            columns_to_delete (list or str or int): List of column names/indices to delete, or single column name/index
            
        Returns:
            tuple: (success, message, preview)
        """
        try:
            if not isinstance(columns_to_delete, list):
                columns_to_delete = [columns_to_delete]
                
            # Convert any numeric indices to column names
            columns_to_delete = [
                self.data.columns[col] if isinstance(col, int) else col 
                for col in columns_to_delete
            ]
                
            # Validate columns exist
            missing_cols = [col for col in columns_to_delete if col not in self.data.columns]
            if missing_cols:
                return False, f"Columns not found: {', '.join(missing_cols)}", None
                
            # Drop columns
            self.data = self.data.drop(columns=columns_to_delete)
            
            # Update metadata
            self._update_metadata()
            
            # Get preview
            preview = self.get_data_preview()
            
            return True, f"Successfully deleted columns: {', '.join(columns_to_delete)}", preview
            
        except Exception as e:
            logger.error(f"Error deleting columns: {str(e)}", exc_info=True)
            return False, str(e), None
