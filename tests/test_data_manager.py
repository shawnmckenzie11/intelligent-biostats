import unittest
from app.core.data_manager import DataManager
import pandas as pd
import numpy as np
import os

class TestDataManager(unittest.TestCase):
    def setUp(self):
        self.df = DataManager()
        
    def test_load_data(self):
        # Create a temporary CSV file
        test_data = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['a', 'b', 'c']
        })
        test_file = 'test_data.csv'
        test_data.to_csv(test_file, index=False)
        
        try:
            # Test loading data
            success, error = self.df.load_data(test_file)
            self.assertTrue(success)
            self.assertIsNone(error)
            self.assertIsNotNone(self.df.data)
            self.assertEqual(len(self.df.data), 3)
            self.assertEqual(list(self.df.data.columns), ['A', 'B'])
            
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)
                
    def test_metadata_initialization(self):
        # Create a temporary CSV file
        test_data = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['a', 'b', 'c']
        })
        test_file = 'test_data.csv'
        test_data.to_csv(test_file, index=False)
        
        try:
            # Load data and check metadata
            success, error = self.df.load_data(test_file)
            self.assertTrue(success)
            
            # Check metadata
            self.assertIn('file_stats', self.df.metadata)
            self.assertIn('column_types', self.df.metadata)
            self.assertIn('data_quality', self.df.metadata)
            
            # Check file stats
            stats = self.df.metadata['file_stats']
            self.assertEqual(stats['rows'], 3)
            self.assertEqual(stats['columns'], 2)
            
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)
                
if __name__ == '__main__':
    unittest.main()
