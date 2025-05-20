import sqlite3
from flask import g, current_app, request
import os
from urllib.parse import urlparse, urljoin

from src.utils.logging_config import logger

# DATABASE_PATH points to 'database.db' located in the 'src' directory,
# consistent with where src/User.py expects it.
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'form_data.db')
_db_dir = os.path.dirname(os.path.abspath(DATABASE_PATH))
try:
    if not os.path.exists(_db_dir):
        os.makedirs(_db_dir, exist_ok=True)
        print(f"[helpers.py] Created DB directory: {_db_dir}")
        try:
            from src.utils.logging_config import logger
            logger.info(f"[helpers.py] Created DB directory: {_db_dir}")
        except Exception:
            pass
except Exception as e:
    print(f"[helpers.py] ERROR: Could not create DB directory {_db_dir}: {e}")
    try:
        from src.utils.logging_config import logger
        logger.error(f"[helpers.py] ERROR: Could not create DB directory {_db_dir}: {e}")
    except Exception:
        pass
    raise

print(f"[helpers.py] Using DATABASE_PATH: {os.path.abspath(DATABASE_PATH)}")
try:
    from src.utils.logging_config import logger
    logger.info(f"[helpers.py] Using DATABASE_PATH: {os.path.abspath(DATABASE_PATH)}")
except Exception:
    pass

# --- Ensure Unique Constraint for filled_pdf_filename ---
def ensure_filled_pdf_filename_unique():
    db = get_db()
    cursor = db.cursor()
    abs_db_path = os.path.abspath(DATABASE_PATH)
    print(f"[ensure_filled_pdf_filename_unique] Using DATABASE_PATH: {abs_db_path}")
    try:
        from src.utils.logging_config import logger
        logger.info(f"[ensure_filled_pdf_filename_unique] Using DATABASE_PATH: {abs_db_path}")
    except Exception:
        pass
    # Check if unique index exists
    cursor.execute("PRAGMA index_list('claims')")
    indexes = cursor.fetchall()
    found = False
    for idx in indexes:
        if 'filled_pdf_filename' in idx[1] and idx[2]:
            found = True
    if not found:
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_claims_filled_pdf_filename ON claims(filled_pdf_filename)")
            db.commit()
        except Exception as e:
            print(f"Could not create unique index for filled_pdf_filename: {e}")

# --- Force drop and recreate claims table for debugging ---
def force_recreate_claims_table(DB_SCHEMA, logger=None):
    db = get_db()
    cursor = db.cursor()
    if logger:
        logger.info("force_recreate_claims_table called.")
    else:
        print("force_recreate_claims_table called.")
    try:
        cursor.execute("DROP TABLE IF EXISTS claims")
        if logger:
            logger.info("Dropped existing 'claims' table.")
        else:
            print("Dropped existing 'claims' table.")
        if not DB_SCHEMA or not isinstance(DB_SCHEMA, list):
            msg = "DB_SCHEMA is missing or not a list. Cannot recreate claims table."
            if logger:
                logger.error(msg)
            print(msg)
            return
        columns_sql = ', '.join(["id INTEGER PRIMARY KEY AUTOINCREMENT"] + DB_SCHEMA)
        create_table_sql = f"CREATE TABLE claims ({columns_sql})"
        cursor.execute(create_table_sql)
        db.commit()
        if logger:
            logger.info("Recreated 'claims' table with full DB_SCHEMA.")
        else:
            print("Recreated 'claims' table with full DB_SCHEMA.")
    except Exception as e:
        if logger:
            logger.error(f"Error force-recreating 'claims' table: {e}")
        print(f"Error force-recreating 'claims' table: {e}")

# --- PHONE NUMBER HELPERS ---
def normalize_phone(phone):
    """
    Normalize a phone number to digits only. Returns a string of digits, e.g. '3855556123'.
    """
    import re
    if not phone:
        return ''
    return re.sub(r'\D', '', str(phone))

def format_phone(phone_digits):
    """
    Format a 10-digit phone string as (XXX)XXX-XXXX. If not 10 digits, return as is.
    """
    phone_digits = normalize_phone(phone_digits)
    if len(phone_digits) == 10:
        return f"({phone_digits[:3]}){phone_digits[3:6]}-{phone_digits[6:]}"
    return phone_digits

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def create_tables_if_not_exist(logger=None):
    db = get_db()
    cursor = db.cursor()
    try:
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        if logger:
            logger.info("Users table checked/created.")
        
        # Placeholder for other tables you might add later
        # cursor.execute('''
        #     CREATE TABLE IF NOT EXISTS form_submissions (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         -- define your columns for form data
        #     )
        # ''')
        # if logger:
        #     logger.info("Form_submissions table checked/created.")

        db.commit()
    except sqlite3.Error as e:
        log_message = f"Database error during table creation: {e}"
        if logger:
            logger.error(log_message)
        else:
            print(log_message) # Fallback if no logger
    finally:
        # The database connection is managed by get_db and close_db (via app context)
        pass

def init_db(logger=None):
    log_message_start = "Initializing database..."
    log_message_end = "Database initialization complete."
    if logger:
        logger.info(log_message_start)
    else:
        print(log_message_start) # Fallback if no logger
        
    create_tables_if_not_exist(logger)
    
    if logger:
        logger.info(log_message_end)
    else:
        print(log_message_end) # Fallback if no logger

def init_app_db(app):
    """Registers database functions with the Flask app."""
    app.teardown_appcontext(close_db)
    # If you want a command-line interface (CLI) command like `flask init-db`
    # you would add it here using app.cli.add_command.
    # For example:
    # import click
    # @app.cli.command('init-db')
    # def init_db_command():
    #     """Clear existing data and create new tables."""
    #     init_db(app.logger) # or pass current_app.logger
    #     click.echo('Initialized the database.')

def is_safe_url(target):
    """Checks if a redirect target URL is safe."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc
