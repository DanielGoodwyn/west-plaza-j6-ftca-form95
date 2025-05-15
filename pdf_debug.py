from PyPDF2 import PdfReader

pdf_path = "src/pdf_templates/test.pdf"
try:
    reader = PdfReader(pdf_path)
    print("PDF loaded successfully.")
    print("Number of pages:", len(reader.pages))
    fields = reader.get_fields()
    if fields:
        print("Fields:")
        for k, v in fields.items():
            print(f"  {k}: {v}")
    else:
        print("No form fields found.")
except Exception as e:
    print("Failed to load PDF:", e)
