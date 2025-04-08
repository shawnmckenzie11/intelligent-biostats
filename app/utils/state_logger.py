import logging
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union
from app.core.enums import DataPointFlag

class StateLogger:
    def __init__(self, log_dir: str = "debug_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger('state_logger')
        self.logger.setLevel(logging.DEBUG)
        
        # Create a file handler
        log_file = self.log_dir / 'state_log.jsonl'
        handler = logging.FileHandler(str(log_file), mode='a')
        handler.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)
        
    def capture_state(self, df: Optional[Union[pd.DataFrame, 'EnhancedDataFrame']], operation: str = "state_check", additional_info: Optional[Dict[str, Any]] = None) -> None:
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
        
        # Log the state
        self.logger.debug(json.dumps(state)) 