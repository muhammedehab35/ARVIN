# Database Module
"""
Database management module for user authentication and data storage
This module provides database operations for the Abacus FinBot platform.
"""

from .database import *
from .auth import *

__all__ = [
    'create_tables', 'add_test_users', 'get_db', 'User',
    'authenticate_user', 'validate_email', 'validate_name', 
    'get_current_user', 'create_user'
]
