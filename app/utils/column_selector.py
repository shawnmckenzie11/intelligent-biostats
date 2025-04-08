from typing import List, Union, Tuple
import re
from app.core.data_manager import DataManager

class ColumnSelector:
    """
    Utility class for processing text-based column selection and converting it to actual column names.
    Integrates with DataManager to ensure proper validation and processing.
    """
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        
    def parse_column_specification(self, text: str) -> Tuple[List[str], str]:
        """
        Parse a text specification of columns into a list of column names.
        
        Args:
            text: String containing column specification (e.g., "3,4" or "4-10" or "Age, Height")
            
        Returns:
            Tuple containing:
            - List of column names
            - Error message (if any)
        """
        if not text or not text.strip():
            return [], "No column specification provided"
            
        if self.data_manager.data is None:
            return [], "No data loaded"
            
        try:
            # Split by commas and handle ranges
            parts = [part.strip() for part in text.split(',')]
            column_indices = set()
            
            for part in parts:
                # Handle numeric indices
                if part.isdigit():
                    idx = int(part) - 1  # Convert to 0-based index
                    if 0 <= idx < len(self.data_manager.data.columns):
                        column_indices.add(idx)
                    else:
                        return [], f"Column index {part} is out of range"
                
                # Handle ranges (e.g., "4-10")
                elif '-' in part:
                    try:
                        start, end = map(int, part.split('-'))
                        start_idx = start - 1
                        end_idx = end - 1
                        
                        if not (0 <= start_idx < len(self.data_manager.data.columns) and 
                               0 <= end_idx < len(self.data_manager.data.columns)):
                            return [], f"Range {part} contains out-of-bounds indices"
                            
                        if start_idx > end_idx:
                            return [], f"Invalid range {part}: start must be less than end"
                            
                        column_indices.update(range(start_idx, end_idx + 1))
                    except ValueError:
                        return [], f"Invalid range format: {part}"
                
                # Handle column names
                else:
                    if part in self.data_manager.data.columns:
                        column_indices.add(self.data_manager.data.columns.get_loc(part))
                    else:
                        return [], f"Column '{part}' not found"
            
            # Convert indices to column names
            column_names = [self.data_manager.data.columns[i] for i in sorted(column_indices)]
            return column_names, ""
            
        except Exception as e:
            return [], f"Error parsing column specification: {str(e)}"
    
    def validate_columns(self, column_names: List[str]) -> Tuple[bool, str]:
        """
        Validate that the selected columns exist and are appropriate for the intended operation.
        
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
    
    def get_column_types(self, column_names: List[str]) -> List[str]:
        """
        Get the types of the specified columns.
        
        Args:
            column_names: List of column names
            
        Returns:
            List of column types
        """
        if self.data_manager.data is None:
            return []
            
        column_types = []
        for col in column_names:
            col_type = self.data_manager.metadata['column_types']['column_types_list'][
                self.data_manager.data.columns.get_loc(col)
            ]
            column_types.append(col_type)
            
        return column_types
    
    def process_column_selection(self, text: str) -> Tuple[List[str], str]:
        """
        Complete process of parsing and validating column selection.
        
        Args:
            text: String containing column specification
            
        Returns:
            Tuple containing:
            - List of column names
            - Error message (if any)
        """
        # Parse the text into column names
        column_names, error = self.parse_column_specification(text)
        if error:
            return [], error
            
        # Validate the columns
        is_valid, error = self.validate_columns(column_names)
        if not is_valid:
            return [], error
            
        return column_names, "" 