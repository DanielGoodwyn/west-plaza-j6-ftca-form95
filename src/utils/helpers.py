import sqlite3
from flask import g, current_app, request
import os
from urllib.parse import urlparse, urljoin

from src.utils.logging_config import logger

# DATABASE_PATH points to 'database.db' located in the 'src' directory,
# consistent with where src/User.py expects it.
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'database.db')

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
