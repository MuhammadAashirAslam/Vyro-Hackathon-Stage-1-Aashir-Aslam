"""
Grabpic Configuration
Loads environment variables from .env file.
"""

from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
STORAGE_PATH: str = os.getenv("STORAGE_PATH", "./storage")
SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.4"))
