from fillpdf import fillpdfs
import os

# Construct the absolute path to the PDF file
script_dir = os.path.dirname(os.path.abspath(__file__))
pdf_template_path = os.path.join(script_dir, 'data', 'sf95-saved.pdf')

print(f"Attempting to read fields from: {pdf_template_path}")

try:
    if not os.path.exists(pdf_template_path):
        print(f"Error: PDF file not found at {pdf_template_path}")
    else:
        # Get the fields from the PDF
        form_fields = fillpdfs.get_form_fields(pdf_template_path, sort=True)
        
        if form_fields:
            print("\nDetected form fields:")
            for field_name, field_value in form_fields.items():
                print(f"  '{field_name}': '{field_value}'")
        else:
            print("\nNo fillable form fields were found in the PDF.")
            print("This might mean the 'Print to PDF' method did not preserve the form fields, or the PDF is not compatible.")

except Exception as e:
    print(f"\nAn error occurred while trying to read PDF fields: {e}")
    print("This could indicate incompatibility with the fillpdfs library or issues with the PDF file itself.")

print("\nTest script finished.")
