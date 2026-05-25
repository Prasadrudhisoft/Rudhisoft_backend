import pymysql

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Atul@2002', 
    'database': 'company_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Create and return database connection"""
    connection = pymysql.connect(**DB_CONFIG)
    return connection



