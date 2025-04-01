import numpy as np
from scipy import stats
import pandas as pd
from typing import Dict, Any, Union, List, Tuple
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

class StatsEngine:
    """Implements statistical analyses for biological data."""
    
    def __init__(self):
        """Initialize the Stats Engine with necessary imports and configurations."""
        # Ensure single initialization
        if not hasattr(self, '_initialized'):
            # Import required packages
            self._import_required_packages()
            
            self.available_tests = {
                't_test': self.perform_t_test,
                'anova': self.perform_anova,
                'correlation': self.perform_correlation
            }
            
            self._initialized = True
    
    def _import_required_packages(self):
        """Import all required packages for statistical analysis."""
        try:
            global np, stats, pd
            import numpy as np
            from scipy import stats
            import pandas as pd
        except ImportError as e:
            print(f"Error importing required packages: {str(e)}")
            raise

    def perform_t_test(self, data: pd.DataFrame, group1: np.ndarray, group2: np.ndarray) -> Dict[str, Any]:
        """Perform t-test analysis."""
        try:
            result = stats.ttest_ind(group1, group2)
            return {
                'statistic': result.statistic,
                'p_value': result.pvalue
            }
        except Exception as e:
            print(f"Error performing t-test: {str(e)}")
            raise
        
    def perform_anova(self, data: pd.DataFrame, groups: List[np.ndarray]) -> Dict[str, Any]:
        """Perform ANOVA analysis."""
        try:
            result = stats.f_oneway(*groups)
            return {
                'statistic': result.statistic,
                'p_value': result.pvalue
            }
        except Exception as e:
            print(f"Error performing ANOVA: {str(e)}")
            raise
        
    def perform_correlation(self, data: pd.DataFrame, var1: np.ndarray, var2: np.ndarray) -> Dict[str, Any]:
        """Perform correlation analysis."""
        try:
            result = stats.pearsonr(var1, var2)
            return {
                'correlation': result.statistic,
                'p_value': result.pvalue
            }
        except Exception as e:
            print(f"Error performing correlation: {str(e)}")
            raise
