import logging
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

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
        
    def capture_state(self, df: Optional[pd.DataFrame], operation: str = "state_check") -> None:
        """Capture current state of the DataFrame without affecting it"""
        if df is None:
            state = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "status": "no_data"
            }
        else:
            try:
                state = {
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation,
                    "status": "active",
                    "shape": df.shape,
                    "memory_mb": df.memory_usage(deep=True).sum() / (1024*1024),
                    "column_info": {
                        col: {
                            "dtype": str(df[col].dtype),
                            "null_count": int(df[col].isna().sum()),
                            "unique_count": int(df[col].nunique())
                        } for col in df.columns
                    }
                }
                
                # Add numeric column statistics without modifying data
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    state["numeric_stats"] = {
                        col: {
                            "mean": float(df[col].mean()),
                            "std": float(df[col].std()),
                            "min": float(df[col].min()),
                            "max": float(df[col].max())
                        } for col in numeric_cols
                    }
            
            except Exception as e:
                state = {
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation,
                    "status": "error",
                    "error": str(e)
                }
        
        # Log the state
        self.logger.debug(json.dumps(state)) 