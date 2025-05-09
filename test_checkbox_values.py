import os
from fillpdf import fillpdfs

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_TEMPLATE_DIR = os.path.join(BASE_DIR, 'src', 'pdf_templates')
INPUT_PDF_NAME = 'simple_checkbox_test.pdf'
INPUT_PDF_PATH = os.path.join(PDF_TEMPLATE_DIR, INPUT_PDF_NAME)

OUTPUT_DIR_NAME = 'checkbox_test_outputs'
OUTPUT_DIR_PATH = os.path.join(BASE_DIR, OUTPUT_DIR_NAME)

CHECKBOX_FIELD_NAME = 'Check Box3' # As identified from the screenshot

def main():
    print(f"Using PDF template: {INPUT_PDF_PATH}")
    if not os.path.exists(INPUT_PDF_PATH):
        print(f"ERROR: Input PDF not found at {INPUT_PDF_PATH}")
        print(f"Please ensure '{INPUT_PDF_NAME}' exists in '{PDF_TEMPLATE_DIR}'")
        return

    if not os.path.exists(OUTPUT_DIR_PATH):
        try:
            os.makedirs(OUTPUT_DIR_PATH)
            print(f"Created output directory: {OUTPUT_DIR_PATH}")
        except OSError as e:
            print(f"ERROR: Could not create output directory {OUTPUT_DIR_PATH}: {e}")
            return

    # Values to test for checking the checkbox
    test_values_for_checked = ['Yes', 'On', 1, True, 'X']
    
    # Value to test for unchecking the checkbox
    test_value_for_unchecked = 'Off'

    all_test_attempts = []

    print(f"\nAttempting to set '{CHECKBOX_FIELD_NAME}' to various 'checked' states...")
    for value in test_values_for_checked:
        data_to_fill = {CHECKBOX_FIELD_NAME: value}
        # Sanitize value for filename (e.g., True -> true, remove spaces)
        filename_value_part = str(value).replace(" ", "_").lower()
        output_pdf_name = f"test_checked_with_{filename_value_part}.pdf"
        output_pdf_full_path = os.path.join(OUTPUT_DIR_PATH, output_pdf_name)
        
        try:
            fillpdfs.write_fillable_pdf(INPUT_PDF_PATH, output_pdf_full_path, data_to_fill, flatten=False)
            print(f"  SUCCESS: Created '{output_pdf_name}' using value: {repr(value)} (type: {type(value).__name__})")
            all_test_attempts.append({'value': repr(value), 'type': type(value).__name__, 'state': 'checked', 'output_file': output_pdf_name, 'status': 'success'})
        except Exception as e:
            print(f"  ERROR trying value {repr(value)} (type: {type(value).__name__}): {e}")
            all_test_attempts.append({'value': repr(value), 'type': type(value).__name__, 'state': 'checked', 'output_file': output_pdf_name, 'status': f'error - {e}'})

    print(f"\nAttempting to set '{CHECKBOX_FIELD_NAME}' to 'unchecked' state...")
    data_to_fill_off = {CHECKBOX_FIELD_NAME: test_value_for_unchecked}
    output_pdf_name_off = f"test_unchecked_with_{str(test_value_for_unchecked).lower()}.pdf"
    output_pdf_full_path_off = os.path.join(OUTPUT_DIR_PATH, output_pdf_name_off)
    try:
        fillpdfs.write_fillable_pdf(INPUT_PDF_PATH, output_pdf_full_path_off, data_to_fill_off, flatten=False)
        print(f"  SUCCESS: Created '{output_pdf_name_off}' using value: {repr(test_value_for_unchecked)} (type: {type(test_value_for_unchecked).__name__})")
        all_test_attempts.append({'value': repr(test_value_for_unchecked), 'type': type(test_value_for_unchecked).__name__, 'state': 'unchecked', 'output_file': output_pdf_name_off, 'status': 'success'})
    except Exception as e:
        print(f"  ERROR trying value {repr(test_value_for_unchecked)} (type: {type(test_value_for_unchecked).__name__}): {e}")
        all_test_attempts.append({'value': repr(test_value_for_unchecked), 'type': type(test_value_for_unchecked).__name__, 'state': 'unchecked', 'output_file': output_pdf_name_off, 'status': f'error - {e}'})

    print("\n--- Test Summary ---")
    print(f"All output PDFs have been written to: {OUTPUT_DIR_PATH}")
    print("Please open and inspect each PDF to verify the state of checkbox 'Check Box3'.")
    for attempt in all_test_attempts:
        print(f"  - Value Tested: {attempt['value']} (Type: {attempt['type']}, Desired State: {attempt['state']}) -> Output: {attempt['output_file']}, Result: {attempt['status']}")

if __name__ == '__main__':
    main()
