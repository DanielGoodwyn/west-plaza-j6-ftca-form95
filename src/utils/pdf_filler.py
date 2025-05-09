import os
import json
import subprocess
import tempfile
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)

# --- Explicit logger configuration for debugging-logs.txt ---
# Construct path to debugging-logs.txt in the project root directory
# (one level up from 'src', then into project root)
# Corrected path: three levels up from src/utils/pdf_filler.py to reach project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
debug_log_path = os.path.join(project_root, 'debugging-logs.txt')
# Path to the new PDF field map
PDF_FIELD_MAP_PATH = os.path.join(project_root, 'data', 'pdf_field_map.json')

# Load the PDF field map from JSON
try:
    with open(PDF_FIELD_MAP_PATH, 'r') as f:
        PDF_FIELD_MAP = json.load(f)
except FileNotFoundError:
    logger.error(f"Critical: PDF field map file not found at {PDF_FIELD_MAP_PATH}")
    PDF_FIELD_MAP = {} # Fallback to empty map to prevent crash, but filling will fail
except json.JSONDecodeError:
    logger.error(f"Critical: Error decoding JSON from PDF field map file at {PDF_FIELD_MAP_PATH}")
    PDF_FIELD_MAP = {} # Fallback

# Remove any existing handlers from this specific logger to prevent duplicate logs
# or interference from other configurations (like basicConfig if it affected this logger).
if logger.hasHandlers():
    logger.handlers.clear()

debug_file_handler = logging.FileHandler(debug_log_path, mode='w') # 'w' for overwrite
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')
debug_file_handler.setFormatter(formatter)
logger.addHandler(debug_file_handler)
logger.setLevel(logging.DEBUG) # Ensure this logger captures DEBUG level messages
# --- End explicit logger configuration ---

# Default values for fields that are pre-filled or have fallbacks
# These keys should match the application-side keys used in PDF_FIELD_MAP
DEFAULT_VALUES = {
    'field1_agency': 'United States Capitol Police\n119 D Street, NE\nWashington, DC 20510',
    'field6_date_of_incident': '01/06/2021',
    'field7_time_of_incident': '1:06 P.M.', # Corrected as per your previous form defaults
    'field8_basis_of_claim': "While the claimant was protesting on January 6, 2021 at the West side of the U.S. Capitol, the Capitol Police and D.C. Metropolitan Police acting on behalf of the Capitol Police used excessive force against the claimant causing claimant physical injuries. The excessive force took the form of various munitions launched against the protesters including but not limited to: pepper balls, rubber balls or bullets some filled with Oleoresin Capsicum (\"OC\"), FM 303 projectiles, sting balls, flash bang, sting bomb and tear gas grenades, tripple chasers,pepper spray, CS Gas and physical strikes with firsts or batons.",
    'field9_owner_name_address': 'N/A',
    'field9_property_damage_description': 'N/A', # Corresponds to 'BRIEFLY DESCRIBE THE PROPERTY, NATURE AN'
    'field10_nature_of_injury': "The claimant went to the U.S. Capitol to peacefully protest the presidential election. While the claimant was in the area of the West Side of the U.S. Capitol building police launched weapons referenced above and used excessive force. The claimant was struck and or exposed to the launched munitions and/or OC or CS Gas and suffered injuries as a result. The legal ramifications of these actions are currently under review and form part of the ongoing damages being claimed.",
    'field11_witness_name': 'See FBI and Capitol Police database',
    'field11_witness_address': 'The FBI and Capitol Police already maintain a database of 1,000+ witnesses',
    'field12a_property_damage': '0.00',
    'field12b_personal_injury': '90000.00',
    'field12c_wrongful_death': '0.00'
    # field12d_total is calculated in app.py, not a direct default here
    # field13a_signature, field_pdf_13b_phone, field14_date_signed are user-input
}

def fill_sf95_pdf(form_data, pdf_template_path_param, output_pdf_full_path_param):
    logger.info(f"-------------------- Entering fill_sf95_pdf --------------------")
    logger.info(f"PDF Template Path: {pdf_template_path_param}")
    logger.info(f"Output PDF Path: {output_pdf_full_path_param}")
    logger.debug(f'Raw form_data received by fill_sf95_pdf: {form_data}')

    # Initialize pdfcpu_data to match the structure from 'pdfcpu form export'
    pdfcpu_data = {
        "forms": [
            {
                # We will populate field types like "textfield", "checkbox" here
            }
        ]
    }
    logger.debug(f'Initial pdfcpu_data structure: {json.dumps(pdfcpu_data, indent=2)}')

    logger.info("Starting general field processing loop based on PDF_FIELD_MAP.")
    form_fields_dict = pdfcpu_data["forms"][0] # Get a reference to the dictionary holding field type lists

    for app_field_key, pdf_field_name_from_map in PDF_FIELD_MAP.items():
        # Get value from form_data first (data submitted by user)
        submitted_value = form_data.get(app_field_key)

        # If submitted_value is None (key not in form) or an empty string, try to use default
        if submitted_value is None or str(submitted_value).strip() == '':
            field_value = DEFAULT_VALUES.get(app_field_key)
        else:
            field_value = submitted_value

        if field_value is not None: # Only add if there's a value (from form or default)
            final_json_value = field_value # Value that will actually be put into the JSON

            # Monetary field formatting for section 12
            monetary_fields = [
                'field12a_property_damage',
                'field12b_personal_injury',
                'field12c_wrongful_death',
                'field12d_total'
            ]
            if app_field_key in monetary_fields:
                try:
                    # Convert to float first to handle potential string inputs and ensure numeric format
                    numeric_value = float(field_value)
                    final_json_value = f"${numeric_value:,.2f}" # Format as $xxx,xxx.xx
                except ValueError:
                    logger.warning(f"Could not convert monetary field '{app_field_key}' value '{field_value}' to float. Using original value: {final_json_value}")
                    # If conversion fails, final_json_value remains the original field_value

            # Determine pdfcpu_field_type based on the app_field_key
            if app_field_key in ['field3_checkbox_civilian', 'field3_checkbox_military']:
                pdfcpu_field_type = 'checkbox'
                # Ensure the final_json_value is a Python boolean for checkboxes
                if isinstance(field_value, str):
                    if field_value.lower() == 'true':
                        final_json_value = True
                    elif field_value.lower() == 'false':
                        final_json_value = False
                    else:
                        logger.warning(f"Checkbox '{app_field_key}' received ambiguous string '{field_value}'. Interpreting as False.")
                        final_json_value = False
                elif not isinstance(field_value, bool):
                    # If it's not a string and not a bool (e.g., int 1), convert to bool
                    final_json_value = bool(field_value)
                # If it's already a bool, final_json_value is already correct (as field_value)
            else:
                pdfcpu_field_type = 'textfield' 

            # Log processed value (original field_value for context, final_json_value for what's used)
            logger.info(f"Processing '{app_field_key}': PDF Target='{pdf_field_name_from_map}', Original Value='{field_value}', JSON Value='{final_json_value}'")

            if pdfcpu_field_type not in form_fields_dict:
                form_fields_dict[pdfcpu_field_type] = []
            form_fields_dict[pdfcpu_field_type].append({
                "name": pdf_field_name_from_map,
                "value": final_json_value # Use the explicitly typed boolean for checkboxes
            })
            logger.debug(f"Added to pdfcpu_data: {{'name': '{pdf_field_name_from_map}', 'value': {final_json_value}, 'type': '{pdfcpu_field_type}'}}")
        else:
            logger.debug(f"Skipping '{app_field_key}': No value in form_data and no default_value specified in DEFAULT_VALUES.")

    logger.info(f"Final pdfcpu_data before conversion to JSON:\n{json.dumps(pdfcpu_data, indent=2)}")

    # Convert the dictionary to a JSON string
    try:
        pdfcpu_data_json = json.dumps(pdfcpu_data) # No indent for simpler XFA JSON
        logger.info(f"Final pdfcpu_data in JSON format to be written to file: {pdfcpu_data_json}")
    except TypeError as e:
        logger.error(f"Error serializing pdfcpu_data to JSON: {e}")
        logger.error(f"Problematic pdfcpu_data: {pdfcpu_data}")
        # Potentially re-raise or handle, e.g., by returning an error status
        # For now, proceeding will likely fail at pdfcpu stage
        pdfcpu_data_json = "{}" # Provide empty JSON to avoid crashing file write

    temp_json_file_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json", encoding='utf-8') as tmp_json_file:
            tmp_json_file.write(pdfcpu_data_json)
            temp_json_file_path = tmp_json_file.name
        logger.info(f"Temporary JSON file created at: {temp_json_file_path}")

        # Resolve paths to be absolute and normalized
        resolved_output_pdf_path = os.path.abspath(output_pdf_full_path_param)
        resolved_template_path = os.path.abspath(pdf_template_path_param)

        logger.info(f"Resolved PDF Template Path: {resolved_template_path}")
        logger.info(f"Resolved Output PDF Path: {resolved_output_pdf_path}")

        # Ensure output directory for the resolved path exists
        output_dir = os.path.dirname(resolved_output_pdf_path)
        os.makedirs(output_dir, exist_ok=True)

        # Additional diagnostics before calling pdfcpu
        logger.info(f"Absolute path of temp JSON file: {os.path.abspath(temp_json_file_path)}")
        logger.info(f"Output directory confirmed to exist: {os.path.isdir(output_dir)}")
        logger.info(f"Write permissions for output directory ({output_dir}): {os.access(output_dir, os.W_OK)}")

        # Corrected pdfcpu command arguments and added -mode xfa
        pdfcpu_command = [
            'pdfcpu',
            'form','fill',
            '-mode', 'xfa',             # Specify XFA mode
            resolved_template_path,     # 1. Input PDF path (resolved)
            temp_json_file_path,        # 2. JSON data file path
            resolved_output_pdf_path    # 3. Output PDF path (resolved)
        ]
        logger.info(f"Executing pdfcpu command: {' '.join(pdfcpu_command)}")

        process_result = subprocess.run(pdfcpu_command, capture_output=True, text=True, check=False)
        if process_result.returncode == 0:
            logger.info(f"PDF filled successfully: {resolved_output_pdf_path}")
            return resolved_output_pdf_path
        else:
            logger.error(f"Error filling PDF with pdfcpu. Return code: {process_result.returncode}")
            logger.error(f"pdfcpu error details: {process_result.stderr}")
            return None

    except Exception as e:
        logger.error(f"Exception during PDF filling: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None
    finally:
        if temp_json_file_path and os.path.exists(temp_json_file_path):
            try:
                os.remove(temp_json_file_path)
                logger.info(f"Temporary JSON file {temp_json_file_path} removed.")
            except OSError as e_remove:
                logger.error(f"Error removing temporary file {temp_json_file_path}: {e_remove.strerror}")
        logger.info("-"*20 + " Exiting fill_sf95_pdf " + "-"*20 + "\n")


if __name__ == '__main__':
    # This is just for direct testing of this script.
    # In the actual app, app.py will call fill_sf95_pdf with flask's request.form and the map.
    sample_form_data = {
        'field1_agency': 'Test Agency',
    }
    # Simulate ImmutableMultiDict for direct call if needed, or just pass dict
    from werkzeug.datastructures import ImmutableMultiDict
    sample_form_data_imm = ImmutableMultiDict(sample_form_data)

    pdf_template_path = 'path_to_your_pdf_template.pdf' # Replace with actual path
    output_pdf_full_path = 'path_to_your_output_pdf.pdf' # Replace with actual path

    filled_pdf_path = fill_sf95_pdf(sample_form_data_imm, pdf_template_path, output_pdf_full_path)
    if filled_pdf_path:
        print(f"Standalone test: PDF saved to {filled_pdf_path}")
    else:
        print("Standalone test: PDF filling failed.")
