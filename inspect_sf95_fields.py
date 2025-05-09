import os
from fillpdf import fillpdfs

# Define the base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the SF-95 PDF template
PDF_TEMPLATE_PATH = os.path.join(BASE_DIR, 'src', 'pdf_templates', 'sf95.pdf')

def main():
    print(f"Attempting to read fields from PDF: {PDF_TEMPLATE_PATH}")

    if not os.path.exists(PDF_TEMPLATE_PATH):
        print(f"Error: PDF template not found at {PDF_TEMPLATE_PATH}")
        return

    try:
        # Get the form fields
        form_fields = fillpdfs.get_form_fields(PDF_TEMPLATE_PATH)

        # Print the field names and their values
        print("PDF Field Names and Values:")
        for field_name, field_val in form_fields.items():
            print(f"Name: {field_name}, Value: {field_val}")

        if not form_fields:
            print("No fields found in sf95.pdf by fillpdfs.")

    except Exception as e:
        print(f"Error reading fields from sf95.pdf: {e}")

if __name__ == "__main__":
    main()
