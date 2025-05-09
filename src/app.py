import sqlite3
import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, current_app, g # Added g
from fillpdf import fillpdfs # Added import for get_form_fields

# Import utility functions
from utils.pdf_filler import fill_sf95_pdf, DEFAULT_VALUES as PDF_FILLER_DEFAULTS # Renamed for clarity
import utils.pdf_filler # Import the module itself to check its path
# from utils.notifier import send_notification_email # To be created

app = Flask(__name__)
app.logger.setLevel(logging.INFO) # Set logger level to INFO to see detailed logs
app.secret_key = os.urandom(24) # For session management, CSRF protection later

# --- Configuration ---
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'form_data.db')
PDF_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'sf95.pdf') # Updated PDF name
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
    file_handler = logging.FileHandler(log_file_path, mode='w')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]')
    file_handler.setFormatter(formatter)
    
    # Add handler to current_app.logger if it's not already there
    # and also to Flask's root logger to catch more general Flask logs if desired
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == file_handler.baseFilename for h in current_app.logger.handlers):
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
    # This dictionary provides rich default values for HTML form fields for easy debugging
    html_form_defaults = {
        'field1_agency': PDF_FILLER_DEFAULTS.get('field1_agency', "DEPARTMENT OF JUSTICE"), # Agency is special, might be from PDF_FILLER_DEFAULTS or a hardcoded app default
        'field2_name': 'AJ Fish Debug',
        'field2_address': '123 Debugger Lane',
        'field2_city': 'Testville',
        'field2_state': 'FL',
        'field2_zip': '33800',
        'field3_type_employment': 'Civilian',
        'field_pdf_4_dob': '1990-01-01',
        'field_pdf_5_marital_status': 'Single',
        'field8_basis_of_claim': PDF_FILLER_DEFAULTS.get('field8_basis_of_claim', "Basis of claim debug text: Specific incident involving negligence by federal employees."),
        'field10_nature_of_injury': PDF_FILLER_DEFAULTS.get('field10_nature_of_injury', "Nature of injury debug text: Resulting physical and emotional distress."),
        'field12a_property_damage_amount': '10.00',
        'field12b_personal_injury_amount': '90000.00', # Changed back to 90000.00
        'field12c_wrongful_death_amount': '0.00',
        # Total is usually calculated, but can have a default for display if needed
        'field12d_total_amount': '90010.00', # Adjusted total to reflect 90000+10
        'field_pdf_13b_phone': '555-123-4567',
        'field14_date_signed': today_date,
        'field13a_signature': '' # Empty for typed signature or placeholder
    }
    return render_template('form.html', default_values=html_form_defaults, title="SF-95 Claim Form")

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
    
    # Server-side validation
    validation_errors = {}
    required_fields = {
        'field2_name': "Claimant's Name",
        'field2_address': "Claimant's Address",
        'field2_city': "Claimant's City",
        'field2_state': "Claimant's State",
        'field2_zip': "Claimant's ZIP Code",
        'field_pdf_4_dob': "Claimant's Date of Birth",
        'field3_type_employment': "Claimant's Type of Employment",
        'field_pdf_5_marital_status': "Claimant's Marital Status",
        'field8_basis_of_claim': "Basis of Claim",
        'field10_nature_of_injury': "Nature and Extent of Personal Injury",
        # Amount fields (12a, 12b, 12c, 12d) are numeric, validation for format handled below
        # Signature and Date Signed are crucial
        'field13a_signature': "Signature", # Assuming this holds the signature data
        'field14_date_signed': "Date Signed"
    }

    for field, name in required_fields.items():
        if not form_data.get(field):
            validation_errors[field] = f"{name} is required."

    # Date validation (format YYYY-MM-DD)
    date_fields_to_validate = {
        'field_pdf_4_dob': "Claimant's Date of Birth",
        'field14_date_signed': "Date Signed"
    }
    for field, name in date_fields_to_validate.items():
        date_value = form_data.get(field)
        if date_value:
            try:
                datetime.strptime(date_value, '%Y-%m-%d')
            except ValueError:
                validation_errors[field] = f"{name} must be in YYYY-MM-DD format."
        elif field in required_fields: # Ensure required date fields aren't just empty
             validation_errors.setdefault(field, f"{name} is required and must be in YYYY-MM-DD format.")


    if validation_errors:
        current_app.logger.warning(f"Validation errors: {validation_errors} for form data: {form_data}")
        # When validation fails, re-render the form with errors, existing form_data, and HTML_FORM_DEFAULTS
        today_date = datetime.today().strftime('%Y-%m-%d')
        html_form_defaults_for_error = {
            'field1_agency': PDF_FILLER_DEFAULTS.get('field1_agency', "DEPARTMENT OF JUSTICE"),
            'field2_name': 'AJ Fish Debug',
            'field2_address': '123 Debugger Lane',
            'field2_city': 'Testville',
            'field2_state': 'FL',
            'field2_zip': '33800',
            'field3_type_employment': 'Civilian',
            'field_pdf_4_dob': '1990-01-01',
            'field_pdf_5_marital_status': 'Single',
            'field8_basis_of_claim': PDF_FILLER_DEFAULTS.get('field8_basis_of_claim', "Basis of claim debug text: Specific incident involving negligence by federal employees."),
            'field10_nature_of_injury': PDF_FILLER_DEFAULTS.get('field10_nature_of_injury', "Nature of injury debug text: Resulting physical and emotional distress."),
            'field12a_property_damage_amount': '10.00',
            'field12b_personal_injury_amount': '90000.00', # Changed back to 90000.00
            'field12c_wrongful_death_amount': '0.00',
            'field12d_total_amount': '90010.00', # Adjusted total to reflect 90000+10
            'field_pdf_13b_phone': '555-123-4567',
            'field14_date_signed': today_date,
            'field13a_signature': ''
        }
        # User's submitted form_data should take precedence for fields they've filled
        # The template should handle this by checking form_data first, then default_values
        return render_template('form.html', form_data=form_data, title="SF-95 Claim Form", validation_errors=validation_errors, default_values=html_form_defaults_for_error), 400

    try:
        # --- Prepare data for PDF --- 
        data_to_save = {
            'FIELD2_NAME': form_data.get('field2_name'),
            'FIELD2_ADDRESS': form_data.get('field2_address'),
            'FIELD2_CITY': form_data.get('field2_city'),
            'FIELD2_STATE': form_data.get('field2_state'),
            'FIELD2_ZIP': form_data.get('field2_zip'),
            'FIELD_PDF_4_DOB': form_data.get('field_pdf_4_dob'),
            'FIELD3_TYPE_EMPLOYMENT': form_data.get('field3_type_employment'),
            'FIELD_PDF_5_MARITAL_STATUS': form_data.get('field_pdf_5_marital_status'),
            'FIELD8_BASIS_OF_CLAIM': form_data.get('field8_basis_of_claim'),
            'FIELD10_NATURE_OF_INJURY': form_data.get('field10_nature_of_injury'),
            'FIELD12A_PROPERTY_DAMAGE_AMOUNT': form_data.get('field12a_property_damage_amount', type=float, default=0.0),
            'FIELD12B_PERSONAL_INJURY_AMOUNT': form_data.get('field12b_personal_injury_amount', type=float, default=0.0),
            'FIELD12C_WRONGFUL_DEATH_AMOUNT': form_data.get('field12c_wrongful_death_amount', type=float, default=0.0),
            'FIELD12D_TOTAL_AMOUNT': form_data.get('field12d_total_amount', type=float, default=0.0),
            'FIELD_PDF_13B_PHONE': form_data.get('field_pdf_13b_phone'),
            # Map the typed signature from field13a_signature to the database column
            'FIELD_PDF_13B_SIGNATURE_DATA': form_data.get('field13a_signature'), 
            'FIELD14_DATE_SIGNED': form_data.get('field14_date_signed'),
            'FILLED_PDF_FILENAME': None  # Placeholder, will be updated after PDF generation
        }

        # Prepare the dictionary to be passed to the PDF filler
        pdf_data_for_filling = {
            # Field 1 (Agency) - Handled by DEFAULT_VALUES in pdf_filler.py if not overridden
            'field1_agency': form_data.get('field1_agency'), 

            # Field 2 (Claimant Info) - We will address this specifically later with 'field2_claimant_info_combined'
            # For now, pass individual components if they exist in form_data, though pdf_filler might not use them directly yet
            'field2_name': form_data.get('field2_name'),
            'field2_address': form_data.get('field2_address'),
            'field2_city': form_data.get('field2_city'),
            'field2_state': form_data.get('field2_state'),
            'field2_zip': form_data.get('field2_zip'),

            # Field 3 (Employment)
            'field3_type_employment': form_data.get('field3_type_employment'), # Keep sending the text value
            'field3_other_specify': form_data.get('field3_other_specify'),
            # Checkbox-specific keys will be added below

            # Field 4 & 5 (DOB, Marital Status)
            'field_pdf_4_dob': form_data.get('field_pdf_4_dob'),
            'field_pdf_5_marital_status': form_data.get('field_pdf_5_marital_status'),

            # Field 6 & 7 (Incident Date/Time) - Handled by DEFAULT_VALUES in pdf_filler.py if not overridden
            'field6_date_of_incident': form_data.get('field6_date_of_incident'),
            'field7_time_of_incident': form_data.get('field7_time_of_incident'),

            # Field 8 (Basis of Claim)
            'field8_basis_of_claim': form_data.get('field8_basis_of_claim'),

            # Field 9 (Property Damage - Owner & Description)
            'field9_owner_name_address': form_data.get('field9_owner_name_address'),
            'field9_property_damage_description': form_data.get('field9_property_damage_description'), # Matches HTML input
            # Note: The HTML form uses 'field9_property_damage_description_vehicle' and 'field9_property_damage_description_other'.
            # We might need to combine these or decide which one maps to PDF's 'field9_property_damage_description'.
            # For now, assuming a direct field or that defaults in pdf_filler are desired if these are empty.

            # Field 10 (Nature of Injury)
            'field10_nature_of_injury': form_data.get('field10_nature_of_injury'),

            # Field 11 (Witnesses)
            'field11_witness_name': form_data.get('field11_witness_name'),
            'field11_witness_address': form_data.get('field11_witness_address'),

            # Field 12 (Amounts)
            'field12a_property_damage': form_data.get('field12a_property_damage_amount'), # Map from _amount key
            'field12b_personal_injury': form_data.get('field12b_personal_injury_amount'), # Map from _amount key
            'field12c_wrongful_death': form_data.get('field12c_wrongful_death_amount'), # Map from _amount key
            'field12d_total': form_data.get('field12d_total_amount'), # Map from _amount key

            # Field 13 (Signature & Phone)
            'field13a_signature': form_data.get('field13a_signature'), # This is the key PDF_FIELD_MAP uses for the signature box
            'field_pdf_13b_phone': form_data.get('field_pdf_13b_phone'),
            # Also ensure the DB key for signature is populated if 'field13a_signature' is what we are using for PDF
            'field_pdf_13b_signature_data': form_data.get('field13a_signature'), 

            # Field 14 (Date Signed)
            'field14_date_signed': form_data.get('field14_date_signed'),

            # Fields 15-19 (Insurance) - Pass them through if submitted
            'field15_accident_insurance': form_data.get('field15_accident_insurance'),
            'field15_insurer_name_address_policy': form_data.get('field15_insurer_name_address_policy'),
            'field16_filed_claim': form_data.get('field16_filed_claim'),
            'field16_claim_details': form_data.get('field16_claim_details'),
            'field17_deductible_amount': form_data.get('field17_deductible_amount'),
            'field18_insurer_action': form_data.get('field18_insurer_action'),
            'field19_insurer_name_address': form_data.get('field19_insurer_name_address')
        }

        # Handle Field 3 (Employment) checkboxes
        employment_type = form_data.get('field3_type_employment')
        if employment_type == 'Civilian':
            pdf_data_for_filling['field3_checkbox_civilian'] = True
        elif employment_type == 'Military':
            pdf_data_for_filling['field3_checkbox_military'] = True

        # Special handling for field2_claimant_info_combined (will be addressed more thoroughly next)
        # For now, let's ensure it's constructed if individual parts are present
        name = pdf_data_for_filling.get('field2_name', '')
        address = pdf_data_for_filling.get('field2_address', '')
        city = pdf_data_for_filling.get('field2_city', '')
        state_val = pdf_data_for_filling.get('field2_state', '') # Renamed to avoid conflict with 'state' module
        zip_code = pdf_data_for_filling.get('field2_zip', '')
        if name or address or city or state_val or zip_code: # only construct if there's something to combine
            pdf_data_for_filling['field2_claimant_info_combined'] = f"{name}\n{address}\n{city}, {state_val} {zip_code}".strip()
        else:
            # If all parts are empty, we don't want to send an empty 'field2_claimant_info_combined'
            # Let pdf_filler handle it (it will skip if not in form_data and no default)
            if 'field2_claimant_info_combined' in pdf_data_for_filling:
                 del pdf_data_for_filling['field2_claimant_info_combined']

        # Call the PDF filling utility with the prepared data
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_pdf_filename = f"SF95_filled_{timestamp_str}.pdf"
        # Ensure FILLED_PDF_DIR exists (it should be created by initialize_app_state, but good practice to check)
        if not os.path.exists(FILLED_PDF_DIR):
            os.makedirs(FILLED_PDF_DIR)
            current_app.logger.info(f"Created FILLED_PDF_DIR during submit at: {FILLED_PDF_DIR}")
        output_pdf_path = os.path.join(FILLED_PDF_DIR, output_pdf_filename)
        
        actual_pdf_path = fill_sf95_pdf(pdf_data_for_filling, PDF_TEMPLATE_PATH, output_pdf_path)

        if not actual_pdf_path:
            current_app.logger.error(f"Error filling PDF. PDF filler data: {pdf_data_for_filling}")
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
    except Exception as e:
        current_app.logger.error(f"Error during PDF generation or database saving: {str(e)}", exc_info=True)
        current_app.logger.error(f"Data that caused error: {pdf_data_for_filling}")
        flash('An unexpected error occurred while processing your form. Please try again or contact support.', 'danger')
        return redirect(url_for('form'))

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
        app.logger.error(f"Error creating instance folder: {e}")
        # Handle error appropriately, e.g., exit or log
    app.logger.info("Starting Flask development server.")
    app.run(debug=True, port=61662) # No port specified, Flask default is 5000
