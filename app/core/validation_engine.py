from typing import List, Dict, Any, Tuple
import pandas as pd
from app.core.data_manager import DataManager, ColumnType

class ValidationEngine:
    """
    A dedicated engine for handling data validation and quality checks.
    Provides real-time validation and sophisticated validation rules.
    """
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.validation_rules = {}
        self.validation_results = {
            'errors': [],
            'warnings': [],
            'passed': True
        }
    
    def validate_column_selection(self, column_names: List[str]) -> Tuple[bool, str]:
        """
        Validate a list of column names for selection.
        
        Args:
            column_names: List of column names to validate
            
        Returns:
            Tuple containing:
            - Boolean indicating if validation passed
            - Error message (if any)
        """
        if not column_names:
            return False, "No columns selected"
            
        if self.data_manager.data is None:
            return False, "No data loaded"
            
        # Check if all columns exist
        missing_cols = [col for col in column_names if col not in self.data_manager.data.columns]
        if missing_cols:
            return False, f"Columns not found: {', '.join(missing_cols)}"
            
        return True, ""
    
    def validate_column_types(self, column_names: List[str], required_types: List[ColumnType]) -> Tuple[bool, str]:
        """
        Validate that selected columns match required data types.
        
        Args:
            column_names: List of column names to validate
            required_types: List of required column types
            
        Returns:
            Tuple containing:
            - Boolean indicating if validation passed
            - Error message (if any)
        """
        if not column_names:
            return False, "No columns selected"
            
        invalid_types = []
        for col in column_names:
            col_type = self.data_manager.metadata['column_types']['column_types_list'][
                self.data_manager.data.columns.get_loc(col)
            ]
            if col_type not in required_types:
                invalid_types.append(f"{col} ({col_type})")
                
        if invalid_types:
            return False, f"Invalid column types: {', '.join(invalid_types)}"
            
        return True, ""
    
    def add_validation_rule(self, column: str, rule_name: str, rule_value: Any) -> None:
        """
        Add a custom validation rule for a specific column.
        
        Args:
            column: Column name
            rule_name: Name of the rule
            rule_value: Value or condition for the rule
        """
        if column not in self.validation_rules:
            self.validation_rules[column] = {}
        self.validation_rules[column][rule_name] = rule_value
    
    def validate_custom_rules(self, column: str) -> Tuple[bool, List[str]]:
        """
        Validate a column against its custom rules.
        
        Args:
            column: Column name to validate
            
        Returns:
            Tuple containing:
            - Boolean indicating if validation passed
            - List of error messages
        """
        if column not in self.validation_rules:
            return True, []
            
        errors = []
        series = self.data_manager.data[column]
        rules = self.validation_rules[column]
        
        for rule_name, rule_value in rules.items():
            if rule_name == 'min_value' and series.min() < rule_value:
                errors.append(f"Column {column} has values below minimum allowed ({rule_value})")
            elif rule_name == 'max_value' and series.max() > rule_value:
                errors.append(f"Column {column} has values above maximum allowed ({rule_value})")
            elif rule_name == 'allowed_values' and not series.isin(rule_value).all():
                errors.append(f"Column {column} contains values not in allowed set")
                
        return len(errors) == 0, errors
    
    def get_column_quality_metrics(self, column: str) -> Dict[str, Any]:
        """
        Get quality metrics for a specific column.
        
        Args:
            column: Column name
            
        Returns:
            Dictionary containing quality metrics
        """
        if column not in self.data_manager.data.columns:
            return {}
            
        series = self.data_manager.data[column]
        metrics = {
            'missing_count': series.isna().sum(),
            'unique_count': series.nunique(),
            'duplicate_count': len(series) - series.nunique(),
            'type': self.data_manager.metadata['column_types']['column_types_list'][
                self.data_manager.data.columns.get_loc(column)
            ]
        }
        
        if pd.api.types.is_numeric_dtype(series):
            metrics.update({
                'min': series.min(),
                'max': series.max(),
                'mean': series.mean(),
                'std': series.std()
            })
            
        return metrics 