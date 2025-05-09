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

# Maps HTML form field names to their corresponding PDF internal field names (XFA paths).
# This is the primary map used by the fill_sf95_pdf function.
# pdf_data_map = {
#     # Page 1 - Reduced to test only field1_agency
#     'field1_agency': '1 Submit to Appropriate Federal Agency',
# }

PDF_FIELD_METADATA = {
    # 1. Agency
    'field1_agency': {'pdf_field_name': '1 Submit to Appropriate Federal Agency', 'type': 'textfield_multiline', 'default_value': 'United States Capitol Police\n119 D Street, NE\nWashington, DC 20510'},
    
    # 2. Claimant Info (Name, Address, City, State, Zip) - Combined into one PDF field
    'field2_claimant_info_combined': {'pdf_field_name': '2 Name address of claimant and claimants personal representative if any See instructions on reverse Number Street City State and Zip code', 'type': 'textfield_multiline'},

    # 3. Employment Type (Radio Buttons) & Other Specify (Text Field) - Placeholders for now
    'field3_type_employment_military': {'pdf_field_name': 'PLACEHOLDER Military', 'type': 'radio', 'group': 'employment_type'},
    'field3_type_employment_civilian': {'pdf_field_name': 'PLACEHOLDER Civilian', 'type': 'radio', 'group': 'employment_type'},
    'field3_type_employment_other': {'pdf_field_name': 'PLACEHOLDER Other', 'type': 'radio', 'group': 'employment_type'},
    'field3_other_specify': {'pdf_field_name': 'PLACEHOLDER 3. Other Employment - Specify', 'type': 'textfield'},

    # 4. Date of Birth
    'field_pdf_4_dob': {'pdf_field_name': '4 DATE OF BIRTH', 'type': 'textfield'},

    # 5. Marital Status (Radio Buttons) - Placeholders for now
    'field_pdf_5_marital_status_single': {'pdf_field_name': 'PLACEHOLDER Single', 'type': 'radio', 'group': 'marital_status'},
    'field_pdf_5_marital_status_married': {'pdf_field_name': 'PLACEHOLDER Married', 'type': 'radio', 'group': 'marital_status'},
    # ... (add other marital status options if they exist, with placeholder pdf_field_names)
    'field_pdf_5_marital_status_divorced': {'pdf_field_name': 'PLACEHOLDER Divorced', 'type': 'radio', 'group': 'marital_status'},
    'field_pdf_5_marital_status_widowed': {'pdf_field_name': 'PLACEHOLDER Widowed', 'type': 'radio', 'group': 'marital_status'},
    'field_pdf_5_marital_status_separated': {'pdf_field_name': 'PLACEHOLDER Separated', 'type': 'radio', 'group': 'marital_status'},

    # 6. Date of Incident
    'field6_date_of_incident': {'pdf_field_name': '6 DATE AND DAY OF ACCIDENT', 'type': 'textfield', 'default_value': '01/06/2021'},

    # 7. Time of Incident
    'field7_time_of_incident': {'pdf_field_name': '7 TIME AM OR PM', 'type': 'textfield', 'default_value': '1:06 P.M.'},

    # 8. Basis of Claim
    'field8_basis_of_claim': {'pdf_field_name': '8 BASIS OF CLAIM State in detail the known facts and circumstances attending the damage injury or death identifying persons and property involved the place of occurrence and the cause thereof Use additional pages if necessary', 'type': 'textfield'},

    # 9. Property Damage & Owner Info
    'field9_owner_name_address': {'pdf_field_name': 'NAME AND ADDRESS OF OWNER IF OTHER THAN CLAIMANT Number Street City State and Zip Code', 'type': 'textfield', 'default_value': 'N/A'},
    'field9_property_damage_description_vehicle': {'pdf_field_name': 'BRIEFLY DESCRIBE THE PROPERTY NATURE AND EXTENT OF THE DAMAGE AND THE LOCATION OF WHERE THE PROPERTY MAY BE INSPECTED See instructions on reverse side', 'type': 'textfield', 'default_value': 'N/A'},
    'field9_property_damage_description_other': {'pdf_field_name': 'PLACEHOLDER 9. Description of Property Damage - Other', 'type': 'textfield'},

    # 10. Nature of Injury
    'field10_nature_of_injury': {'pdf_field_name': 'STATE THE NATURE AND EXTENT OF EACH INJURY OR CAUSE OF DEATH WHICH FORMS THE BASIS OF THE CLAIM  IF OTHER THAN CLAIMANT STATE THE NAME OF THE INJURED PERSON OR DECEDENT', 'type': 'textfield'},

    # 11. Witnesses - Updated XFA paths
    'field11_witness_name': {'pdf_field_name': 'NAMERow1', 'type': 'textfield', 'default_value': 'See FBI and Capitol Police database'},
    'field11_witness_address': {'pdf_field_name': 'ADDRESS Number Street City State and Zip CodeRow1', 'type': 'textfield', 'default_value': 'The FBI and Capitol Police already maintain a database of 1,000+ witnesses'},

    # 12. Amount of Claim
    'field12a_property_damage_amount': {'pdf_field_name': 'a PROPERTY DAMAGE[0]', 'type': 'textfield', 'default_value': '0.00'},
    'field12b_personal_injury_amount': {'pdf_field_name': 'b PERSONAL INJURY[0]', 'type': 'textfield', 'default_value': '90000.00'},
    'field12c_wrongful_death_amount': {'pdf_field_name': 'c WRONGFUL DEATH[0]', 'type': 'textfield', 'default_value': '0.00'},
    'field12d_total_amount': {'pdf_field_name': 'd TOTAL Failure to specify may cause forfeiture of your rights[0]', 'type': 'textfield', 'default_value': '90000.00'},
    
    # 13. Signature & Phone
    'field13a_signature': {'pdf_field_name': '13a SIGNATURE OF CLAIMANT See instructions on reverse side[0]', 'type': 'textfield'}, # For typed name
    'field_pdf_13b_phone': {'pdf_field_name': '13b PHONE NUMBER OF PERSON SIGNING FORM', 'type': 'textfield'},

    # 14. Date Signed
    'field14_date_signed': {'pdf_field_name': '14 DATE OF SIGNATURE', 'type': 'textfield'},
    
    # Page 2 Insurance Questions (Checkboxes) - Placeholders for now
    'insurance_yes': {'pdf_field_name': 'PLACEHOLDER Insurance_Yes', 'type': 'checkbox', 'value_on': 'Yes', 'value_off': 'Off'},
    'insurance_no': {'pdf_field_name': 'PLACEHOLDER Insurance_No', 'type': 'checkbox', 'value_on': 'Yes', 'value_off': 'Off'},
    'field15_insurer_name': {'pdf_field_name': 'PLACEHOLDER 15. Name of Insurer', 'type': 'textfield'},
    'field15_policy_number': {'pdf_field_name': 'PLACEHOLDER 15. Policy Number', 'type': 'textfield'},
    # ... add other insurance related fields if necessary
}

def add_to_pdfcpu_data(pdfcpu_data, xfa_path, value):
    logger.debug(f"add_to_pdfcpu_data called with: xfa_path='{xfa_path}', value='{value}'")
    pdfcpu_data[xfa_path] = str(value)

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

    logger.info("Starting general field processing loop based on PDF_FIELD_METADATA.")
    form_fields_dict = pdfcpu_data["forms"][0] # Get a reference to the dictionary holding field type lists

    for html_field_name, field_meta in PDF_FIELD_METADATA.items():
        pdf_field_name = field_meta['pdf_field_name']

        # Get value from form_data first
        submitted_value = form_data.get(html_field_name)

        # If submitted_value is None (key not in form) or an empty string, try to use default
        if submitted_value is None or submitted_value == '':
            field_value = field_meta.get('default_value')
        else:
            field_value = submitted_value

        if field_value is not None: # Only add if there's a value (from form or default)
            logger.info(f"Processing '{html_field_name}' (type: {field_meta.get('type', 'textfield')}): XFA Path='{pdf_field_name}', Value='{field_value}'")
            
            # Determine the pdfcpu field type
            pdfcpu_field_type = field_meta.get('type', 'textfield') # Default to 'textfield'
            # TODO: Add specific handling or mapping if pdfcpu expects different type names, e.g., 'checkboxfield'
            # if field_meta.get('type') == 'checkbox': 
            #     pdfcpu_field_type = 'checkboxfield' # Example, confirm actual pdfcpu name

            if pdfcpu_field_type not in form_fields_dict:
                form_fields_dict[pdfcpu_field_type] = []
            
            form_fields_dict[pdfcpu_field_type].append({
                "name": pdf_field_name,
                "value": str(field_value)
                # "locked": False # Optional, defaults to false
            })
        else:
            logger.debug(f"Skipping '{html_field_name}': No value in form_data and no default_value specified.")

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
