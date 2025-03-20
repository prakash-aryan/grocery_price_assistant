import os
from dotenv import load_dotenv

"""
Configuration settings for the Grocery Price Assistant

This file manages configuration parameters for:
1. Ollama LLM API settings
2. Currency settings

Database connection parameters are loaded from .env file.
"""

# Load environment variables from .env file if it exists
load_dotenv(override=True)

print(f"ENV MODEL_NAME loaded as: {os.getenv('MODEL_NAME')}")

# Ollama LLM configuration
# -----------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")  # Ollama API endpoint
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-r1:32b")  # LLM model to use
print(f"CONFIG MODEL_NAME set to: {MODEL_NAME}")

# Currency configuration
# ---------------------
CURRENCY = "INR" 
CURRENCY_SYMBOL = "₹"

def get_db_connection():
    """
    Get database connection parameters from environment variables.
    Used by other modules to connect to the database.
    """
    return {
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT")
    }