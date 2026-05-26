import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

# Database Configuration
DB_CONFIG = {
    'host': os.environ.get("HOST"),
    'user': os.environ.get("USER"),
    'password': os.environ.get("PASSWORD"), 
    'database': os.environ.get("DATABASE"),
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Create and return database connection"""
    connection = pymysql.connect(**DB_CONFIG)
    return connection



