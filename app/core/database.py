import sqlite3
from datetime import datetime
import json
from typing import List, Dict, Any
import os

class AnalysisHistoryDB:
    def __init__(self, db_path='analysis_history.db'):
        # Get the absolute path to the database
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', db_path)
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        print(f"Database path: {self.db_path}")  # Debug print
        self._init_db()
    
    def _init_db(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        input_file TEXT NOT NULL,
                        modifications TEXT,
                        test_name TEXT NOT NULL,
                        test_details TEXT NOT NULL,
                        date_time TEXT NOT NULL,
                        conclusion TEXT NOT NULL
                    )
                ''')
                conn.commit()
                print("Database initialized successfully")  # Debug print
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
    
    def add_analysis(self, input_file: str, modifications: str, test_name: str, 
                    test_details: Dict[str, Any], conclusion: str) -> int:
        """Add a new analysis record to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO analysis_history 
                    (input_file, modifications, test_name, test_details, date_time, conclusion)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    input_file,
                    modifications,
                    test_name,
                    json.dumps(test_details),
                    datetime.now().isoformat(),
                    conclusion
                ))
                conn.commit()
                print(f"Added analysis record: {test_name}")  # Debug print
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database error while adding analysis: {e}")
            raise
    
    def get_all_analyses(self) -> List[Dict[str, Any]]:
        """Retrieve all analysis records from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, input_file, modifications, test_name, test_details, 
                           date_time, conclusion
                    FROM analysis_history
                    ORDER BY date_time DESC
                ''')
                rows = cursor.fetchall()
                print(f"Retrieved {len(rows)} analysis records")  # Debug print
                
                return [{
                    'id': row[0],
                    'input_file': row[1],
                    'modifications': row[2],
                    'test_name': row[3],
                    'test_details': json.loads(row[4]),
                    'date_time': row[5],
                    'conclusion': row[6]
                } for row in rows]
        except sqlite3.Error as e:
            print(f"Database error while retrieving analyses: {e}")
            raise
    
    def get_analysis_by_id(self, analysis_id: int) -> Dict[str, Any]:
        """Retrieve a specific analysis record by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, input_file, modifications, test_name, test_details, 
                           date_time, conclusion
                    FROM analysis_history
                    WHERE id = ?
                ''', (analysis_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'input_file': row[1],
                        'modifications': row[2],
                        'test_name': row[3],
                        'test_details': json.loads(row[4]),
                        'date_time': row[5],
                        'conclusion': row[6]
                    }
                return None
        except sqlite3.Error as e:
            print(f"Database error while retrieving analysis: {e}")
            raise 