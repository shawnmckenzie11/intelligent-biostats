from functools import wraps
import time
import logging
from typing import Dict, Any, Callable
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.timings: Dict[str, float] = {}
        self.thresholds = {
            'file_upload': 5.0,  # seconds
            'data_processing': 3.0,
            'database_operation': 1.0,
            'api_response': 2.0
        }
    
    @contextmanager
    def measure(self, operation_name: str):
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.timings[operation_name] = duration
            if operation_name in self.thresholds and duration > self.thresholds[operation_name]:
                logger.warning(f"Performance warning: {operation_name} took {duration:.2f}s")
            logger.info(f"Operation timing - {operation_name}: {duration:.2f}s")

    def timing_decorator(self, operation_name: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                with self.measure(operation_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

performance_monitor = PerformanceMonitor() 