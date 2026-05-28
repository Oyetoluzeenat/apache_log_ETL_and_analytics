import sqlite3
import logging

logger = logging.getLogger(__name__)

def init_db(db_path="logs.db"):
    """Creates the SQLite database schema with logs and errors tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Structured Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            timestamp TEXT,
            method TEXT,
            resource_path TEXT,
            protocol TEXT,
            status_code INTEGER,
            bytes_sent INTEGER,
            referrer TEXT,
            user_agent TEXT
        )
    """)
    
    # 2. Malformed / Unparsed Lines Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_line TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized successfully at '{db_path}'.")

def load_data_to_db(parsed_records, malformed_records, db_path="logs.db"):
    """Inserts processed rows into logs table and raw strings into errors table using transactions."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inserted_logs = 0
    inserted_errors = 0
    
    try:
        # Load structured records
        if parsed_records:
            log_query = """
                INSERT INTO logs (ip, timestamp, method, resource_path, protocol, status_code, bytes_sent, referrer, user_agent)
                VALUES (:ip, :timestamp, :method, :resource_path, :protocol, :status_code, :bytes_sent, :referrer, :user_agent)
            """
            cursor.executemany(log_query, parsed_records)
            inserted_logs = len(parsed_records)
            
        # Load malformed records
        if malformed_records:
            error_query = "INSERT INTO errors (raw_line, reason) VALUES (?, ?)"
            cursor.executemany(error_query, malformed_records)
            inserted_errors = len(malformed_records)
            
        conn.commit()
        logger.info(f"Load Phase Success: Loaded {inserted_logs} valid logs and {inserted_errors} error records to storage.")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Load Phase Failure: Transactions rolled back due to error: {e}")
        raise e
    finally:
        conn.close()