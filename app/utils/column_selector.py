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
        self._current_columns = set()
        self._current_error = "No column specification provided"
        self._is_valid = False
        
    def get_current_state(self) -> dict:
        """
        Get the current validation state.
        
        Returns:
            dict containing:
            - columns: set of valid column names
            - error: current error message
            - is_valid: boolean indicating if current state is valid
        """
        return {
            'columns': list(self._current_columns),
            'error': self._current_error,
            'is_valid': self._is_valid
        }
        
    def parse_column_specification(self, text: str) -> None:
        """
        Parse a text specification of columns and update the current state.
        Supports:
        - Column numbers (e.g., "4", "5, 9")
        - Column ranges (e.g., "3-5", "6-10")
        - Column names (e.g., "Age", "Age, length")
        - Column name ranges (e.g., "Age - height")
        
        Args:
            text: String containing column specification
        """
        if not text:
            self._current_columns = set()
            self._current_error = "No column specification provided"
            self._is_valid = False
            return
            
        if self.data_manager.data is None:
            self._current_columns = set()
            self._current_error = "No data loaded"
            self._is_valid = False
            return
            
        try:
            # Split by commas and process each part
            parts = [p.strip() for p in text.split(',')]
            cols_to_delete = set()
            
            for part in parts:
                # Handle numeric column specifications
                if any(c.isdigit() for c in part):
                    # Handle range format (e.g., "4-7" or "9+")
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        if start < 1 or end > len(self.data_manager.data.columns):
                            self._current_columns = set()
                            self._current_error = f"Column range {part} is out of bounds"
                            self._is_valid = False
                            return
                        cols_to_delete.update(range(start-1, end))  # Convert to 0-based index
                    else:
                        # Single column number
                        col_num = int(part)
                        if col_num < 1 or col_num > len(self.data_manager.data.columns):
                            self._current_columns = set()
                            self._current_error = f"Column number {col_num} is out of bounds"
                            self._is_valid = False
                            return
                        cols_to_delete.add(col_num-1)  # Convert to 0-based index
                
                # Handle column name specifications
                else:
                    # Handle range format (e.g., "Age - height")
                    if '-' in part:
                        start_col, end_col = [c.strip() for c in part.split('-')]
                        if start_col not in self.data_manager.data.columns:
                            self._current_columns = set()
                            self._current_error = f"Column {start_col} not found"
                            self._is_valid = False
                            return
                        if end_col not in self.data_manager.data.columns:
                            self._current_columns = set()
                            self._current_error = f"Column {end_col} not found"
                            self._is_valid = False
                            return
                        start_idx = self.data_manager.data.columns.get_loc(start_col)
                        end_idx = self.data_manager.data.columns.get_loc(end_col)
                        cols_to_delete.update(range(start_idx, end_idx + 1))
                    else:
                        # Single column name
                        if part not in self.data_manager.data.columns:
                            self._current_columns = set()
                            self._current_error = f"Column {part} not found"
                            self._is_valid = False
                            return
                        cols_to_delete.add(self.data_manager.data.columns.get_loc(part))
            
            # Convert indices to column names
            self._current_columns = set(self.data_manager.data.columns[i] for i in sorted(cols_to_delete))
            self._current_error = ""
            self._is_valid = True
            
        except Exception as e:
            self._current_columns = set()
            self._current_error = f"Error parsing column specification: {str(e)}"
            self._is_valid = False
    
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
        self.parse_column_specification(text)
        if self._current_error:
            return [], self._current_error
            
        # Validate the columns
        is_valid, error = self.validate_columns(list(self._current_columns))
        if not is_valid:
            return [], error
            
        return list(self._current_columns), "" 