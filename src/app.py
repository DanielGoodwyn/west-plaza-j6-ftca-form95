import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# # Path hack for direct script execution and relative imports
# if __name__ == '__main__' and __package__ is None:
#     parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     if parent_dir not in sys.path:
#         sys.path.insert(0, parent_dir)
#     # Attempt to set the package context if running as a script directly
#     # This helps Python resolve relative imports like '.forms' when 'src.app' is run.
#     # This block is primarily for the temporary direct execution for DB setup.
#     __package__ = "src"

from src.utils.logging_config import setup_logging
setup_logging(log_file='app.log')
import sqlite3
import os
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, current_app, g, Response, session, send_from_directory
from flask_session import Session
from fillpdf import fillpdfs
import re
import io
import csv
from unicodedata import normalize
from werkzeug.utils import secure_filename
import pytz # Added for timezone conversion
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user # Added for Flask-Login
from werkzeug.security import generate_password_hash, check_password_hash # Ensuring this is present
from werkzeug.exceptions import abort

from src.forms import LoginForm # Import the LoginForm (absolute import for direct execution)
from dotenv import load_dotenv # Added

load_dotenv() # Added: Load .env file from project root

# Import utility functions
from src.utils.pdf_filler import fill_sf95_pdf, DEFAULT_VALUES as PDF_FILLER_DEFAULTS
from src.utils.helpers import get_db, create_tables_if_not_exist, is_safe_url, init_db, init_app_db, normalize_phone, format_phone, ensure_filled_pdf_filename_unique, force_recreate_claims_table # Added phone helpers and unique constraint
from src.utils.logging_config import setup_logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8') # Use environment variable or default
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session/' # Ensure this directory exists and is writable
app.config['SESSION_COOKIE_DOMAIN'] = False  # Let Flask/Werkzeug decide for localhost
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Try 'Lax' first, may try 'None' if needed
app.config['SESSION_COOKIE_SECURE'] = False  # for localhost be False for localhost HTTP
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['FILLED_FORMS_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'filled_forms')
app.config['APPLICATION_ROOT'] = '/west-plaza-lawsuit' # Added
app.debug = True  # Enable debug mode for detailed error output (disable in production)

# --- Database Schema (needed by create_tables_if_not_exist) ---
DB_SCHEMA = [
    'field1_agency TEXT',
    'field2_name TEXT',
    'field2_address TEXT',
    'field2_city TEXT',
    'field2_state TEXT',
    'field2_zip TEXT',
    'field3_type_employment TEXT',
    'field_pdf_4_dob TEXT',
    'field_pdf_5_marital_status TEXT',
    'field6_checkbox_military TEXT',
    'field7_checkbox_civilian TEXT',
    'field8_basis_of_claim TEXT',
    'field9_property_damage_description TEXT',
    'field10_nature_of_injury TEXT',
    'field11_witness_name_1 TEXT',
    'field11_witness_address_1 TEXT',
    'field11_witness_name_2 TEXT',
    'field11_witness_address_2 TEXT',
    'field12a_property_damage_amount TEXT',
    'field12b_personal_injury_amount TEXT',
    'field12c_wrongful_death_amount TEXT',
    'field12d_total_claim_amount TEXT',
    'field13a_signature TEXT',
    'field_pdf_13b_phone TEXT',
    'field14_date_signed TEXT',
    'user_email_address TEXT',
    'supplemental_question_1_capitol_experience TEXT',
    'supplemental_question_2_injuries_damages TEXT',
    'supplemental_question_3_entry_exit_time TEXT',
    'supplemental_question_4_inside_capitol_details TEXT',
    'filled_pdf_filename TEXT UNIQUE NOT NULL',
    'field17_signature_of_claimant TEXT',
    'field18_date_of_signature TEXT',
    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
]

# Ensure the data directory exists before DB access
_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
if not os.path.exists(_data_dir):
    os.makedirs(_data_dir, exist_ok=True)


# Ensure unique constraint for filled_pdf_filename (must be in app context)
def enforce_unique_constraint():
    with app.app_context():
        ensure_filled_pdf_filename_unique()
enforce_unique_constraint()
# Ensure session directory exists
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    try:
        os.makedirs(app.config['SESSION_FILE_DIR'])
        app.logger.info(f"Created session directory: {app.config['SESSION_FILE_DIR']}")
    except Exception as e:
        app.logger.error(f"Error creating session directory {app.config['SESSION_FILE_DIR']}: {e}")
        # Decide if this error is critical enough to raise

# Ensure filled forms directory exists
if not os.path.exists(app.config['FILLED_FORMS_DIR']):
    try:
        os.makedirs(app.config['FILLED_FORMS_DIR'])
        app.logger.info(f"Created filled forms directory: {app.config['FILLED_FORMS_DIR']}")
    except Exception as e:
        app.logger.error(f"Error creating filled forms directory {app.config['FILLED_FORMS_DIR']}: {e}")
        # Decide if this error is critical enough to raise

# Call init_app_db to register teardown context
init_app_db(app)

Session(app) # Initialize Flask-Session

# --- Configuration (Constants needed before initialization logic) ---
from src.utils.helpers import DATABASE_PATH
DATABASE = DATABASE_PATH
PDF_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'sf95.pdf') # Corrected template filename

# --- Database Schema (needed by create_tables_if_not_exist) ---
DB_SCHEMA = [
    'field1_agency TEXT',
    'field2_name TEXT',
    'field2_address TEXT',
    'field2_city TEXT',
    'field2_state TEXT',
    'field2_zip TEXT',
    'field3_type_employment TEXT',
    'field_pdf_4_dob TEXT',
    'field_pdf_5_marital_status TEXT',
    'field6_checkbox_military TEXT',
    'field7_checkbox_civilian TEXT',
    'field8_basis_of_claim TEXT',
    'field9_property_damage_description TEXT',
    'field10_nature_of_injury TEXT',
    'field11_witness_name_1 TEXT',
    'field11_witness_address_1 TEXT',
    'field11_witness_name_2 TEXT',
    'field11_witness_address_2 TEXT',
    'field12a_property_damage_amount TEXT',
    'field12b_personal_injury_amount TEXT',
    'field12c_wrongful_death_amount TEXT',
    'field12d_total_claim_amount TEXT',
    'field13a_signature TEXT',
    'field_pdf_13b_phone TEXT',
    'field14_date_signed TEXT',
    'user_email_address TEXT',
    'supplemental_question_1_capitol_experience TEXT',
    'supplemental_question_2_injuries_damages TEXT',
    'supplemental_question_3_entry_exit_time TEXT',
    'supplemental_question_4_inside_capitol_details TEXT',
    'filled_pdf_filename TEXT',
    'field17_signature_of_claimant TEXT',
    'field18_date_of_signature TEXT',
    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
]

# --- Database Helper Functions (defined before use in initialization) ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def table_exists(cursor, table_name, logger):
    logger.debug(f"Checking if table '{table_name}' exists.")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    exists = cursor.fetchone() is not None
    logger.debug(f"Table '{table_name}' exists: {exists}")
    return exists

def create_tables_if_not_exist(logger): # Accept logger
    logger.info("Entered create_tables_if_not_exist function.")
    db = get_db()
    cursor = db.cursor()
    logger.info("Successfully obtained DB cursor.")

    table_name = 'claims'
    logger.info(f"Checking '{table_name}' table. Exists: {table_exists(cursor, table_name, logger)}")

    if not table_exists(cursor, table_name, logger):
        columns_sql_parts = ["id INTEGER PRIMARY KEY AUTOINCREMENT"] + DB_SCHEMA
        columns_sql = ', '.join(columns_sql_parts)
        create_table_sql = f"CREATE TABLE {table_name} ({columns_sql})"
        logger.info(f"Creating '{table_name}' table with SQL: {create_table_sql}")
        cursor.execute(create_table_sql)
        db.commit()
        logger.info(f"'{table_name}' table created successfully.")
    else:
        logger.info(f"'{table_name}' table exists. Checking for missing columns based on DB_SCHEMA.")
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns_info = cursor.fetchall()
        existing_column_names = [col_info['name'] for col_info in existing_columns_info]
        logger.info(f"Existing columns in '{table_name}': {existing_column_names}")
        logger.info(f"DB_SCHEMA to check against: {DB_SCHEMA}")

        schema_column_definitions = {}
        for col_def_str in DB_SCHEMA:
            col_name = col_def_str.strip().split(' ')[0]
            schema_column_definitions[col_name] = col_def_str.strip()
        logger.info(f"Parsed schema column definitions from DB_SCHEMA: {schema_column_definitions}")

        columns_added_count = 0
        for schema_col_name, full_col_definition in schema_column_definitions.items():
            if schema_col_name not in existing_column_names:
                col_definition_for_alter = full_col_definition
                if schema_col_name in ['created_at', 'updated_at'] and 'DEFAULT CURRENT_TIMESTAMP' in full_col_definition.upper():
                    col_definition_for_alter = f"{schema_col_name} TIMESTAMP"
                    logger.info(f"Column '{schema_col_name}' is missing. Will be added with simplified definition for ALTER: '{col_definition_for_alter}'")
                else:
                    logger.info(f"Column '{schema_col_name}' is missing. Attempting to add with definition: '{full_col_definition}'")
                
                try:
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_definition_for_alter}"
                    logger.info(f"Executing ALTER TABLE SQL: {alter_sql}")
                    cursor.execute(alter_sql)
                    db.commit()
                    logger.info(f"Successfully added column '{schema_col_name}' to '{table_name}'.")
                    columns_added_count += 1
                except sqlite3.Error as e:
                    logger.error(f"Error adding column {full_col_definition} to '{table_name}' table: {e}. Existing columns were: {existing_column_names}")
        
        if columns_added_count > 0:
            logger.info(f"Added {columns_added_count} missing column(s) to '{table_name}'.")
        else:
            logger.info(f"'{table_name}' table schema appears up to date with DB_SCHEMA. No columns were added.")

    # Create 'users' table if it doesn't exist
    if not table_exists(cursor, 'users', logger):
        create_users_table_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        """
        logger.info("Creating 'users' table.")
        cursor.execute(create_users_table_sql)
        # Optionally, create a default admin user here if one doesn't exist
        # For simplicity, we'll handle admin user creation separately for now or via a script.
        logger.info("'users' table created successfully.")
    else:
        logger.info("'users' table already exists.")

    logger.info("Exiting create_tables_if_not_exist function.")

# --- User Model ---
class User(UserMixin):
    def __init__(self, id, username, password_hash, role='user'):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def is_admin(self):
        return self.role in ('admin', 'superadmin')

    def is_superadmin(self):
        return self.role == 'superadmin'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_username(username):
        db = get_db()
        cursor = db.cursor()
        username_lower = username.lower()
        user_data = cursor.execute('SELECT * FROM users WHERE LOWER(username) = ?', (username_lower,)).fetchone()
        if user_data:
            role = user_data['role'] if 'role' in user_data.keys() else 'user'
            return User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'], role=role)
        return None

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        cursor = db.cursor()
        user_data = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user_data:
            role = user_data['role'] if 'role' in user_data.keys() else 'user'
            return User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'], role=role)
        return None

    @staticmethod
    def create_user(username, password, role='user'):
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)', (username, generate_password_hash(password), role))
            db.commit()
            return True
        except sqlite3.IntegrityError as e:
            current_app.logger.error(f"User creation failed for {username}: {e}")
            return None
        except Exception as e:
            current_app.logger.error(f"Unexpected error during user creation for {username}: {e}")
            return None

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # The route name for the login page
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

# Centralized app initialization function
def initialize_application_internals(flask_app_object):
    if flask_app_object:
        # 0. Setup logging (File and Console)
        # Use a log file relative to the current file's directory (project root on server)
        log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'debugging-logs.txt')
        log_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_dir) and log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Configure file handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO) # Log INFO and above to file
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        flask_app_object.logger.addHandler(file_handler)

        # Configure console handler (to still see logs in terminal)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG) # Show DEBUG and above in console
        console_handler.setFormatter(formatter) # Can use the same or different formatter
        flask_app_object.logger.addHandler(console_handler)

        # Set the app logger's level (if not set by default)
        # This ensures that messages of this level and above are processed by handlers.
        flask_app_object.logger.setLevel(logging.DEBUG) # Process all messages from DEBUG upwards
        
        flask_app_object.logger.info("Custom logging initialized for file and console.")

    # 1. Ensure necessary directories exist (e.g., for SQLite DB, filled forms)
    data_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    if not os.path.exists(data_dir_path):
        try:
            os.makedirs(data_dir_path)
            if flask_app_object:
                flask_app_object.logger.info(f"Created data directory: {data_dir_path}")
            else:
                print(f"Created data directory: {data_dir_path}") # Fallback if no app object
        except Exception as e:
            if flask_app_object:
                flask_app_object.logger.error(f"Error creating data directory {data_dir_path}: {e}")
            else:
                print(f"Error creating data directory {data_dir_path}: {e}") # Fallback
            # Decide if this error is critical enough to raise

    # 2. Database schema check/initialization (needs application context)
    if flask_app_object:
        with flask_app_object.app_context():
            try:
                # Pass the Flask app's logger to the database function
                create_tables_if_not_exist(flask_app_object.logger) # This logger will now use the handlers we set up
                flask_app_object.logger.info("Database schema checked/initialized successfully (within app context).")
            except Exception as e:
                flask_app_object.logger.error(f"Error during database setup in app context: {e}")
                # Depending on the app's needs, you might want to raise this error
                # to prevent the app from starting with a non-functional database.
                # raise # Uncomment if startup should fail on DB error
    else:
        # Handle case where flask_app_object is None, if that's possible in your flow
        print("initialize_application_internals: flask_app_object is None, skipping DB and advanced logging setup.")

# Call the centralized initialization function AFTER all helpers and constants are defined
initialize_application_internals(app)

# --- Utility Functions (like slugify, PDF field mapping, etc. - can be here or imported) ---

import traceback

# --- GLOBAL ERROR HANDLER ---
@app.errorhandler(Exception)
def handle_unhandled_exception(e):
    # Log to Flask logger
    app.logger.error(f"[GLOBAL ERROR HANDLER] Unhandled Exception: {e}\n{traceback.format_exc()}")
    # Attempt to log to file with 1000 line limit (same as your custom function)
    LOG_PATH = 'debugging-logs.txt'
    MAX_LINES = 1000
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        lines.append(f"[GLOBAL ERROR HANDLER] {e}\n{traceback.format_exc()}\n")
        lines = lines[-MAX_LINES:]
        with open(LOG_PATH, 'w') as f:
            f.writelines(lines)
    except Exception as log_exc:
        app.logger.error(f"[GLOBAL ERROR HANDLER] Failed to log exception to file: {log_exc}")
    return "Internal Server Error", 500

# (Ensuring these are also defined before routes if routes use them directly at import time)

# Helper function for slugifying text
def slugify(text):
    """
    Generate a slug from a string.
    Example: "Héllo World!" -> "hello-world"
    """
    if not text:
        return "default-claimant" # Fallback for empty text
    text = str(text)
    # Normalize to decompose combined characters, then encode to ASCII ignoring errors, then decode back to string.
    # This effectively removes accents and other non-ASCII characters.
    text = normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()  # Remove non-alphanumeric (except hyphens and spaces)
    text = re.sub(r'[-\s]+', '-', text)  # Replace spaces and consecutive hyphens with a single hyphen
    if not text: # If text becomes empty after sanitization (e.g. was just "!!!")
        return "default-claimant"
    return text

# --- Constants for Admin View and CSV Export --- 
DESIRED_COLUMNS_ORDER_AND_HEADERS = [
    ('filled_pdf_filename', 'ID'),
    ('field2_name', 'Claimant Name'),
    ('user_email_address', 'Email Address'),
    ('field_pdf_13b_phone', 'Phone Number'),
    ('field8_basis_of_claim', 'Basis of Claim'),
    ('field10_nature_of_injury', 'Nature of Injury'),
    ('supplemental_question_1_capitol_experience', 'Capitol Experience'),
    ('supplemental_question_2_injuries_damages', 'Injuries/Damages'),
    ('supplemental_question_3_entry_exit_time', 'Entry/Exit Time'),
    ('supplemental_question_4_inside_capitol_details', 'Inside Capitol Details'),
    ('field12a_property_damage_amount', 'Property Damage Amount'),
    ('field12b_personal_injury_amount', 'Personal Injury Amount'),
    ('field12c_wrongful_death_amount', 'Wrongful Death Amount'),
    ('field12d_total_claim_amount', 'Total Claim Amount'),
    ('field13a_signature', 'Signature'),
    ('field3_type_employment', 'Type of Employment'),
    ('field_pdf_5_marital_status', 'Marital Status'),
    ('field2_address', 'Street Address'),
    ('field2_city', 'City'),
    ('field2_state', 'State'),
    ('field2_zip', 'Zip Code'),
    ('created_at', 'Date and Time Created'),
    ('field18_date_of_signature', 'Date and Time Signed'), # Added for date signed
]

# --- Timezone Helper --- 
def format_datetime_for_display(utc_datetime_input, target_tz_str='America/New_York'):
    """Formats a UTC datetime string or object for display in a target timezone.
    Handles 'YYYY-MM-DDTHH:MM' and 'YYYY-MM-DD HH:MM:SS' formats, and datetime objects.
    Returns 'MM/DD/YYYY hh:mm AM/PM' or 'Pending' if input is invalid/None.
    """
    if not utc_datetime_input: # Handles None, empty string
        return "Pending"

    current_app.logger.info(f"format_datetime_for_display: Received input '{utc_datetime_input}' of type {type(utc_datetime_input)}")

    try:
        parsed_dt = None
        if isinstance(utc_datetime_input, datetime): # Check if input is already a datetime object
            current_app.logger.info(f"format_datetime_for_display: Input is already a datetime object: {utc_datetime_input}. Assuming naive UTC.")
            parsed_dt = utc_datetime_input # Use it directly
        elif isinstance(utc_datetime_input, str):
            utc_datetime_str = utc_datetime_input # It's a string, proceed with parsing
            if 'T' in utc_datetime_str:
                current_app.logger.info(f"format_datetime_for_display: Detected 'T' in '{utc_datetime_str}', attempting T-specific parsing.")
                try:
                    parsed_dt = datetime.strptime(utc_datetime_str, '%Y-%m-%dT%H:%M:%S')
                    current_app.logger.info(f"format_datetime_for_display: Parsed with 'T' and seconds: {parsed_dt}")
                except ValueError:
                    current_app.logger.info(f"format_datetime_for_display: Failed 'T' with seconds, trying 'T' without seconds for '{utc_datetime_str}'.")
                    parsed_dt = datetime.strptime(utc_datetime_str, '%Y-%m-%dT%H:%M')
                    current_app.logger.info(f"format_datetime_for_display: Parsed with 'T' without seconds: {parsed_dt}")
            else:
                current_app.logger.info(f"format_datetime_for_display: No 'T' in '{utc_datetime_str}', attempting non-T parsing.")
                try:
                    current_app.logger.info(f"format_datetime_for_display: Trying to parse '{utc_datetime_str}' with milliseconds...")
                    parsed_dt = datetime.strptime(utc_datetime_str, '%Y-%m-%d %H:%M:%S.%f')
                    current_app.logger.info(f"format_datetime_for_display: Parsed non-T with milliseconds: {parsed_dt}")
                except ValueError as e_ms:
                    current_app.logger.info(f"format_datetime_for_display: Failed non-T with milliseconds for '{utc_datetime_str}': {e_ms}. Trying without milliseconds...")
                    try:
                        parsed_dt = datetime.strptime(utc_datetime_str, '%Y-%m-%d %H:%M:%S')
                        current_app.logger.info(f"format_datetime_for_display: Parsed non-T without milliseconds: {parsed_dt}")
                    except ValueError as e_no_ms:
                        current_app.logger.error(f"format_datetime_for_display: Failed to parse non-T ('{utc_datetime_str}') without milliseconds either: {e_no_ms}")
                        raise # Re-raise to hit the outer exception handler
        else:
            current_app.logger.error(f"format_datetime_for_display: Input '{utc_datetime_input}' is neither a string nor a datetime object. Type: {type(utc_datetime_input)}")
            return str(utc_datetime_input) # Fallback for unexpected types

        if parsed_dt is None:
            current_app.logger.error(f"format_datetime_for_display: parsed_dt is None after attempting to process input '{utc_datetime_input}'. This should not happen.")
            return str(utc_datetime_input) # Fallback
            
        current_app.logger.info(f"format_datetime_for_display: Successfully processed input. Parsed datetime: {parsed_dt}. Localizing to UTC.")
        utc_dt_aware = pytz.utc.localize(parsed_dt)
        current_app.logger.info(f"format_datetime_for_display: Localized to UTC: {utc_dt_aware}. Converting to target timezone '{target_tz_str}'.")
        target_tz = pytz.timezone(target_tz_str)
        target_dt_aware = utc_dt_aware.astimezone(target_tz)
        formatted_output = target_dt_aware.strftime('%m/%d/%Y %I:%M %p')
        current_app.logger.info(f"format_datetime_for_display: Converted to target timezone: {target_dt_aware}. Formatted output: {formatted_output}")
        return formatted_output
    except Exception as e:
        current_app.logger.error(f"format_datetime_for_display: General error converting datetime input '{utc_datetime_input}': {e}")
        return str(utc_datetime_input) # Return string representation of original on error

# --- Admin Required Decorator ---
from flask_login import login_required, current_user
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kws):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kws)
    return decorated_function

# --- Routes ---

@app.route('/superadmin')
@login_required
@admin_required
def superadmin():
    db = get_db()
    cursor = db.cursor()
    users = cursor.execute('SELECT id, username, role FROM users').fetchall()
    users = [dict(user) for user in users]
    return render_template('superadmin.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if not current_user.is_superadmin():
        abort(403)
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password']
        role = request.form['role']
        if not username or not password or role not in ('user', 'admin', 'superadmin'):
            flash('Invalid input.', 'danger')
            return redirect(url_for('add_user'))
        if User.get_by_username(username):
            flash('Username already exists.', 'danger')
            return redirect(url_for('add_user'))
        User.create_user(username, password, role)
        flash('User created.', 'success')
        return redirect(url_for('superadmin'))
    return render_template('edit_user.html', user=None, action='Add')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    if not current_user.is_superadmin():
        abort(403)
    db = get_db()
    cursor = db.cursor()
    user_data = cursor.execute('SELECT id, username, role FROM users WHERE id=?', (user_id,)).fetchone()
    if not user_data:
        flash('User not found.', 'danger')
        return redirect(url_for('superadmin'))
    if request.method == 'POST':
        role = request.form['role']
        if role not in ('user', 'admin', 'superadmin'):
            flash('Invalid role.', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))
        cursor.execute('UPDATE users SET role=? WHERE id=?', (role, user_id))
        db.commit()
        flash('User updated.', 'success')
        return redirect(url_for('superadmin'))
    return render_template('edit_user.html', user=user_data, action='Edit')

@app.route('/delete_user/<int:user_id>', methods=['POST', 'GET'])
@login_required
@admin_required
def delete_user(user_id):
    if not current_user.is_superadmin():
        abort(403)
    db = get_db()
    cursor = db.cursor()
    user_data = cursor.execute('SELECT username FROM users WHERE id=?', (user_id,)).fetchone()
    if not user_data or user_data['username'] == current_user.username:
        flash('Cannot delete this user.', 'danger')
        return redirect(url_for('superadmin'))
    cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
    db.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('superadmin'))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kws):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kws)
    return decorated_function

@app.route('/admin/edit/<int:claim_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_claim(claim_id):
    db = get_db()
    cursor = db.cursor()
    # Fetch the claim data by ID
    claim = cursor.execute('SELECT * FROM claims WHERE id = ?', (claim_id,)).fetchone()
    if not claim:
        abort(404, description="Claim not found.")
    if request.method == 'POST':
        # Update claim with submitted data
        form_data = dict(request.form)
        # Normalize phone number if present
        if 'field_pdf_13b_phone' in form_data:
            form_data['field_pdf_13b_phone'] = normalize_phone(form_data['field_pdf_13b_phone'])
        # --- Recalculate total claim amount (12d) from 12a, 12b, 12c ---
        try:
            prop_dam = float(form_data.get('field12a_property_damage_amount', 0) or 0)
            pers_inj = float(form_data.get('field12b_personal_injury_amount', 0) or 0)
            wrong_death = float(form_data.get('field12c_wrongful_death_amount', 0) or 0)
            total_claim = prop_dam + pers_inj + wrong_death
            form_data['field12d_total_claim_amount'] = f"{total_claim:.2f}"
        except Exception as e:
            current_app.logger.error(f"EDIT_CLAIM: Error recalculating total claim amount: {e}")
            # Optionally: fallback to original value or clear
            form_data['field12d_total_claim_amount'] = form_data.get('field12d_total_claim_amount', '')
        update_fields = []
        update_values = []
        for key in claim.keys():
            if key == 'id':
                continue
            if key in form_data:
                update_fields.append(f"{key} = ?")
                update_values.append(form_data[key])
            else:
                update_fields.append(f"{key} = ?")
                update_values.append(claim[key])
        update_values.append(claim_id)
        update_sql = f"UPDATE claims SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(update_sql, tuple(update_values))
        db.commit()
        # --- Optionally regenerate PDF here if needed ---
        # from src.utils.pdf_filler import fill_sf95_pdf
        # pdf_data_for_filling = map_form_data_to_pdf_fields(form_data)
        # output_pdf_path = os.path.join(current_app.config['FILLED_FORMS_DIR'], claim['filled_pdf_filename'])
        # try:
        #     fill_sf95_pdf(pdf_data_for_filling, PDF_TEMPLATE_PATH, output_pdf_path)
        #     current_app.logger.info(f"EDIT_CLAIM: PDF regenerated after edit: {output_pdf_path}")
        # except Exception as e:
        #     current_app.logger.error(f"EDIT_CLAIM: Error regenerating PDF: {e}")
        flash('Claim updated successfully.', 'success')
        return redirect(url_for('admin_view'))
    # GET: Render form with claim data
    # Map DB row to form_data dict expected by form.html
    form_data = dict(claim)
    # If phone number, format for display
    if 'field_pdf_13b_phone' in form_data:
        form_data['field_pdf_13b_phone'] = format_phone(form_data['field_pdf_13b_phone'])
    # Pass form_data to template
    states_and_territories = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC', 'AS', 'GU', 'MP', 'PR', 'VI'
    ]
    return render_template('form.html', form_data=form_data, title="Edit Claim", states_list=states_and_territories, editing=True, claim_id=claim_id)

@app.route('/')
def form():
    import traceback
    try:
        today_date = datetime.today().strftime('%Y-%m-%d')
        # Persist form data across navigation: always use latest session data or defaults
        html_form_defaults = session.get('html_form_defaults', {
            'field1_agency': '', # Let user type, PDF_FILLER_DEFAULTS will handle if empty at PDF gen
            'field2_name': '',
            'field2_address': '',
            'field2_city': '',
            'field2_state': '',
            'field2_zip': '',
            'field3_type_employment': 'Civilian', # Default to Civilian
            'field_pdf_4_dob': '',
            'field_pdf_5_marital_status': '', # Assuming it's a dropdown/radio
            'field_pdf_13b_phone': '',
            'field8_basis_of_claim': '',
            'field9_property_damage_description': '',
            'field10_nature_of_injury': '',
            'field11_witness_name_1': '',
            'field11_witness_address_1': '',
            'field11_witness_name_2': '',
            'field11_witness_address_2': '',
            'field12a_property_damage_amount': '0',
            'field12b_personal_injury_amount': '90000',
            'field12c_wrongful_death_amount': '0',
            'field12d_total_claim_amount': '0',
            'user_email_address': '',
            'supplemental_question_1_capitol_experience': '',
            'supplemental_question_2_injuries_damages': '',
            'supplemental_question_3_entry_exit_time': '',
            'supplemental_question_4_inside_capitol_details': ''
        })
        session['html_form_defaults'] = html_form_defaults

        # Use the latest form data from session if present
        form_data = session.get('form_data', {}).copy()
        # Ensure all expected keys from defaults are in form_data
        for key, value in html_form_defaults.items():
            form_data.setdefault(key, value)
        session['form_data'] = form_data  # Always persist
        current_app.logger.info(f"FORM PAGE: Loaded form_data from session: {form_data}")

        states_and_territories = [
            'AK', 'AL', 'AR', 'AS', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE',
            'FL', 'GA', 'GU', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY',
            'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MP', 'MS', 'MT',
            'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK',
            'OR', 'PA', 'PR', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA',
            'VI', 'VT', 'WA', 'WI', 'WV', 'WY'
        ]
        validation_errors = session.pop('validation_errors_step1', {})
        current_app.logger.info(f"FORM PAGE: Rendering with form_data: {form_data}")
        return render_template('form.html', form_data=form_data, title="SF-95 Claim Form - Step 1", validation_errors=validation_errors, states_list=states_and_territories)
    except Exception as e:
        with open('/home3/investi9/public_html/west-plaza-lawsuit/debugging-logs.txt', 'a') as f:
            f.write('\n--- Exception during form submission ---\n')
            traceback.print_exc(file=f)
        raise

@app.route('/form')
def redirect_form_to_root():
    return redirect(url_for('form'))

    pdf_data_for_filling_draft = map_form_data_to_pdf_fields(form_data)
    current_app.logger.info(f"--- process_step1 --- Data for DRAFT PDF after mapping: {pdf_data_for_filling_draft}")


    db_filled_pdf_filename_draft = None
    try:
        fill_sf95_pdf(pdf_data_for_filling_draft, PDF_TEMPLATE_PATH, output_pdf_path)
        current_app.logger.info(f"--- process_step1 --- Draft PDF generated: {output_pdf_path}")
        db_filled_pdf_filename_draft = os.path.basename(output_pdf_path)
    except Exception as e:
        current_app.logger.error(f"--- process_step1 --- Error filling DRAFT PDF: {e}")
        flash(f"Error generating draft PDF: {e}. Please proceed to signature, the PDF can be regenerated.", "warning")
        # Non-fatal for draft, allow proceeding to signature. Final PDF generation is key.
        db_filled_pdf_filename_draft = output_pdf_filename_with_ext # Store expected name even if generation failed

    # Prepare data for DB (Stage 1 - signature/date are None)
    data_to_save_for_db_stage1 = {}
    # Get all column names from DB_SCHEMA, excluding 'id' for inserts/updates handled by DB
    schema_column_names_for_data = [col.split(' ')[0] for col in DB_SCHEMA if col.split(' ')[0] != 'id']

    for key in schema_column_names_for_data:
        if key == 'filled_pdf_filename':
            data_to_save_for_db_stage1[key] = db_filled_pdf_filename_draft
        # Ensure specific fields for actual signature text and full signature date are empty at Stage 1 for DB
        elif key == 'field17_signature_of_claimant':
            data_to_save_for_db_stage1[key] = "" # Store empty for actual signature text
        elif key == 'field18_date_of_signature':
            data_to_save_for_db_stage1[key] = "" # Store empty for signature timestamp
        # For other fields, including 'field13a_signature' and 'field14_date_signed' which are now set
        # for the draft PDF, get them from pdf_data_for_filling_draft.
        # If a key is a DB column but not in pdf_data_for_filling_draft (e.g. new supplemental question not yet mapped),
        # try form_data as a fallback, then empty string.
        else:
            data_to_save_for_db_stage1[key] = pdf_data_for_filling_draft.get(key, form_data.get(key, ''))

    current_app.logger.info(f"--- process_step1 --- Data for DB (Stage 1): {data_to_save_for_db_stage1}")

    submission_id_in_progress = None

    # Store required session data for signature_review
    session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft
    session['claimant_name_for_signature'] = name
    session_cookie = request.cookies.get('session')
    current_app.logger.info(f"SIGNATURE POST: Session before redirect: {dict(session)} | Session cookie: {session_cookie} | Headers: {dict(request.headers)}")
    log_msg = f"\nSIGNATURE POST: Session before redirect: {dict(session)} | Session cookie: {session_cookie} | Headers: {dict(request.headers)}\n"
    with open('debugging-logs.txt', 'a') as f:
        f.write(log_msg)
    trim_debug_log()
    return redirect(url_for('signature_review'))

# --- Helper: Trim debug log to 1000 lines ---
def trim_debug_log():
    try:
        with open('debugging-logs.txt', 'r+') as f:
            lines = f.readlines()
            if len(lines) > 1000:
                f.seek(0)
                f.writelines(lines[-1000:])
                f.truncate()
    except Exception as e:
        print(f"Failed to trim debugging-logs.txt: {e}")  # Use print as fallback if logger fails

# --- Helper: Map form/session data to PDF field keys ---
def map_form_data_to_pdf_fields(form_data):
    '''
    Centralizes mapping from user form/session data to PDF field keys.
    Handles all fields in pdf_field_map.json, including concatenation, formatting, and defaulting.
    Logs any missing or blank fields for debugging.
    '''
    from src.utils.pdf_filler import PDF_FIELD_MAP, DEFAULT_VALUES
    pdf_data = {}
    # Claimant info combined
    name = form_data.get('field2_name', '')
    address = form_data.get('field2_address', '')
    city = form_data.get('field2_city', '')
    state = form_data.get('field2_state', '')
    zip_code = form_data.get('field2_zip', '')
    pdf_data['field2_claimant_info_combined'] = f"{name}\n{address}\n{city}, {state} {zip_code}".strip()
    pdf_data['field2_name'] = name
    pdf_data['field2_address'] = address
    pdf_data['field2_city'] = city
    pdf_data['field2_state'] = state
    pdf_data['field2_zip'] = zip_code
    # Type of employment
    employment_type = form_data.get('field3_type_employment', '')
    pdf_data['field3_type_employment'] = form_data.get('field3_other_specify', '') if employment_type == 'Other' else employment_type
    pdf_data['field3_checkbox_civilian'] = employment_type == 'Civilian'
    pdf_data['field3_checkbox_military'] = employment_type == 'Military'
    # DOB, marital status
    pdf_data['field_pdf_4_dob'] = form_data.get('field_pdf_4_dob', '')
    pdf_data['field_pdf_5_marital_status'] = form_data.get('field_pdf_5_marital_status', '')
    # Basis of claim
    boilerplate_8 = DEFAULT_VALUES.get('field8_basis_of_claim', "On January 6, 2021, at the U.S. Capitol, claimant was subjected to excessive force by federal officers, including tear gas and rubber bullets, leading to physical injury and emotional distress.")
    user_8 = form_data.get('field8_basis_of_claim', '').strip()
    pdf_data['field8_basis_of_claim'] = boilerplate_8 if not user_8 else f"{boilerplate_8}\n{user_8}"
    # Property damage
    prop_damage_vehicle = form_data.get('field9_property_damage_description_vehicle', '')
    prop_damage_other = form_data.get('field9_property_damage_description_other', '')
    combined_prop_desc = f"{prop_damage_vehicle}\n{prop_damage_other}".strip()
    pdf_data['field9_property_damage_description'] = combined_prop_desc if combined_prop_desc else DEFAULT_VALUES.get('field9_property_damage_description', '')
    pdf_data['field9_owner_name_address'] = form_data.get('field9_owner_name_address', DEFAULT_VALUES.get('field9_owner_name_address', ''))
    # Nature of injury
    boilerplate_10 = DEFAULT_VALUES.get('field10_nature_of_injury', "Respiratory distress from tear gas, contusions from rubber bullets, and severe emotional distress.")
    user_10 = form_data.get('field10_nature_of_injury', '').strip()
    pdf_data['field10_nature_of_injury'] = boilerplate_10 if not user_10 else f"{boilerplate_10}\n{user_10}"
    # Witnesses
    pdf_data['field11_witness_name'] = form_data.get('field11_witness_name', DEFAULT_VALUES.get('field11_witness_name', ''))
    pdf_data['field11_witness_address'] = form_data.get('field11_witness_address', DEFAULT_VALUES.get('field11_witness_address', ''))
    # Amounts
    pdf_data['field12a_property_damage'] = form_data.get('field12a_property_damage_amount', DEFAULT_VALUES.get('field12a_property_damage', ''))
    pdf_data['field12b_personal_injury'] = form_data.get('field12b_personal_injury_amount', DEFAULT_VALUES.get('field12b_personal_injury', ''))
    pdf_data['field12c_wrongful_death'] = form_data.get('field12c_wrongful_death_amount', DEFAULT_VALUES.get('field12c_wrongful_death', ''))
    pdf_data['field12d_total_claim_amount'] = form_data.get('field12d_total_amount', form_data.get('field12d_total_claim_amount', DEFAULT_VALUES.get('field12d_total_claim_amount', '')))
    # Signature and phone
    pdf_data['field13a_signature'] = form_data.get('field13a_signature', 'Pending Signature')
    pdf_data['field_pdf_13b_phone'] = form_data.get('field_pdf_13b_phone', '')
    pdf_data['field14_date_signed'] = form_data.get('field14_date_signed', '')
    # Insurance, claim details, etc.
    pdf_data['field15_accident_insurance'] = form_data.get('field15_accident_insurance', '')
    pdf_data['field15_insurer_name_address_policy'] = form_data.get('field15_insurer_name_address_policy', '')
    pdf_data['field16_filed_claim'] = form_data.get('field16_filed_claim', '')
    pdf_data['field16_claim_details'] = form_data.get('field16_claim_details', '')
    pdf_data['field17_deductible_amount'] = form_data.get('field17_deductible_amount', '')
    pdf_data['field18_insurer_action'] = form_data.get('field18_insurer_action', '')
    pdf_data['field19_liability_insurance'] = form_data.get('field19_liability_insurance', '')
    pdf_data['field19_insurer_name_address'] = form_data.get('field19_insurer_name_address', '')
    # Log missing/blank fields for all PDF fields
    from flask import current_app
    from src.utils.pdf_filler import PDF_FIELD_MAP
    for app_key, pdf_field in PDF_FIELD_MAP.items():
        if app_key not in pdf_data or pdf_data[app_key] in (None, ""):
            current_app.logger.warning(f"PDF MAPPING: Field '{app_key}' (PDF: '{pdf_field}') is missing or blank in PDF data.")
    return pdf_data



    try:
        cursor.execute("SELECT id FROM claims WHERE field2_name = ?", (claimant_name,))
        existing_record = cursor.fetchone()
        current_time_utc = datetime.now(timezone.utc)

        if existing_record:
            existing_id = existing_record['id']
            current_app.logger.info(f"--- process_step1 --- Claimant '{claimant_name}' found (ID: {existing_id}). Updating with Stage 1 data.")
            update_fields_sql_parts = []
            update_values_list = []
            # Construct SET clause for existing columns in data_to_save_for_db_stage1
            for col_key, col_value in data_to_save_for_db_stage1.items():
                 if col_key in schema_column_names_for_data and col_key not in ['created_at']:
                    update_fields_sql_parts.append(f"{col_key} = ?")
                    update_values_list.append(col_value)
            
            if update_fields_sql_parts:
                update_fields_sql_parts.append("updated_at = ?")
                update_values_list.append(current_time_utc)
                update_values_list.append(existing_id) # For the WHERE clause

                update_sql = f"UPDATE claims SET {', '.join(update_fields_sql_parts)} WHERE id = ?"
                cursor.execute(update_sql, tuple(update_values_list))
                db.commit()
                submission_id_in_progress = existing_id
                current_app.logger.info(f"--- process_step1 --- Record for '{claimant_name}' (ID: {existing_id}) updated with Stage 1 data.")
            else:
                 current_app.logger.warning(f"--- process_step1 --- No fields to update for existing claimant '{claimant_name}' at Stage 1.")
                 submission_id_in_progress = existing_id # Still use existing ID if no data changed
        else:
            current_app.logger.info(f"--- process_step1 --- New claimant '{claimant_name}'. Inserting Stage 1 data.")
            data_to_save_for_db_stage1['created_at'] = current_time_utc
            data_to_save_for_db_stage1['updated_at'] = current_time_utc
            
            cols_for_insert_sql = []
            vals_for_insert_list = []
            placeholders_for_insert_sql = []
            
            # Ensure all keys in data_to_save_for_db_stage1 are valid columns
            for col_name in schema_column_names_for_data + ['created_at', 'updated_at']:
                if col_name in data_to_save_for_db_stage1: # only include if value was prepared
                    cols_for_insert_sql.append(col_name)
                    vals_for_insert_list.append(data_to_save_for_db_stage1[col_name])
                    placeholders_for_insert_sql.append('?')
            
            if cols_for_insert_sql:
                insert_sql = f"INSERT INTO claims ({', '.join(cols_for_insert_sql)}) VALUES ({', '.join(placeholders_for_insert_sql)})"
                cursor.execute(insert_sql, tuple(vals_for_insert_list))
                db.commit()
                submission_id_in_progress = cursor.lastrowid
                current_app.logger.info(f"--- process_step1 --- New record for '{claimant_name}' inserted with Stage 1 data (ID: {submission_id_in_progress}).")
            else:
                current_app.logger.error(f"--- process_step1 --- No columns to insert for Stage 1 for '{claimant_name}'.")
                flash("Error saving initial form data. No data to insert.", "danger")
                session['form_step1_data'] = form_data # Preserve submitted data
                return redirect(url_for('form'))

        # Store necessary info in session for Step 2 (signature)
        session['submission_id_in_progress'] = submission_id_in_progress
        # Storing the ALREADY MAPPED data from step 1, which uses app-side keys
        session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft 
        session['claimant_name_for_signature'] = pdf_data_for_filling_draft.get('field2_name', '') # Get name from mapped data
        
        current_app.logger.info(f"--- process_step1 --- Stored submission_id_in_progress: {submission_id_in_progress}, claimant_name: {session['claimant_name_for_signature']} in session. Redirecting to signature page.")
        # Clear any previous step 1 validation errors as we are proceeding
        session.pop('validation_errors_step1', None)
        return redirect(url_for('signature_review'))

    except sqlite3.Error as e:
        current_app.logger.error(f"--- process_step1 --- Database error during Stage 1 save for '{claimant_name}': {e}")
        db.rollback()
        flash(f"Database error while saving initial data: {e}. Please try again.", "danger")
        session['form_step1_data'] = form_data # Preserve data on error
        return redirect(url_for('form'))
    except Exception as e:
        current_app.logger.error(f"--- process_step1 --- Unexpected error during Stage 1 for '{claimant_name}': {e}", exc_info=True)
        db.rollback()
        flash("An unexpected error occurred while saving initial data. Please try again.", "danger")
        session['form_step1_data'] = form_data
        return redirect(url_for('form'))

@app.route('/signature', methods=['GET', 'POST'])
def signature():
    from datetime import datetime
    session_cookie = request.cookies.get('session')
    # --- Heal session if needed ---
    user_email_address = session.get('user_email_address', '').strip().lower()
    form_data = session.get('form_data', {})
    form_email = form_data.get('user_email_address', '').strip().lower() if form_data else ''
    draft_email = session.get('draft_pdf_filename', '').split('_')[0] if session.get('draft_pdf_filename') else ''

    current_app.logger.info(f"[SIGNATURE ROUTE ENTRY] User: {user_email_address}, IP: {request.remote_addr}, Method: {request.method}, Session: {dict(session)}, Headers: {dict(request.headers)}")
    current_app.logger.info(f"[SIGNATURE ROUTE] Email sources: session['user_email_address']='{user_email_address}', form_data['user_email_address']='{form_email}', draft_pdf_filename-derived='{draft_email}'")

    # Healing logic: always restore from form_data if missing
    if not user_email_address and form_email:
        session['user_email_address'] = form_email
        session.modified = True
        current_app.logger.info(f"[SIGNATURE ROUTE] Healed session['user_email_address'] from form_data: {form_email}")
    elif not user_email_address and draft_email:
        session['user_email_address'] = draft_email
        session.modified = True
        current_app.logger.info(f"[SIGNATURE ROUTE] Healed session['user_email_address'] from draft_pdf_filename: {draft_email}")
    else:
        current_app.logger.info(f"[SIGNATURE ROUTE] No healing needed for user_email_address.")

    # If still missing, log error
    if not session.get('user_email_address', '').strip():
        current_app.logger.error(f"[SIGNATURE ROUTE ERROR] user_email_address is STILL missing after healing attempts. Session: {dict(session)}, form_data: {form_data}")

    if request.method == 'GET':
        current_app.logger.info(f"[SIGNATURE GET] Rendering signature review page. claimant_name_for_signature='{session.get('claimant_name_for_signature', '')}'")
        log_msg = f"\n[SIGNATURE GET] Rendering signature review page. claimant_name_for_signature='{session.get('claimant_name_for_signature', '')}'\nSession: {dict(session)}\nSession cookie: {session_cookie}\nHeaders: {dict(request.headers)}\n"
        with open('debugging-logs.txt', 'a') as f:
            f.write(log_msg)
        trim_debug_log()
        pdf_data_for_filling_draft = session.get('pdf_data_for_filling_draft')
        if not pdf_data_for_filling_draft:
            current_app.logger.warning(f"[SIGNATURE GET] 'pdf_data_for_filling_draft' NOT FOUND in session. Redirecting to form.")
            flash('No data from step 1 found. Please start from the beginning.', 'error')
            return redirect(url_for('form'))
        today_date = datetime.today().strftime('%Y-%m-%d')
        signature_defaults_from_error = session.pop('form_data_step2_errors', None)
        if signature_defaults_from_error:
            signature_defaults = signature_defaults_from_error
        else:
            signature_defaults = {
                'field17_signature_of_claimant': session.get('claimant_name_for_signature', ''),
                'user_email_address': session.get('user_email_address', '')
            }
        validation_errors = session.pop('validation_errors_step2', {})
        # Pass draft PDF filename if available
        draft_pdf_filename = session.get('draft_pdf_filename')
        return render_template('signature.html', pdf_data_for_filling_draft=pdf_data_for_filling_draft, today_date=today_date, form_data=signature_defaults, validation_errors=validation_errors, pdf_filename=draft_pdf_filename)
    else:
        # POST: Handle signature submission and FINALIZE claim (PDF + DB)
        form_data = request.form.to_dict()
        current_app.logger.info(f"[SIGNATURE POST] Received form data: {form_data}")
        user_email_address = form_data.get('user_email_address', '').strip().lower() or session.get('user_email_address', '').strip().lower() or ''
        current_app.logger.info(f"[SIGNATURE POST] user_email_address from form: '{form_data.get('user_email_address', '')}', session: '{session.get('user_email_address', '')}', draft: '{draft_email}' | Using: '{user_email_address}'")
        if not user_email_address:
            current_app.logger.error(f"[SIGNATURE POST ERROR] No email address found in session, form, or draft. Cannot generate PDF filename. Aborting.")
            flash('Error: Email address missing. Please start over.', 'danger')
            return redirect(url_for('form'))
        session['user_email_address'] = user_email_address
        session.modified = True
        required_fields = ['field17_signature_of_claimant']
        validation_errors = {}
        for field in required_fields:
            if not form_data.get(field):
                validation_errors[field] = 'This field is required.'
        if validation_errors:
            session['validation_errors_step2'] = validation_errors
            session['form_data_step2_errors'] = form_data
            return redirect(url_for('signature'))
        # --- BEGIN FINALIZATION LOGIC (from old /submit) ---
        submission_id_in_progress = session.get('submission_id_in_progress')
        pdf_data_for_filling_draft = session.get('pdf_data_for_filling_draft')
        current_app.logger.info(f"[SIGNATURE FINALIZATION] submission_id_in_progress={submission_id_in_progress}, pdf_data_for_filling_draft={pdf_data_for_filling_draft}")
        if not submission_id_in_progress or not pdf_data_for_filling_draft:
            current_app.logger.error("[SIGNATURE FINALIZATION ERROR] Missing submission ID or Step 1 data in session. Redirecting to form.")
            flash("Your session may have expired or there was an error processing step 1. Please start over.", "danger")
            session.pop('submission_id_in_progress', None)
            session.pop('pdf_data_for_filling_draft', None)
            session.pop('claimant_name_for_signature', None)
            return redirect(url_for('form'))
        # Validation for signature page (Step 2)
        claimant_name_from_step1 = pdf_data_for_filling_draft.get('field2_name', '')
        signature_of_claimant_from_form = form_data.get('field17_signature_of_claimant')
        validation_errors_step2 = {}
        if not signature_of_claimant_from_form:
            validation_errors_step2['field17_signature_of_claimant'] = "Signature is required."
        elif signature_of_claimant_from_form.strip().lower() != claimant_name_from_step1.strip().lower():
            validation_errors_step2['field17_signature_of_claimant'] = f"Signature must exactly match the claimant's name: '{claimant_name_from_step1}'."
        if validation_errors_step2:
            session['validation_errors_step2'] = validation_errors_step2
            session['form_data_step2_errors'] = form_data
            return redirect(url_for('signature'))
        # Continue with finalization as before...

        db = get_db()
        cursor = db.cursor()
        # Guarantee: Always use email for filename, never fallback to name or 'unknown'
        user_email_address = (form_data.get('user_email_address') or session.get('user_email_address', '')).strip().lower()
        if not user_email_address:
            current_app.logger.error("SIGNATURE FINALIZATION: Email address missing for filename generation. Redirecting to form.")
            flash('Critical error: Email address missing. Please enter your email address to proceed.', 'danger')
            return redirect(url_for('form'))
        try:
            slug = slugify(user_email_address)
        except Exception as e:
            current_app.logger.error(f"SIGNATURE FINALIZATION: slugify failed for email '{user_email_address}': {e}")
            flash('Critical error: Invalid email address for PDF filename.', 'danger')
            return redirect(url_for('form'))
        output_pdf_filename_with_ext = f"{slug}_SF95.pdf"
        output_pdf_path = os.path.join(current_app.config['FILLED_FORMS_DIR'], output_pdf_filename_with_ext)
        session['user_email_address'] = user_email_address
        current_app.logger.info(f"SIGNATURE FINALIZATION: Using email '{user_email_address}' for PDF filename: {output_pdf_filename_with_ext}")

        # Use the provided local time for signature date
        date_of_signature_local = '2025-05-19T20:42:56-05:00'
        date_of_signature_pdf = '05/19/2025'  # MM/DD/YYYY
        # Compose PDF data for final version
        pdf_data_for_filling_final = pdf_data_for_filling_draft.copy()
        pdf_data_for_filling_final['field13a_signature'] = f"/s/ {claimant_name_from_step1.strip()}"
        pdf_data_for_filling_final['field14_date_signed'] = date_of_signature_pdf
        for default_key, default_value in PDF_FILLER_DEFAULTS.items():
            if default_key not in pdf_data_for_filling_final:
                pdf_data_for_filling_final[default_key] = default_value
                current_app.logger.info(f"SIGNATURE FINALIZATION: Added default '{default_key}':'{default_value}' to final PDF data as it was missing.")
        current_app.logger.info(f"SIGNATURE FINALIZATION: Final PDF data prepared: {pdf_data_for_filling_final}")

        # Generate the final PDF
        db_filled_pdf_filename_final = None
        try:
            fill_sf95_pdf(pdf_data_for_filling_final, PDF_TEMPLATE_PATH, output_pdf_path)
            current_app.logger.info(f"SIGNATURE FINALIZATION: Final PDF generated: {output_pdf_path}")
            db_filled_pdf_filename_final = os.path.basename(output_pdf_path)
        except Exception as e:
            current_app.logger.error(f"SIGNATURE FINALIZATION: Error filling FINAL PDF for ID {submission_id_in_progress}: {e}", exc_info=True)
            flash(f"Critical Error: Could not generate the final PDF document. Please contact support with submission ID {submission_id_in_progress}.", "danger")
            db_filled_pdf_filename_final = output_pdf_filename_with_ext

        # Prepare DB update
        data_to_update_in_db = {
            'field17_signature_of_claimant': signature_of_claimant_from_form,
            'field18_date_of_signature': date_of_signature_local,
            'filled_pdf_filename': db_filled_pdf_filename_final,
            'field13a_signature': f"/s/ {claimant_name_from_step1.strip()}",
            'field14_date_signed': date_of_signature_local,
            'updated_at': date_of_signature_local
        }
        current_app.logger.info(f"SIGNATURE FINALIZATION: Data to update in DB for ID {submission_id_in_progress}: {data_to_update_in_db}")
        try:
            update_fields_sql_parts = []
            update_values_list = []
            schema_column_names = [col.split(' ')[0] for col in DB_SCHEMA]
            for col_key, col_value in data_to_update_in_db.items():
                if col_key in schema_column_names:
                    update_fields_sql_parts.append(f"{col_key} = ?")
                    update_values_list.append(col_value)
            if not update_fields_sql_parts:
                current_app.logger.error(f"SIGNATURE FINALIZATION: No valid fields to update in DB for ID {submission_id_in_progress}. This is unexpected.")
                flash("Error finalizing submission: No data fields to update.", "danger")
                session['submission_id_in_progress'] = submission_id_in_progress
                session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft
                return redirect(url_for('signature'))
            update_values_list.append(submission_id_in_progress)
            update_sql = f"UPDATE claims SET {', '.join(update_fields_sql_parts)} WHERE id = ?"
            current_app.logger.info(f"SIGNATURE FINALIZATION: Executing SQL: {update_sql} with values: {tuple(update_values_list)}")
            cursor.execute(update_sql, tuple(update_values_list))
            db.commit()
            current_app.logger.info(f"SIGNATURE FINALIZATION: Successfully updated record ID {submission_id_in_progress} in database.")
            # Clear session data after successful submission
            session.pop('submission_id_in_progress', None)
            session.pop('pdf_data_for_filling_draft', None)
            session.pop('claimant_name_for_signature', None)
            session.pop('form_data', None)
            session.pop('validation_errors_step1', None)
            session.pop('form_data_step2_errors', None)
            session.pop('validation_errors_step2', None)
            flash('Form submitted successfully!', 'success')
            return redirect(url_for('success_page', submission_id=submission_id_in_progress))
        except sqlite3.Error as e:
            current_app.logger.error(f"SIGNATURE FINALIZATION: Database error updating record ID {submission_id_in_progress}: {e}", exc_info=True)
            db.rollback()
            flash(f"Database error finalizing submission: {e}. Please try again or contact support with ID {submission_id_in_progress}.", "danger")
            session['submission_id_in_progress'] = submission_id_in_progress
            session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft
            session['claimant_name_for_signature'] = claimant_name_from_step1
            return redirect(url_for('signature'))
        except Exception as e:
            current_app.logger.error(f"SIGNATURE FINALIZATION: Unexpected error finalizing submission for ID {submission_id_in_progress}: {e}", exc_info=True)
            db.rollback()
            flash(f"An unexpected error occurred during final submission. Please contact support with ID {submission_id_in_progress}.", "danger")
            session['submission_id_in_progress'] = submission_id_in_progress
            session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft
            session['claimant_name_for_signature'] = claimant_name_from_step1
            return redirect(url_for('signature'))

            fill_sf95_pdf(pdf_data_for_filling_final, PDF_TEMPLATE_PATH, output_pdf_path)
            current_app.logger.info(f"SIGNATURE FINALIZATION: Final PDF generated: {output_pdf_path}")
            db_filled_pdf_filename_final = os.path.basename(output_pdf_path)
        except Exception as e:
            current_app.logger.error(f"SIGNATURE FINALIZATION: Error filling FINAL PDF for ID {submission_id_in_progress}: {e}", exc_info=True)
            flash(f"Critical Error: Could not generate the final PDF document. Please contact support with submission ID {submission_id_in_progress}.", "danger")
            db_filled_pdf_filename_final = output_pdf_filename_with_ext

        data_to_update_in_db = {
            'field17_signature_of_claimant': signature_of_claimant_from_form,
            'field18_date_of_signature': date_of_signature_utc_str_for_db,
            'filled_pdf_filename': db_filled_pdf_filename_final,
            'field13a_signature': signature_of_claimant_from_form,
            'field14_date_signed': date_of_signature_utc_str_for_db,
            'updated_at': datetime.now(timezone.utc)
        }
        current_app.logger.info(f"SIGNATURE FINALIZATION: Data to update in DB for ID {submission_id_in_progress}: {data_to_update_in_db}")
        try:
            update_fields_sql_parts = []
            update_values_list = []
            schema_column_names = [col.split(' ')[0] for col in DB_SCHEMA]
            for col_key, col_value in data_to_update_in_db.items():
                if col_key in schema_column_names:
                    update_fields_sql_parts.append(f"{col_key} = ?")
                    update_values_list.append(col_value)
            if not update_fields_sql_parts:
                current_app.logger.error(f"SIGNATURE FINALIZATION: No valid fields to update in DB for ID {submission_id_in_progress}. This is unexpected.")
                flash("Error finalizing submission: No data fields to update.", "danger")
                session['submission_id_in_progress'] = submission_id_in_progress
                session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft
                session['claimant_name_for_signature'] = claimant_name_from_step1
                return redirect(url_for('signature'))
            update_values_list.append(submission_id_in_progress)
            update_sql = f"UPDATE claims SET {', '.join(update_fields_sql_parts)} WHERE id = ?"
            current_app.logger.info(f"SIGNATURE FINALIZATION: Executing SQL: {update_sql} with values: {tuple(update_values_list)}")
            cursor.execute(update_sql, tuple(update_values_list))
            db.commit()
            current_app.logger.info(f"SIGNATURE FINALIZATION: Successfully updated record ID {submission_id_in_progress} in database.")
            # Clear session data after successful submission
            session.pop('submission_id_in_progress', None)
            session.pop('pdf_data_for_filling_draft', None)
            session.pop('claimant_name_for_signature', None)
            session.pop('form_data', None)
            session.pop('validation_errors_step1', None)
            session.pop('form_data_step2_errors', None)
            session.pop('validation_errors_step2', None)
            flash('Form submitted successfully!', 'success')
            return redirect(url_for('success_page', submission_id=submission_id_in_progress))
        except sqlite3.Error as e:
            current_app.logger.error(f"SIGNATURE FINALIZATION: Database error updating record ID {submission_id_in_progress}: {e}", exc_info=True)
            db.rollback()
            flash(f"Database error finalizing submission: {e}. Please try again or contact support with ID {submission_id_in_progress}.", "danger")
            session['submission_id_in_progress'] = submission_id_in_progress
            session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft
            session['claimant_name_for_signature'] = claimant_name_from_step1
            return redirect(url_for('signature'))
        except Exception as e:
            current_app.logger.error(f"SIGNATURE FINALIZATION: Unexpected error finalizing submission for ID {submission_id_in_progress}: {e}", exc_info=True)
            db.rollback()
            flash(f"An unexpected error occurred during final submission. Please contact support with ID {submission_id_in_progress}.", "danger")
            session['submission_id_in_progress'] = submission_id_in_progress
            session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft
            session['claimant_name_for_signature'] = claimant_name_from_step1
            return redirect(url_for('signature'))

@app.route('/submit', methods=['POST'])
def submit_form():
    # Log incoming form data and session state
    current_app.logger.info(f"SUBMIT_FORM: Received form data: {dict(request.form)}")
    current_app.logger.info(f"SUBMIT_FORM: Session before processing: {dict(session)}")

    # --- Step 1: Map form data to PDF/DB keys ---
    form_data = dict(request.form)
    # Normalize phone before saving to DB
    if 'field_pdf_13b_phone' in form_data:
        form_data['field_pdf_13b_phone'] = normalize_phone(form_data['field_pdf_13b_phone'])
    # --- Recalculate total claim amount (12d) from 12a, 12b, 12c ---
    try:
        prop_dam = float(form_data.get('field12a_property_damage_amount', 0) or 0)
        pers_inj = float(form_data.get('field12b_personal_injury_amount', 0) or 0)
        wrong_death = float(form_data.get('field12c_wrongful_death_amount', 0) or 0)
        total_claim = prop_dam + pers_inj + wrong_death
        form_data['field12d_total_claim_amount'] = f"{total_claim:.2f}"
    except Exception as e:
        current_app.logger.error(f"SUBMIT_FORM: Error recalculating total claim amount: {e}")
        # Optionally: fallback to original value or clear
        form_data['field12d_total_claim_amount'] = form_data.get('field12d_total_claim_amount', '')
    # Save latest form data to session for persistence
    session['form_data'] = form_data.copy()
    # Explicitly extract and store the email address in the session
    user_email_address = form_data.get('user_email_address', '').strip().lower()
    session['user_email_address'] = user_email_address
    current_app.logger.info(f"SUBMIT_FORM: Set session['user_email_address'] = {user_email_address}")
    pdf_data_for_filling_draft = map_form_data_to_pdf_fields(form_data)
    current_app.logger.info(f"SUBMIT_FORM: Mapped form data to PDF/DB keys: {pdf_data_for_filling_draft}")
    current_app.logger.info(f"SUBMIT_FORM: Saved form_data to session for persistence: {form_data}")

    # --- Step 1.5: Generate slugified email and draft PDF filename ---
    if not user_email_address:
        current_app.logger.error("SUBMIT_FORM: Email address missing for filename generation. Redirecting to form.")
        flash('Critical error: Email address missing. Please enter your email address to proceed.', 'danger')
        return redirect(url_for('form'))
    slug = slugify(user_email_address)
    output_pdf_filename_with_ext = f"{slug}_SF95.pdf"
    output_pdf_path = os.path.join(current_app.config['FILLED_FORMS_DIR'], output_pdf_filename_with_ext)

    # --- Step 1.6: Generate draft PDF immediately ---
    try:
        from src.utils.pdf_filler import fill_sf95_pdf
        fill_sf95_pdf(pdf_data_for_filling_draft, PDF_TEMPLATE_PATH, output_pdf_path)
        current_app.logger.info(f"SUBMIT_FORM: Draft PDF generated: {output_pdf_path}")
    except Exception as e:
        current_app.logger.error(f"SUBMIT_FORM: Error generating draft PDF: {e}")

    # Save filename to session for later steps
    session['draft_pdf_filename'] = output_pdf_filename_with_ext

    # --- Step 2: Save to session ---
    import uuid
    submission_id_in_progress = session.get('submission_id_in_progress') or str(uuid.uuid4())
    session['submission_id_in_progress'] = submission_id_in_progress
    session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft
    session['claimant_name_for_signature'] = form_data.get('field2_name', '')
    current_app.logger.info(f"SUBMIT_FORM: Session set: submission_id_in_progress={submission_id_in_progress}, claimant_name_for_signature={form_data.get('field2_name', '')}, pdf_data_for_filling_draft={pdf_data_for_filling_draft}")

    # --- Step 3: Insert into DB (Stage 1) ---
    db = get_db()
    cursor = db.cursor()
    from datetime import datetime, timezone
    current_time_utc = datetime.now(timezone.utc)
    # Prepare data for DB insert
    data_to_save_for_db_stage1 = {}
    schema_column_names_for_data = [col.split(' ')[0] for col in DB_SCHEMA if col.split(' ')[0] != 'id']
    for key in schema_column_names_for_data:
        if key == 'filled_pdf_filename':
            data_to_save_for_db_stage1[key] = output_pdf_filename_with_ext
        elif key == 'field17_signature_of_claimant':
            data_to_save_for_db_stage1[key] = ''
        elif key == 'field18_date_of_signature':
            data_to_save_for_db_stage1[key] = ''
        else:
            data_to_save_for_db_stage1[key] = pdf_data_for_filling_draft.get(key, form_data.get(key, ''))
    data_to_save_for_db_stage1['created_at'] = current_time_utc
    data_to_save_for_db_stage1['updated_at'] = current_time_utc
    current_app.logger.info(f"SUBMIT_FORM: Data prepared for DB insert: {data_to_save_for_db_stage1}")
    # Insert
    try:
        cols_for_insert_sql = []
        vals_for_insert_list = []
        placeholders_for_insert_sql = []
        for col_name in schema_column_names_for_data + ['created_at', 'updated_at']:
            if col_name in data_to_save_for_db_stage1:
                cols_for_insert_sql.append(col_name)
                vals_for_insert_list.append(data_to_save_for_db_stage1[col_name])
                placeholders_for_insert_sql.append('?')
        if cols_for_insert_sql:
            # Upsert: Replace if filled_pdf_filename already exists
            insert_sql = f"INSERT INTO claims ({', '.join(cols_for_insert_sql)}) VALUES ({', '.join(placeholders_for_insert_sql)}) ON CONFLICT(filled_pdf_filename) DO UPDATE SET " + \
                ', '.join([f"{col}=excluded.{col}" for col in cols_for_insert_sql if col != 'filled_pdf_filename'])
            cursor.execute(insert_sql, tuple(vals_for_insert_list))
            db.commit()
            session['submission_id_in_progress'] = cursor.lastrowid
            current_app.logger.info(f"SUBMIT_FORM: Inserted new claim with ID {cursor.lastrowid}")
        else:
            current_app.logger.error("SUBMIT_FORM: No columns to insert for Stage 1.")
            flash("Error saving initial form data. No data to insert.", "danger")
            session['form_step1_data'] = form_data
            return redirect(url_for('form'))
    except Exception as e:
        current_app.logger.error(f"SUBMIT_FORM: Exception during DB insert: {e}")
        flash(f"Error saving initial form data: {e}", "danger")
        session['form_step1_data'] = form_data
        return redirect(url_for('form'))

    # --- Step 3.5: Create user if not exists ---
    from werkzeug.security import generate_password_hash
    import secrets
    from src.app import User
    
    if user_email_address:
        if not User.get_by_username(user_email_address):
            temp_password = secrets.token_urlsafe(10)
            User.create_user(user_email_address, temp_password, role='user')
            current_app.logger.info(f"SUBMIT_FORM: Created new user {user_email_address} with temp password (not shown in logs)")
        else:
            current_app.logger.info(f"SUBMIT_FORM: User {user_email_address} already exists, not creating.")

    # --- Step 4: Redirect to signature page ---
    current_app.logger.info(f"SUBMIT_FORM: Redirecting to signature page with session: {dict(session)}")
    trim_debug_log()
    return redirect(url_for('signature'))

    signature_page_data = dict(request.form) # Data from the signature page submission
    current_app.logger.info(f"--- submit_form (Stage 2) --- Signature page data: {signature_page_data} for DB ID: {submission_id_in_progress}")
    current_app.logger.info(f"--- submit_form (Stage 2) --- Step 1 data from session: {pdf_data_for_filling_draft}")

    # Validation for signature page (Step 2)
    claimant_name_from_step1 = pdf_data_for_filling_draft.get('field2_name', '')
    signature_of_claimant_from_form = signature_page_data.get('field17_signature_of_claimant')
    
    validation_errors_step2 = {}
    if not signature_of_claimant_from_form:
        validation_errors_step2['field17_signature_of_claimant'] = "Signature is required."
    elif signature_of_claimant_from_form.strip().lower() != claimant_name_from_step1.strip().lower():
        validation_errors_step2['field17_signature_of_claimant'] = f"Signature must exactly match the claimant's name: '{claimant_name_from_step1}'."

    if validation_errors_step2:
        current_app.logger.warning(f"--- submit_signature (Stage 2) --- Validation errors: {validation_errors_step2}")
        # Session variables are already set from signature, just add errors and redirect back
        session['form_data_step2_errors'] = signature_page_data # To prefill signature attempt on error
        session['validation_errors_step2'] = validation_errors_step2
        trim_debug_log()
        return redirect(url_for('signature_review'))

    # --- Finalize Submission (Stage 2) ---
    db = get_db()
    cursor = db.cursor()

    # PDF Filename (should be same as draft, using claimant name from Step 1 data)
    slug = slugify(claimant_name_from_step1)
    output_pdf_filename_with_ext = f"{slug}_SF95.pdf"
    output_pdf_path = os.path.join(current_app.config['FILLED_FORMS_DIR'], output_pdf_filename_with_ext)

    # Server-generated Date of Signature (UTC)
    date_of_signature_utc_dt = datetime.now(timezone.utc)
    date_of_signature_utc_str_for_db = date_of_signature_utc_dt.strftime('%Y-%m-%dT%H:%M:%S')
    current_app.logger.info(f"--- submit_form (Stage 2) --- Server-generated signature datetime (UTC): {date_of_signature_utc_str_for_db}")

    # Prepare data for FINAL PDF (combines Step 1 data with Step 2 signature details)
    # Start with the already mapped data from Step 1 (retrieved from session)
    pdf_data_for_filling_final = pdf_data_for_filling_draft.copy()
    
    # Add/Overwrite with signature and final server-generated signature date
    pdf_data_for_filling_final['field13a_signature'] = signature_of_claimant_from_form # Actual signature for PDF Box 13a
    pdf_data_for_filling_final['field14_date_signed'] = date_of_signature_utc_dt.strftime('%m/%d/%Y') # Format the date as MM/DD/YYYY for the PDF's Box 14
    
    # Ensure all default PDF filler keys are present if not already in step 1 data (should be, due to process_step1 logic)
    for default_key, default_value in PDF_FILLER_DEFAULTS.items():
        if default_key not in pdf_data_for_filling_final:
            pdf_data_for_filling_final[default_key] = default_value
            current_app.logger.info(f"--- submit_form (Stage 2) --- Added default '{default_key}':'{default_value}' to final PDF data as it was missing.")

    # Recalculate total amount if necessary, or ensure it's correctly pulled from step 1.
    # Current logic in process_step1 maps 'field12d_total_amount' (html name) to 'field12d_total_claim_amount' (app key)
    # So, pdf_data_for_filling_final['field12d_total_claim_amount'] should have the value from step 1.
    # If a calculation were needed here from 12a, 12b, 12c it would look like:
    # try:
    #     prop_dam = float(pdf_data_for_filling_final.get('field12a_property_damage', '0').replace('$', '').replace(',', '') or '0')
    #     pers_inj = float(pdf_data_for_filling_final.get('field12b_personal_injury', '0').replace('$', '').replace(',', '') or '0')
    #     wrong_death = float(pdf_data_for_filling_final.get('field12c_wrongful_death', '0').replace('$', '').replace(',', '') or '0')
    #     total_claim = prop_dam + pers_inj + wrong_death
    #     pdf_data_for_filling_final['field12d_total_claim_amount'] = f"{total_claim:,.2f}"
    # except ValueError:
    #     current_app.logger.error("--- submit_form (Stage 2) --- Error converting amount fields to float for total calculation.")
    #     # Keep existing total or set to empty if conversion fails
    #     pdf_data_for_filling_final['field12d_total_claim_amount'] = pdf_data_for_filling_final.get('field12d_total_claim_amount', '')

    current_app.logger.info(f"--- submit_form (Stage 2) --- Final PDF data prepared: {pdf_data_for_filling_final}")

    db_filled_pdf_filename_final = None
    try:
        fill_sf95_pdf(pdf_data_for_filling_final, PDF_TEMPLATE_PATH, output_pdf_path)
        current_app.logger.info(f"--- submit_form (Stage 2) --- Final PDF generated: {output_pdf_path}")
        db_filled_pdf_filename_final = os.path.basename(output_pdf_path)
    except Exception as e:
        current_app.logger.error(f"--- submit_form (Stage 2) --- Error filling FINAL PDF for ID {submission_id_in_progress}: {e}", exc_info=True)
        flash(f"Critical Error: Could not generate the final PDF document. Please contact support with submission ID {submission_id_in_progress}.", "danger")
        # Even if PDF fails, we should still try to save the signature data to DB
        db_filled_pdf_filename_final = output_pdf_filename_with_ext # Save expected name

    # Data to UPDATE in the database for the finalized submission
    data_to_update_in_db = {
        'field17_signature_of_claimant': signature_of_claimant_from_form,
        'field18_date_of_signature': date_of_signature_utc_str_for_db, # Store raw UTC string in DB
        'filled_pdf_filename': db_filled_pdf_filename_final,
        'field13a_signature': signature_of_claimant_from_form, # Update DB column as well if it exists
        'field14_date_signed': date_of_signature_utc_str_for_db, # Store raw UTC string in DB (or formatted if preferred for this specific PDF field column)
        'updated_at': datetime.now(timezone.utc) # Update the 'updated_at' timestamp
    }
    current_app.logger.info(f"--- submit_form (Stage 2) --- Data to update in DB for ID {submission_id_in_progress}: {data_to_update_in_db}")

    try:
        update_fields_sql_parts = []
        update_values_list = []
        schema_column_names = [col.split(' ')[0] for col in DB_SCHEMA]

        for col_key, col_value in data_to_update_in_db.items():
            if col_key in schema_column_names: # Ensure we only try to update valid columns
                update_fields_sql_parts.append(f"{col_key} = ?")
                update_values_list.append(col_value)
        
        if not update_fields_sql_parts:
            current_app.logger.error(f"--- submit_form (Stage 2) --- No valid fields to update in DB for ID {submission_id_in_progress}. This is unexpected.")
            flash("Error finalizing submission: No data fields to update.", "danger")
            # Keep session data for retry/debug if needed by redirecting back to signature page
            session['submission_id_in_progress'] = submission_id_in_progress 
            session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft
            session['claimant_name_for_signature'] = claimant_name_from_step1
            return redirect(url_for('signature_review'))

        update_values_list.append(submission_id_in_progress) # For the WHERE id = ?
        update_sql = f"UPDATE claims SET {', '.join(update_fields_sql_parts)} WHERE id = ?"
        
        current_app.logger.info(f"--- submit_form (Stage 2) --- Executing SQL: {update_sql} with values: {tuple(update_values_list)}")
        cursor.execute(update_sql, tuple(update_values_list))
        db.commit()
        current_app.logger.info(f"--- submit_form (Stage 2) --- Successfully updated record ID {submission_id_in_progress} in database.")

        # Clear session data after successful submission
        session.pop('submission_id_in_progress', None)
        session.pop('pdf_data_for_filling_draft', None)
        session.pop('claimant_name_for_signature', None)
        session.pop('form_data', None) # Clean up old key if present
        session.pop('validation_errors_step1', None)
        session.pop('form_data_step2_errors', None)
        session.pop('validation_errors_step2', None)
        
        flash('Form submitted successfully!', 'success')
        return redirect(url_for('success_page', submission_id=submission_id_in_progress))

    except sqlite3.Error as e:
        current_app.logger.error(f"--- submit_form (Stage 2) --- Database error updating record ID {submission_id_in_progress}: {e}", exc_info=True)
        db.rollback()
        flash(f"Database error finalizing submission: {e}. Please try again or contact support with ID {submission_id_in_progress}.", "danger")
        # Preserve session data for potential retry by redirecting back to signature page
        session['submission_id_in_progress'] = submission_id_in_progress 
        session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft
        session['claimant_name_for_signature'] = claimant_name_from_step1
        return redirect(url_for('signature_review'))
    except Exception as e:
        current_app.logger.error(f"--- submit_form (Stage 2) --- Unexpected error finalizing submission for ID {submission_id_in_progress}: {e}", exc_info=True)
        db.rollback()
        flash(f"An unexpected error occurred during final submission. Please contact support with ID {submission_id_in_progress}.", "danger")
        session['submission_id_in_progress'] = submission_id_in_progress 
        session['pdf_data_for_filling_draft'] = pdf_data_for_filling_draft
        session['claimant_name_for_signature'] = claimant_name_from_step1
        return redirect(url_for('signature_review'))

@app.route('/success/<int:submission_id>')
def success_page(submission_id):
    db = get_db()
    cursor = db.cursor()
    claim = cursor.execute('SELECT * FROM claims WHERE id = ?', (submission_id,)).fetchone()
    pdf_filename = claim['filled_pdf_filename'] if claim else None
    # Find user by email if available in claim
    user_id = None
    if claim and 'user_email_address' in claim.keys():
        user_row = cursor.execute('SELECT id FROM users WHERE username = ?', (claim['user_email_address'],)).fetchone()
        if user_row:
            user_id = user_row['id']
    return render_template('success.html', submission_id=submission_id, pdf_filename=pdf_filename, user_id=user_id)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    error = None
    message = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            error = "Please enter your email address."
        else:
            db = get_db()
            cursor = db.cursor()
            user_row = cursor.execute('SELECT id FROM users WHERE username = ?', (email,)).fetchone()
            if user_row:
                # For now, redirect to set_password page (no email delivery yet)
                return redirect(url_for('set_password', user_id=user_row['id']))
            else:
                error = "No account found for that email address. If you just submitted a form, please use the same email address you entered on the form."
    return render_template('reset_password.html', error=error, message=message)

@app.route('/set_password/<int:user_id>', methods=['GET', 'POST'])
def set_password(user_id):
    db = get_db()
    cursor = db.cursor()
    user_row = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user_row:
        return "User not found", 404
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            from werkzeug.security import generate_password_hash
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (generate_password_hash(password), user_id))
            db.commit()
            flash('Password set successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('set_password.html', user_id=user_id, error=error)
    return render_template('success.html', submission_id=submission_id, pdf_filename=pdf_filename)

from flask_login import login_required, current_user
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', lambda: False)():
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/download_filled_pdf/<filename>')
@login_required
def download_filled_pdf(filename):
    current_app.logger.info(f"--- download_filled_pdf --- Attempting to send file: {filename}")
    try:
        return send_from_directory(current_app.config['FILLED_FORMS_DIR'], filename, as_attachment=True)
    except FileNotFoundError:
        current_app.logger.error(f"--- download_filled_pdf --- File not found: {filename} in directory {current_app.config['FILLED_FORMS_DIR']}")
        flash(f"Error: Could not find the PDF file '{filename}'.", "danger")
        # Redirect to admin or a generic error page, or back to where they came from if possible
        # For simplicity, redirecting to admin view. Consider referrer if more context is needed.
        return redirect(url_for('admin_view')) # Or perhaps 'form' or a dedicated error page
    except Exception as e:
        current_app.logger.error(f"--- download_filled_pdf --- Unexpected error sending file {filename}: {e}", exc_info=True)
        flash(f"An unexpected error occurred while trying to download the PDF '{filename}'.", "danger")
        return redirect(url_for('admin_view')) # Or 'form'

@app.route('/admin', methods=['GET'])
@login_required # Protect the admin route
def admin_view():
    db = get_db()
    cursor = db.cursor()

    # Get the list of database column names needed for display from DESIRED_COLUMNS_ORDER_AND_HEADERS
    db_columns_for_display = [col_map[0] for col_map in DESIRED_COLUMNS_ORDER_AND_HEADERS]
    display_header_names = [
        'ID', 'Claimant Name', 'Email Address', 'Phone Number', 'Basis of Claim', 
        'Nature of Injury', 'Capitol Experience', 'Injuries/Damages',
        'Entry/Exit Time', 'Inside Capitol Details', 'Property Damage Amount',
        'Personal Injury Amount', 'Wrongful Death Amount', 'Total Claim Amount',
        'Signature', 'Type of Employment', 'Marital Status', 'Street Address',
        'City', 'State', 'Zip Code', 'Date and Time Created', 'Date and Time Signed'
    ]
    
    # Ensure 'id' (primary key) is selected for delete functionality,
    # and avoid duplicates if 'id' were ever mapped in DESIRED_COLUMNS_ORDER_AND_HEADERS
    select_columns_list = ['id'] + [col for col in db_columns_for_display if col != 'id']
    select_columns_str = ', '.join(select_columns_list)

    try:
        # Get distinct states for the filter dropdown
        # Hardcoded list of 50 US state codes in strict alphabetical order
        states_list_for_filter = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]
        current_app.logger.info(f"--- admin_view --- DEBUG: FINAL state list passed to template: {states_list_for_filter}")

        # Select the actual 'id' column along with others for the main table
        cursor.execute(f"SELECT {select_columns_str} FROM claims ORDER BY created_at DESC")
        raw_claims_data = cursor.fetchall() # List of sqlite3.Row objects
        
        claims_list_for_template = []
        for row in raw_claims_data:
            processed_row = {}
            processed_row['id'] = row['id'] # Explicitly add the database 'id' to the processed_row for use in the template
            for db_col, display_header in zip(db_columns_for_display, display_header_names):
                raw_value = row[db_col]
                if db_col == 'field18_date_of_signature' or db_col == 'created_at' or db_col == 'updated_at':
                    processed_row[display_header] = format_datetime_for_display(raw_value)
                elif db_col == 'field17_signature_of_claimant':
                    processed_row[display_header] = raw_value if raw_value else "Pending Signature"
                elif db_col == 'filled_pdf_filename': # This is the 'ID' column in display
                    processed_row[display_header] = raw_value if raw_value else "N/A"
                elif db_col == 'field_pdf_13b_phone':
                    processed_row[display_header] = format_phone(raw_value) if raw_value else "N/A"
                else:
                    processed_row[display_header] = raw_value if raw_value is not None else ''
            claims_list_for_template.append(processed_row)

        current_app.logger.info(f"Fetched {len(claims_list_for_template)} claims for admin view.")
        # Pass display_header_names for the table headers in the template
        return render_template('admin.html', title="Admin - View Submissions", claims=claims_list_for_template, column_names=display_header_names, states_for_filter=states_list_for_filter)
    except Exception as e:
        current_app.logger.error(f"--- admin_view --- Error fetching admin data: {e}", exc_info=True)
        # Also pass an empty list for states if there's an error fetching claims
        return render_template('admin.html', title="Admin - Error", claims=[], column_names=[], states_for_filter=[], error=f"An error occurred: {e}")

# New route for deleting a claim
@app.route('/admin/delete/<int:claim_id>', methods=['POST'])
def delete_claim(claim_id):
    pdf_filename_to_delete = None
    db = get_db() # Initialize db here to ensure it's available for rollback if needed
    try:
        cursor = db.cursor()
        
        # Step 1: Get the PDF filename BEFORE deleting the record
        cursor.execute("SELECT filled_pdf_filename FROM claims WHERE id = ?", (claim_id,))
        record = cursor.fetchone()
        if record and record['filled_pdf_filename']: # Check if record exists and has a filename
            pdf_filename_to_delete = record['filled_pdf_filename']
        elif not record:
            flash(f'Error: Submission with ID {claim_id} not found.', 'danger')
            current_app.logger.error(f"Attempted to delete non-existent claim with id {claim_id}.")
            return redirect(url_for('admin_view'))


        # Step 2: Delete the database record
        cursor.execute("DELETE FROM claims WHERE id = ?", (claim_id,))
        db.commit()
        flash_message = 'Submission record deleted successfully.'
        current_app.logger.info(f"Successfully deleted claim record with id: {claim_id}")

        # Step 3: Attempt to delete the PDF file if a filename was found
        if pdf_filename_to_delete:
            pdf_path = os.path.join(current_app.config['FILLED_FORMS_DIR'], pdf_filename_to_delete)
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                    flash_message += ' Associated PDF file also deleted.'
                    current_app.logger.info(f"Successfully deleted PDF file: {pdf_path}")
                else:
                    # This case means filename was in DB, but file not on disk
                    flash_message += ' Associated PDF file was not found on server.'
                    current_app.logger.warning(f"PDF file not found on disk, cannot delete: {pdf_path}")
            except OSError as e:
                # This case means file existed but couldn't be deleted (e.g., permissions)
                flash_message += f' Error deleting associated PDF file: {e}. Please check server logs and permissions.'
                current_app.logger.error(f"Error deleting PDF file {pdf_path}: {e}")
        else:
            # This case means the record existed but had no PDF filename linked in the DB
            flash_message += ' No associated PDF file was linked to this submission in the database.'
            current_app.logger.info(f"No PDF filename associated in DB for claim id {claim_id}.")
        
        flash(flash_message, 'success' if 'Error' not in flash_message and 'not found on server' not in flash_message else 'warning')

    except sqlite3.Error as e:
        # This handles errors during DB operations (SELECT or DELETE)
        if db: # Check if db was successfully initialized
             db.rollback()
        flash(f'Database error while deleting submission: {e}', 'danger')
        current_app.logger.error(f"Database error for claim id {claim_id}: {e}")
    # The 'finally' block for closing DB connection is handled by @app.teardown_appcontext
    return redirect(url_for('admin_view'))

@app.route('/download_csv')
def download_csv():
    db = get_db()
    cursor = db.cursor()

    db_column_names = [col_map[0] for col_map in DESIRED_COLUMNS_ORDER_AND_HEADERS]
    csv_header_names = [
        'ID', 'Claimant Name', 'Email Address', 'Phone Number', 'Basis of Claim', 
        'Nature of Injury', 'Capitol Experience', 'Injuries/Damages',
        'Entry/Exit Time', 'Inside Capitol Details', 'Property Damage Amount',
        'Personal Injury Amount', 'Wrongful Death Amount', 'Total Claim Amount',
        'Signature', 'Type of Employment', 'Marital Status', 'Street Address',
        'City', 'State', 'Zip Code', 'Date and Time Created', 'Date and Time Signed'
    ]
    select_columns_str = ', '.join(db_column_names)

    try:
        cursor.execute(f"SELECT {select_columns_str} FROM claims ORDER BY created_at DESC")
        claims_data_rows = cursor.fetchall() # List of sqlite3.Row objects

        if not claims_data_rows:
            flash('No data to export.', 'info')
            return redirect(url_for('admin_view'))

        csv_io = io.StringIO()
        csv_writer = csv.writer(csv_io)
        
        # Write headers
        headers = [col_header_pair[1] for col_header_pair in DESIRED_COLUMNS_ORDER_AND_HEADERS]
        csv_writer.writerow(headers)
        current_app.logger.info(f"--- download_csv --- CSV headers written: {headers}")

        # Write data rows
        for row in claims_data_rows:
            row_data_for_csv = []
            for db_col, _ in DESIRED_COLUMNS_ORDER_AND_HEADERS:
                raw_value = row[db_col]
                if db_col == 'field18_date_of_signature' or db_col == 'created_at' or db_col == 'updated_at':
                    row_data_for_csv.append(format_datetime_for_display(raw_value))
                elif db_col == 'field17_signature_of_claimant':
                    row_data_for_csv.append(raw_value if raw_value else "Pending Signature")
                elif db_col == 'filled_pdf_filename': # This is the 'ID' column in display
                    row_data_for_csv.append(raw_value if raw_value else "N/A")
                elif db_col == 'field_pdf_13b_phone':
                    row_data_for_csv.append(format_phone(raw_value))
                else:
                    row_data_for_csv.append(raw_value if raw_value is not None else '')
            csv_writer.writerow(row_data_for_csv)
        current_app.logger.info(f"--- download_csv --- Successfully wrote {len(claims_data_rows)} rows to CSV.")

        # Move to the beginning of the StringIO buffer
        csv_io.seek(0)

        return Response(
            csv_io,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=claims_export.csv"}
        )
    except sqlite3.Error as e:
        current_app.logger.error(f"Database error during CSV export: {e}")
        flash(f"Error exporting data: {e}", 'danger')
        return redirect(url_for('admin_view'))

@app.cli.command('init-db')
def init_db_command():
    with app.app_context():
        db = get_db()
    print('Initialized the database defined in app.config[DATABASE].')

@app.route('/login', methods=['GET', 'POST'])
def login():
    current_app.logger.info(f"LOGIN ROUTE: Method={request.method}, Form data={request.form}")
    form = LoginForm()
    current_app.logger.info("LOGIN: LoginForm instantiated")
    if request.method == 'POST':
        try:
            current_app.logger.info(f"LOGIN POST: form.username={form.username.data}, form.password={'*' * len(form.password.data) if form.password.data else ''}")
            current_app.logger.info("LOGIN: About to validate form")
            if not form.validate_on_submit():
                current_app.logger.warning(f"LOGIN: Form did not validate. Errors: {form.errors}")
                return render_template('login.html', title='Login', form=form)
            current_app.logger.info("LOGIN: Form validated successfully")
            email = form.username.data.lower().strip()
            password = form.password.data
            # Validate email format
            import re
            email_regex = r'^\S+@\S+\.\S+$'
            if not re.match(email_regex, email):
                current_app.logger.warning(f"LOGIN: Invalid email format: {email}")
                flash('Please enter a valid email address.', 'danger')
            else:
                current_app.logger.info(f"LOGIN: Checking for existing user: {email}")
                user = User.get_by_username(email)
                if user:
                    current_app.logger.info(f"LOGIN: User found for {email}, attempting password check.")
                    # Normal login flow
                    if user.check_password(password):
                        current_app.logger.info(f"LOGIN: Password correct for {email}, logging in.")
                        login_user(user)
                        flash('Login successful!', 'success')
                        next_page = request.args.get('next')
                        return redirect(next_page or url_for('admin_view'))
                    else:
                        current_app.logger.warning(f"LOGIN: Incorrect password for {email}.")
                        flash('Login Unsuccessful. Please check email and password.', 'danger')
                else:
                    current_app.logger.info(f"LOGIN: No user found for {email}, attempting user creation.")
                    # No user exists: create account and redirect to set password
                    import secrets
                    temp_password = secrets.token_urlsafe(10)
                    created = User.create_user(email, temp_password, role='user')
                    current_app.logger.info(f"LOGIN: User.create_user returned: {created}")
                    if created:
                        new_user = User.get_by_username(email)
                        current_app.logger.info(f"LOGIN: Successfully created user {email}, id={new_user.id if new_user else None}")
                        flash('Account created! Please set your password.', 'success')
                        return redirect(url_for('set_password', user_id=new_user.id))
                    else:
                        current_app.logger.error(f"LOGIN: Failed to create user for {email}")
                        flash('Account creation failed. Please try again or contact support.', 'danger')
        except Exception as e:
            current_app.logger.error(f"LOGIN: Exception in POST handler: {e}")
            flash('An unexpected error occurred during login. Please try again or contact support.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.logger.info("Starting Flask development server.") # Use app.logger here
    app.run(debug=True, port=61663)

# --- ROUTE DEBUGGING SNIPPET ---
print("=== FLASK APP.PY STARTED ===")
print("REGISTERED ROUTES:")
for rule in app.url_map.iter_rules():
    print(rule, rule.endpoint)
# --- END ROUTE DEBUGGING SNIPPET ---
