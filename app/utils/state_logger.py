import logging
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union
from app.core.enums import DataPointFlag
import os

logger = logging.getLogger(__name__)

class StateLogger:
    """Logs the state of data operations for debugging and tracking."""
    
    def __init__(self, log_dir: str = "debug_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file = None
        self.current_csv_name = None
        
        # Setup logging
        self.logger = logging.getLogger('state_logger')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers to prevent duplicate logging
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
    
    def on_csv_load(self, csv_name: str) -> None:
        """Create a new log file when a CSV is loaded.
        
        Args:
            csv_name: Name of the CSV file being loaded
        """
        # Create a new log file with timestamp and CSV name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.current_csv_name = csv_name
        self.current_log_file = self.log_dir / f'state_{timestamp}_{csv_name}.log'
        
        # Remove any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create a new file handler for the current log file
        handler = logging.FileHandler(str(self.current_log_file), mode='a')
        handler.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)
        
        # Log the CSV load event
        self.logger.debug(json.dumps({
            'timestamp': datetime.now().isoformat(),
            'operation': 'csv_load',
            'csv_name': csv_name
        }))
        
    def capture_state(self, df: Optional[Union[pd.DataFrame, 'DataManager']], operation: str = "state_check", additional_info: Optional[Dict[str, Any]] = None) -> None:
        """Capture the current state of the DataFrame or DataManager.
        
        Args:
            df: The DataFrame or DataManager instance to log
            operation: Description of the operation being performed
            additional_info: Any additional information to log
        """
        try:
            # Get the underlying DataFrame if DataManager is passed
            if hasattr(df, 'data'):
                df = df.data
                
            if df is None:
                logger.warning("No data to log")
                return
                
            # Create log entry
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'shape': df.shape if hasattr(df, 'shape') else None,
                'columns': list(df.columns) if hasattr(df, 'columns') else None,
                'additional_info': additional_info
            }
            
            # Log using the logger
            self.logger.debug(json.dumps(log_entry))
                
        except Exception as e:
            logger.error(f"Error logging state: {str(e)}")
            
    def get_recent_states(self, limit: int = 10) -> list:
        """Get the most recent state logs.
        
        Args:
            limit: Maximum number of states to return
            
        Returns:
            List of recent state logs
        """
        try:
            # Get all log files and sort by modification time
            log_files = sorted(
                [f for f in os.listdir(self.log_dir) if f.startswith('state_') and f.endswith('.log')],
                key=lambda x: os.path.getmtime(os.path.join(self.log_dir, x)),
                reverse=True
            )
            
            if not log_files:
                return []
                
            # Read the most recent log file
            with open(os.path.join(self.log_dir, log_files[0]), 'r') as f:
                lines = f.readlines()
                
            states = [json.loads(line) for line in lines[-limit:]]
            return states
            
        except Exception as e:
            logger.error(f"Error getting recent states: {str(e)}")
            return []

    def capture_state_old(self, df: Optional[Union[pd.DataFrame, 'EnhancedDataFrame']], operation: str = "state_check", additional_info: Optional[Dict[str, Any]] = None) -> None:
        """Capture current state of the DataFrame without affecting it"""
        if df is None:
            state = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "status": "no_data"
            }
        else:
            try:
                # Get the underlying DataFrame if EnhancedDataFrame is passed
                data = df.data if hasattr(df, 'data') else df
                
                # Start with basic state information
                state = {
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation,
                    "status": "active",
                    "shape": data.shape,
                    "memory_mb": data.memory_usage(deep=True).sum() / (1024*1024)
                }
                
                # Add flag information if available
                if hasattr(df, '_point_flags') and df._point_flags is not None:
                    state["flag_info"] = {
                        "total_flags": int(np.sum(df._point_flags != DataPointFlag.NORMAL)),
                        "flag_counts": {
                            col: {
                                flag.value: int(np.sum(df._point_flags[:, idx] == flag))
                                for flag in DataPointFlag
                            }
                            for idx, col in enumerate(data.columns)
                        }
                    }
                
                # Add column information
                state["column_info"] = {
                    col: {
                        "dtype": str(data[col].dtype),
                        "null_count": int(data[col].isna().sum()),
                        "unique_count": int(data[col].nunique())
                    } for col in data.columns
                }
                
                # Add numeric column statistics without modifying data
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    state["numeric_stats"] = {
                        col: {
                            "mean": float(data[col].mean()),
                            "std": float(data[col].std()),
                            "min": float(data[col].min()),
                            "max": float(data[col].max())
                        } for col in numeric_cols
                    }
            
            except Exception as e:
                state = {
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation,
                    "status": "error",
                    "error": str(e)
                }
        
        # Add any additional information
        if additional_info:
            state["additional_info"] = additional_info
        
        # Log using the logger
        self.logger.debug(json.dumps(state)) 