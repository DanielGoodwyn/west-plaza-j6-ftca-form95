import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s') # Force basic logging

from flask import Flask, render_template, request, redirect, url_for, g, current_app, flash
import sqlite3
import os
import logging
from logging import FileHandler
from datetime import datetime
from fillpdf import fillpdfs # Added import for get_form_fields

# Import utility functions
from utils.pdf_filler import fill_sf95_pdf # Corrected import name
import utils.pdf_filler # Import the module itself to check its path
logging.info(f"***** PY LOGGING: IMPORTED pdf_filler FROM: {utils.pdf_filler.__file__} *****") # DEBUG PATH with Python logging
# from utils.notifier import send_notification_email # To be created

app = Flask(__name__)
app.logger.setLevel(logging.INFO) # Set logger level to INFO to see detailed logs
app.secret_key = os.urandom(24) # For session management, CSRF protection later

# --- Configuration ---
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'form_data.db')
PDF_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'sf95-illustrator-acrobat.pdf') # Updated PDF name
FILLED_PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'filled_forms')

# Ensure data directories exist
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'), exist_ok=True)
os.makedirs(FILLED_PDF_DIR, exist_ok=True)

# --- Database Setup ---
def get_db():
    if 'db' not in g:
        # Ensure data directory exists before trying to connect/create DB file
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
                current_app.logger.info(f"Created data directory: {data_dir} from get_db")
            except Exception as e_mkdir:
                current_app.logger.error(f"Failed to create data directory {data_dir} from get_db: {e_mkdir}")
                # Decide if to raise or handle, for now log and continue, connect may fail

        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

def create_tables_if_not_exist():
    current_app.logger.info("Entered create_tables_if_not_exist function.")
    db = get_db()
    cursor = db.cursor()
    current_app.logger.info("Successfully obtained DB cursor.")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='submissions';")
    table_exists_row = cursor.fetchone()
    table_exists = table_exists_row is not None
    current_app.logger.info(f"Checking 'submissions' table. Exists: {table_exists}")

    DB_SCHEMA = [
        'field2_name TEXT',
        'field2_address TEXT',
        'field2_city TEXT',
        'field2_state TEXT',
        'field2_zip TEXT',
        'field_pdf_4_dob TEXT',              # Renamed from field2_dob
        'field3_type_employment TEXT',       # Replaces field3_military, civilian, other, other_specify
        'field_pdf_5_marital_status TEXT',   # Renamed from field4_marital_status
        'field8_basis_of_claim TEXT',
        'field10_nature_of_injury TEXT',
        'field12a_property_damage REAL DEFAULT 0.00',
        'field12b_personal_injury REAL',
        'field12c_wrongful_death REAL',
        'field12d_total REAL',
        'field_pdf_13b_phone TEXT',          # New phone field from signature block
        'field_pdf_13b_signature_data TEXT', # For signature data URL (was field13b_signature)
        'field14_date_signed TEXT',
        'filled_pdf_filename TEXT'
    ]

    if not table_exists:
        current_app.logger.info(f"'submissions' table does not exist. Creating it based on DB_SCHEMA: {DB_SCHEMA}")
        columns_with_types = ", ".join(DB_SCHEMA)
        create_table_sql = f"CREATE TABLE submissions (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns_with_types}, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        current_app.logger.info(f"Executing CREATE TABLE SQL: {create_table_sql}")
        try:
            cursor.execute(create_table_sql)
            db.commit()
            current_app.logger.info("Database table 'submissions' created successfully.")
        except sqlite3.Error as e_create:
            current_app.logger.error(f"Failed to create 'submissions' table: {e_create}")
            # If table creation fails, it's a critical error, re-raise or handle appropriately
            raise
    else:
        current_app.logger.info("'submissions' table exists. Checking for missing columns based on DB_SCHEMA.")
        cursor.execute("PRAGMA table_info(submissions)")
        existing_columns_rows = cursor.fetchall()
        existing_columns = [row[1] for row in existing_columns_rows]
        current_app.logger.info(f"Existing columns in 'submissions': {existing_columns}")
        current_app.logger.info(f"DB_SCHEMA to check against: {DB_SCHEMA}")
        
        schema_column_definitions = {}
        for entry in DB_SCHEMA:
            parts = entry.strip().split(maxsplit=1)
            col_name = parts[0]
            col_type = parts[1] if len(parts) > 1 else "TEXT"
            schema_column_definitions[col_name] = f"{col_name} {col_type}"

        current_app.logger.info(f"Parsed schema column definitions from DB_SCHEMA: {schema_column_definitions}")

        missing_cols_added_count = 0
        for col_name, col_definition in schema_column_definitions.items():
            if col_name not in existing_columns:
                current_app.logger.info(f"Column '{col_name}' is missing from 'submissions' table. Attempting to add with definition: '{col_definition}'")
                try:
                    alter_sql = f"ALTER TABLE submissions ADD COLUMN {col_definition}"
                    current_app.logger.info(f"Executing ALTER TABLE SQL: {alter_sql}")
                    cursor.execute(alter_sql)
                    db.commit()
                    current_app.logger.info(f"Successfully added column: {col_definition} to 'submissions' table.") # Fixed typo: definition -> col_definition
                    missing_cols_added_count += 1
                except sqlite3.Error as e_alter:
                    current_app.logger.error(f"Error adding column {col_definition} to 'submissions' table: {e_alter}. Existing columns were: {existing_columns}")
                    # Optionally, re-raise or handle. For now, log and continue checking other columns.
            else:
                current_app.logger.info(f"Column '{col_name}' already exists in 'submissions' table.")
        
        if missing_cols_added_count > 0:
            current_app.logger.info(f"Finished schema update. Added {missing_cols_added_count} missing columns to 'submissions' table.")
        else:
            current_app.logger.info("'submissions' table schema appears up to date with DB_SCHEMA. No columns were added.")
    current_app.logger.info("Exiting create_tables_if_not_exist function.")
    # The connection g.db is managed by teardown_appcontext, no conn.close() here.

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def initialize_app_state():
    # Configure file logging
    log_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.log') # Project root
    file_handler = FileHandler(log_file_path, mode='w')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]')
    file_handler.setFormatter(formatter)
    
    # Add handler to current_app.logger if it's not already there
    # and also to Flask's root logger to catch more general Flask logs if desired
    if not any(isinstance(h, FileHandler) and h.baseFilename == file_handler.baseFilename for h in current_app.logger.handlers):
        current_app.logger.addHandler(file_handler)
    
    current_app.logger.setLevel(logging.INFO) # Ensure app logger processes INFO level

    current_app.logger.info("Running initialize_app_state during app setup. File logging configured.")
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        current_app.logger.info(f"Created data directory: {data_dir}")
    
    try:
        create_tables_if_not_exist()
        current_app.logger.info("Database schema checked/initialized successfully during app setup.")
    except Exception as e:
        current_app.logger.error(f"Error during initialize_app_state: {e}")
        # Depending on severity, you might want to re-raise to stop app startup
        raise # If DB init fails, it's critical

# Run initialization logic after app is created and configured
with app.app_context():
    initialize_app_state()

# --- Routes ---
@app.route('/')
def form():
    today_date = datetime.today().strftime('%Y-%m-%d')
    default_values = {
        'field1_agency': "DEPARTMENT OF JUSTICE",
        'field2_name': 'AJ Fish',
        'field2_address': '123 Main Street',
        'field2_city': 'Lakeland',
        'field2_state': 'FL',
        'field2_zip': '33801',
        'field3_type_employment': 'Civilian',
        'field_pdf_4_dob': '1991-01-06', # Set default DOB
        'field_pdf_5_marital_status': 'Single',
        'field8_basis_of_claim': "While the claimant was protesting on January 6, 2021 at the West side of the U.S. Capitol, the Capitol Police and D.C. Metropolitan Police acting on behalf of the Capitol Police used excessive force against the claimant causing claimant physical injuries. The excessive force took the form of various munitions launched against the protesters including but not limited to: pepper balls, rubber balls or bullets some filled with Oleoresin Capsicum (“OC”), FM 303 projectiles, sting balls, flash bang, sting bomb and tear gas grenades, tripple chasers,pepper spray, CS Gas and physical strikes with firsts or batons.",
        'field10_nature_of_injury': "The claimant went to the U.S. Capitol to peacefully protest the presidential election. While the claimant was in the area of the West Side of the U.S. Capitol building police launched weapons referenced above and used excessive force. The claimant was struck and or exposed to the launched munitions and/or OC or CS Gas and suffered injuries as a result. The legal ramifications of these actions are currently under review and form part of the ongoing damages being claimed.",
        'field12a_property_damage_amount': '0.00',
        'field12b_personal_injury_amount': '90000.00',
        'field12c_wrongful_death_amount': '0.00',
        'field12d_total_amount': '90000.00', # Sum of 12a, 12b, 12c for consistency
        'field_pdf_13b_phone': '8138381299',
        'field14_date_signed': today_date,
        # Add default values for signature image data if needed, e.g., a placeholder text for the hidden field
        'field_pdf_13b_signature_data': '' # Or some placeholder if the JS expects it
    }
    return render_template('form.html', default_values=default_values)

@app.route('/list_pdf_fields', methods=['GET'])
def list_pdf_fields_route():
    try:
        fields = fillpdfs.get_form_fields(PDF_TEMPLATE_PATH)
        print("\n--- Detected PDF Form Fields ---")
        for field_name, field_value in fields.items():
            print(f"Field Name: '{field_name}', Current Value: '{field_value}'")
        print("--- End of PDF Form Fields ---\n")
        return "PDF fields printed to Flask console. Please check your terminal.", 200
    except Exception as e:
        print(f"Error getting PDF fields: {e}")
        return f"Error getting PDF fields: {e}", 500

@app.route('/submit', methods=['POST'])
def submit_form():
    db = None  # Initialize db to None at the top of the function scope
    form_data = request.form
    try:
        # Prepare data for database insertion, matching new schema and HTML names
        data_to_save = {
            'FIELD2_NAME': form_data.get('field2_name'),
            'FIELD2_ADDRESS': form_data.get('field2_address'),
            'FIELD2_CITY': form_data.get('field2_city'),
            'FIELD2_STATE': form_data.get('field2_state'),
            'FIELD2_ZIP': form_data.get('field2_zip'),
            'FIELD_PDF_4_DOB': form_data.get('field_pdf_4_dob'), # New HTML name
            'FIELD3_TYPE_EMPLOYMENT': form_data.get('field3_type_employment'), # New HTML name
            'FIELD_PDF_5_MARITAL_STATUS': form_data.get('field_pdf_5_marital_status'), # New HTML name
            'FIELD8_BASIS_OF_CLAIM': form_data.get('field8_basis_of_claim'),
            'FIELD10_NATURE_OF_INJURY': form_data.get('field10_nature_of_injury'),
            'FIELD12A_PROPERTY_DAMAGE_AMOUNT': form_data.get('field12a_property_damage_amount', type=float, default=0.0),
            'FIELD12B_PERSONAL_INJURY_AMOUNT': form_data.get('field12b_personal_injury_amount', type=float, default=0.0), # Added default
            'FIELD12C_WRONGFUL_DEATH_AMOUNT': form_data.get('field12c_wrongful_death_amount', type=float, default=0.0),
            'FIELD12D_TOTAL_AMOUNT': form_data.get('field12d_total_amount', type=float, default=0.0), # Added default
            'FIELD_PDF_13B_PHONE': form_data.get('field_pdf_13b_phone'), # New HTML name
            'FIELD_PDF_13B_SIGNATURE_DATA': form_data.get('field_pdf_13b_signature_data'), # New HTML name for signature data
            'FIELD14_DATE_SIGNED': form_data.get('field14_date_signed')
        }

        # Generate filled PDF
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_pdf_filename = f"SF95_filled_{timestamp_str}.pdf"
        # Ensure FILLED_PDF_DIR exists (it should be created by initialize_app_state, but good practice to check)
        if not os.path.exists(FILLED_PDF_DIR):
            os.makedirs(FILLED_PDF_DIR)
            current_app.logger.info(f"Created FILLED_PDF_DIR during submit at: {FILLED_PDF_DIR}")
        output_pdf_path = os.path.join(FILLED_PDF_DIR, output_pdf_filename)
        
        # Pass the current pdf_data_map, template path, and output path to the filler function
        # Ensure fill_sf95_pdf expects a dict for form_data if it does complex operations on it.
        actual_pdf_path = fill_sf95_pdf(form_data.to_dict(), PDF_TEMPLATE_PATH, output_pdf_path)

        if not actual_pdf_path:
            current_app.logger.error(f"Error filling PDF. Form data: {form_data.to_dict()}")
            flash("There was an error generating the PDF. Please check the server logs and try again.", 'danger')
            return redirect(url_for('form'))

        # Save to database
        db = get_db() # Assign to the db variable scoped to the function
        cursor = db.cursor()
        
        # SQL query uses lowercase column names as per DB_SCHEMA
        sql_query = '''
        INSERT INTO submissions (
            field2_name, field2_address, field2_city, field2_state, field2_zip,
            field_pdf_4_dob, field3_type_employment, field_pdf_5_marital_status,
            field8_basis_of_claim, field10_nature_of_injury,
            field12a_property_damage, field12b_personal_injury, field12c_wrongful_death, field12d_total,
            field_pdf_13b_phone, field_pdf_13b_signature_data, field14_date_signed,
            filled_pdf_filename
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        # values_tuple matches the order of columns in INSERT and uses data_to_save (UPPERCASE keys)
        values_tuple = (
            data_to_save['FIELD2_NAME'], data_to_save['FIELD2_ADDRESS'], data_to_save['FIELD2_CITY'], 
            data_to_save['FIELD2_STATE'], data_to_save['FIELD2_ZIP'],
            data_to_save['FIELD_PDF_4_DOB'], data_to_save['FIELD3_TYPE_EMPLOYMENT'], 
            data_to_save['FIELD_PDF_5_MARITAL_STATUS'], data_to_save['FIELD8_BASIS_OF_CLAIM'], 
            data_to_save['FIELD10_NATURE_OF_INJURY'],
            data_to_save['FIELD12A_PROPERTY_DAMAGE_AMOUNT'], data_to_save['FIELD12B_PERSONAL_INJURY_AMOUNT'],
            data_to_save['FIELD12C_WRONGFUL_DEATH_AMOUNT'], data_to_save['FIELD12D_TOTAL_AMOUNT'],
            data_to_save['FIELD_PDF_13B_PHONE'], data_to_save['FIELD_PDF_13B_SIGNATURE_DATA'],
            data_to_save['FIELD14_DATE_SIGNED'],
            output_pdf_filename # Storing only the filename
        )
        
        cursor.execute(sql_query, values_tuple)
        submission_id = cursor.lastrowid
        db.commit()
        
        current_app.logger.info(f"Submission {submission_id} successfully saved with PDF: {output_pdf_filename}")
        flash(f"Form submitted successfully! Submission ID: {submission_id}", 'success')
        return redirect(url_for('success_page', submission_id=submission_id))

    except sqlite3.Error as e:
        if db:  # Check if db connection was established
            db.rollback()
        # Log the detailed error and the form data that caused it
        current_app.logger.error(f"Database error during submission: {e}. Form data: {form_data.to_dict()}", exc_info=True)
        flash(f'A database error occurred: {str(e)}. Please try again.', 'danger')
        return redirect(url_for('form'))
    except Exception as e:
        if db:  # If an error occurred after db connection was made
            db.rollback()
        # Log the detailed error and the form data
        current_app.logger.error(f"Unexpected error during submission: {e}. Form data: {form_data.to_dict()}", exc_info=True)
        flash('An unexpected error occurred. Please check server logs and try again.', 'danger')
        return redirect(url_for('form')) # Corrected endpoint

@app.route('/success/<int:submission_id>')
def success_page(submission_id):
    return f"<h1>Form Submitted Successfully!</h1><p>Your Submission ID is: {submission_id}</p><p><a href='{url_for('form')}'>Submit another form</a></p>"

@app.cli.command('init-db')
def init_db_command():
    create_tables_if_not_exist()
    print('Initialized the database.')

if __name__ == '__main__':
    # Create instance folder if it doesn't exist, for the SQLite DB
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as e:
        print(f"Error creating instance folder: {e}")
    
    app.run(debug=True, host=app.config.get('FLASK_RUN_HOST'), port=5003) # Explicitly set port to 5003
