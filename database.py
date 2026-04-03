import os
from mysql.connector import pooling
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment credentials
load_dotenv()

# Initialize the connection pool globally
try:
    db_pool = pooling.MySQLConnectionPool(
        pool_name="sikap_ai_pool",
        pool_size=5,             # Maintain 5 active connections in memory
        pool_reset_session=True, # Wipes temporary session variables upon return
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )
    print("MySQL Connection Pool Initialized Successfully.")
except Error as e:
    print(f"Error initializing MySQL Pool: {e}")
    db_pool = None

def get_db_connection():
    """
    Dependency generator. Borrows a connection for the request and guarantees 
    it is returned to the pool afterward, even if an error occurs.
    """
    if not db_pool:
        raise Exception("Database pool is offline.")
    
    connection = db_pool.get_connection()
    try:
        yield connection
    finally:
        # This does not destroy the TCP link. It returns it to the pool.
        connection.close()