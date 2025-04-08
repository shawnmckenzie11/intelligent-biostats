from typing import Dict, List, Optional, Union, Any, Tuple
import pandas as pd
import os
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

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
    validation_rules: Dict[str, Any]
    statistical_properties: Dict[str, Any]

class EnhancedDataFrame:
    """Enhanced Pandas DataFrame with metadata for biostatistical analysis."""
    
    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}
        self.current_file: Optional[str] = None
        self.modifications_history: List[Dict[str, Any]] = []
        self.column_metadata: Dict[str, ColumnMetadata] = {}
        self.validation_rules: Dict[str, List[Dict[str, Any]]] = {}
        self.cached_statistics: Dict[str, Any] = {}
        
    def load_data(self, file_path: Optional[str] = None, file_obj: Optional[Any] = None) -> Tuple[bool, Optional[str]]:
        """Load data from file path or file object and compute basic statistics."""
        try:
            if file_obj is not None:
                chunks = pd.read_csv(file_obj, chunksize=10000)
                self.data = pd.concat(chunks, ignore_index=True)
                self.current_file = file_obj.filename
            elif file_path is not None:
                self.data = pd.read_csv(file_path)
                self.current_file = os.path.basename(file_path)
            else:
                raise ValueError("Either file_path or file_obj must be provided")
                
            self.modifications_history = []
            self._update_metadata()
            self._validate_data()
            return True, None
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return False, str(e)
    
    def _update_metadata(self) -> None:
        """Update metadata after data changes."""
        if self.data is not None:
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
            self._update_column_metadata()
    
    def _update_column_metadata(self) -> None:
        """Update metadata for each column."""
        if self.data is None:
            return
            
        for col in self.data.columns:
            col_type = self._determine_column_type(self.data[col])
            missing_count = self.data[col].isna().sum()
            unique_values = self.data[col].nunique()
            
            self.column_metadata[col] = ColumnMetadata(
                name=col,
                type=col_type,
                missing_count=int(missing_count),
                unique_values=int(unique_values),
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
    
    def _calculate_statistical_properties(self, column: str, col_type: ColumnType) -> Dict[str, Any]:
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
        """Determine the statistical distribution of a series."""
        # Implementation for distribution testing
        return "unknown"
    
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
        """Assess data accuracy."""
        accuracy_metrics = {
            'outliers': self._detect_outliers(),
            'suspicious_values': self._find_suspicious_values()
        }
        
        return accuracy_metrics
    
    def _detect_outliers(self) -> Dict[str, Any]:
        """Detect outliers in numeric columns."""
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
    
    def _find_suspicious_values(self) -> Dict[str, Any]:
        """Find potentially suspicious values."""
        suspicious = {}
        
        for col, metadata in self.column_metadata.items():
            if metadata.type == ColumnType.NUMERIC:
                series = self.data[col]
                zero_count = (series == 0).sum()
                if zero_count > len(series) * 0.5:  # More than 50% zeros
                    suspicious[col] = {
                        'issue': 'high_zero_count',
                        'count': int(zero_count),
                        'percentage': float(zero_count / len(series) * 100)
                    }
                    
        return suspicious

    def _analyze_column_types(self):
        """Analyze and categorize columns, returning column types and counts."""
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

    def modify_data(self, modification_request, ai_engine=None):
        """Apply modifications to the data and update metadata."""
        if self.data is None:
            return False, "No data loaded", None
            
        try:
            # Store original state
            original_data = self.data.copy()
            
            # Apply modifications using the AI engine if provided
            if ai_engine is not None:
                modified_df, was_modified = ai_engine.modify_data(self.data, modification_request)
            else:
                # Simple modification without AI engine
                modified_df = self.data.copy()
                was_modified = False  # Implement basic modifications here if needed
            
            if was_modified:
                # Update the data
                self.data = modified_df
                
                # Track the modification
                self.modifications_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'modification': modification_request,
                    'changes': {
                        'rows': len(self.data) - len(original_data),
                        'columns': len(self.data.columns) - len(original_data.columns)
                    }
                })
                
                # Update metadata
                self._update_metadata()
                
                # Create preview dict
                preview_dict = {}
                preview_df = self.data.head()
                for column in preview_df.columns:
                    preview_dict[str(column)] = [
                        None if pd.isna(x) else x 
                        for x in preview_df[column].tolist()
                    ]
                
                return True, "Modifications applied successfully", preview_dict
            else:
                return False, "No modifications were made", None
                
        except Exception as e:
            return False, f"Error applying modifications: {str(e)}", None

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
