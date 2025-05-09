import os
from fillpdf import fillpdfs

# Define the base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the simple test PDF template
PDF_TEMPLATE_PATH = os.path.join(BASE_DIR, 'src', 'pdf_templates', 'simple_test.pdf')

# Path for the output filled PDF
OUTPUT_PDF_PATH = os.path.join(BASE_DIR, 'filled_simple_test.pdf')

# Data to fill into the PDF
# IMPORTANT: Replace 'Text1' and 'Text2' with the actual names 
# of the fields in your simple_test.pdf if they are different.
data_to_fill = {
    'Text1': 'Federal Bureau of Investigation',
    'Text2': 'Jane Claimant\n456 Oak Avenue\nSpringfield, IL 67890'
}

def main():
    print(f"Attempting to read fields from PDF: {PDF_TEMPLATE_PATH}")
    print(f"Data to fill: {data_to_fill}")

    if not os.path.exists(PDF_TEMPLATE_PATH):
        print(f"Error: PDF template not found at {PDF_TEMPLATE_PATH}")
        return

    try:
        # Ensure the output directory exists (though for root, it's not strictly necessary)
        output_dir = os.path.dirname(OUTPUT_PDF_PATH)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        fillpdfs.write_fillable_pdf(PDF_TEMPLATE_PATH, OUTPUT_PDF_PATH, data_to_fill, flatten=False)
        print(f"Successfully filled PDF. Output saved to: {OUTPUT_PDF_PATH}")
        
        # To verify, you might want to print the fields that fillpdfs thinks are in the PDF
        fields = fillpdfs.get_form_fields(PDF_TEMPLATE_PATH)
        print("Fields found in PDF:", fields)

    except Exception as e:
        print(f"Error filling PDF: {e}")

if __name__ == "__main__":
    main()
