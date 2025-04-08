from enum import Enum

class DataPointFlag(Enum):
    """Enum for data point flags"""
    NORMAL = "normal"
    OUTLIER = "outlier"
    MISSING = "missing"
    UNEXPECTED_TYPE = "unexpected_type" 