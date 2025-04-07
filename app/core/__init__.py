"""
Core module for intelligent-biostats.

This module contains the core functionality of the application:
- AI Engine: Handles AI-powered analysis and recommendations
- Data Manager: Manages data loading, transformation, and storage
- Database: Handles persistent storage of analysis history
- Stats Engine: Implements statistical analysis methods

The module follows a modular design pattern where each component
is responsible for a specific aspect of the application's functionality.
"""

from .ai_engine import AIEngine
from .data_manager import DataManager
from .database import AnalysisHistoryDB
from .stats_engine import StatsEngine

__all__ = ['AIEngine', 'DataManager', 'AnalysisHistoryDB', 'StatsEngine']
