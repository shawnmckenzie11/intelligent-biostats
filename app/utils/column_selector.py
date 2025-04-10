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
        Only supports numeric specifications:
        - Column numbers (e.g., "4", "5, 9")
        - Column ranges (e.g., "3-5", "6-10")
        - Column number plus remaining (e.g., "4+")
        
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
                # Check if part contains any non-numeric characters (except for + and -)
                if not all(c.isdigit() or c in ['+', '-', ' '] for c in part):
                    self._current_columns = set()
                    self._current_error = "Only numeric column specifications are allowed (e.g., '4', '3-5', '4+')"
                    self._is_valid = False
                    return
                
                # Handle plus format (e.g., "4+")
                if '+' in part:
                    try:
                        start = int(part.replace('+', ''))
                        if start < 1 or start > len(self.data_manager.data.columns):
                            self._current_columns = set()
                            self._current_error = f"Column number {start} is out of bounds"
                            self._is_valid = False
                            return
                        cols_to_delete.update(range(start-1, len(self.data_manager.data.columns)))
                        continue
                    except ValueError:
                        self._current_columns = set()
                        self._current_error = f"Invalid column specification: {part}"
                        self._is_valid = False
                        return
                
                # Handle range format (e.g., "4-7")
                if '-' in part:
                    try:
                        start, end = map(int, part.split('-'))
                        if start < 1 or end > len(self.data_manager.data.columns):
                            self._current_columns = set()
                            self._current_error = f"Column range {part} is out of bounds"
                            self._is_valid = False
                            return
                        cols_to_delete.update(range(start-1, end))  # Convert to 0-based index
                        continue
                    except ValueError:
                        self._current_columns = set()
                        self._current_error = f"Invalid column specification: {part}"
                        self._is_valid = False
                        return
                
                # Single column number
                try:
                    col_num = int(part)
                    if col_num < 1 or col_num > len(self.data_manager.data.columns):
                        self._current_columns = set()
                        self._current_error = f"Column number {col_num} is out of bounds"
                        self._is_valid = False
                        return
                    cols_to_delete.add(col_num-1)  # Convert to 0-based index
                except ValueError:
                    self._current_columns = set()
                    self._current_error = f"Invalid column specification: {part}"
                    self._is_valid = False
                    return
            
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
        Only supports numeric specifications:
        - Column numbers (e.g., "4", "5, 9")
        - Column ranges (e.g., "3-5", "6-10")
        - Column number plus remaining (e.g., "4+")
        
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
            
        # Check if all columns exist and are numeric specifications
        for col in column_names:
            # Check if part contains any non-numeric characters (except for + and -)
            if not all(c.isdigit() or c in ['+', '-', ' '] for c in col):
                return False, "Only numeric column specifications are allowed (e.g., '4', '3-5', '4+')"
            
            # Handle plus format (e.g., "4+")
            if '+' in col:
                try:
                    start = int(col.replace('+', ''))
                    if start < 1 or start > len(self.data_manager.data.columns):
                        return False, f"Column number {start} is out of bounds"
                except ValueError:
                    return False, f"Invalid column specification: {col}"
            
            # Handle range format (e.g., "4-7")
            elif '-' in col:
                try:
                    start, end = map(int, col.split('-'))
                    if start < 1 or end > len(self.data_manager.data.columns):
                        return False, f"Column range {col} is out of bounds"
                except ValueError:
                    return False, f"Invalid column specification: {col}"
            
            # Single column number
            else:
                try:
                    col_num = int(col)
                    if col_num < 1 or col_num > len(self.data_manager.data.columns):
                        return False, f"Column number {col_num} is out of bounds"
                except ValueError:
                    return False, f"Invalid column specification: {col}"
            
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