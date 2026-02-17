# db.py
from mysql.connector import pooling
import threading
import hashlib
from flask import session

connection_pools = {}
pool_lock = threading.Lock()

def sanitize_pool_name(db_name):
    """
    Convert database name to a valid pool name
    Uses MD5 hash for email addresses to ensure uniqueness
    """
    # Check if it looks like an email (contains @)
    if '@' in db_name:
        # Create MD5 hash of the email
        hash_object = hashlib.md5(db_name.encode())
        safe_name = hash_object.hexdigest()[:20]  # Use first 20 chars of hash
    else:
        # For non-email, just replace special chars
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', db_name)
    
    return f"pool_{safe_name}"

def get_db_connection():
    """Get connection - reads database name from SESSION"""
    # Get database name from Flask session
    db_name = session.get('db_name', 'peakers')  # Default to 'peakers'
    
    print(f"🔍 [db.py] Connecting to database: '{db_name}'")
    print(f"   Session ID: {session.sid if hasattr(session, 'sid') else 'No sid'}")
    print(f"   Session keys: {list(session.keys())}")
    
    # Create a safe pool name (for internal use only)
    safe_pool_name = sanitize_pool_name(db_name)
    
    with pool_lock:
        if safe_pool_name not in connection_pools:
            try:
                print(f"🔄 Creating new connection pool for: {db_name}")
                print(f"   Pool name (sanitized): {safe_pool_name}")
                
                pool = pooling.MySQLConnectionPool(
                    pool_name=safe_pool_name,  # Use sanitized name for pool
                    pool_size=3,
                    host="localhost",
                    user="root",
                    password="",
                    database=db_name,  # Use original db_name for actual connection
                )
                connection_pools[safe_pool_name] = pool
                print(f"✅ Created connection pool for database: {db_name}")
            except Exception as e:
                print(f"❌ DB connection failed for '{db_name}': {e}")
                # If default fails, try peakers_pos_test as fallback
                if db_name == 'peakers':
                    print("🔄 Trying fallback database: peakers_pos_test")
                    db_name = 'peakers_pos_test'
                    # Update session for future requests
                    session['db_name'] = db_name
                    return get_db_connection()  # Retry
                raise

        return connection_pools[safe_pool_name].get_connection()