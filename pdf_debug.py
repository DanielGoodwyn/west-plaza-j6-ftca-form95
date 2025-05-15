import os
import sys

# Ensure 'src' is in the Python path for imports, regardless of invocation location
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from PyPDF2 import PdfReader

# Use an absolute path for the test PDF, robust to script location
pdf_path = os.path.join(project_root, 'src', 'pdf_templates', 'test.pdf')
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
