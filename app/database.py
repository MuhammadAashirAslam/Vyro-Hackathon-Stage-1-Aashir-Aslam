"""
Grabpic Database Connection
Simple psycopg2 connection helper using the Supabase connection string.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import DATABASE_URL


def get_conn():
    """Get a new database connection with RealDictCursor for dict-like rows."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
