import os
import pytest
from fillpdf import fillpdfs

# Define the base directory of the project (two levels up from this test script)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_TEMPLATE_PATH = os.path.join(BASE_DIR, 'data', 'sf95.pdf')

def test_sf95_pdf_fields_exist():
    """
    Test that the SF-95 PDF template exists and has at least one form field.
    """
    assert os.path.exists(PDF_TEMPLATE_PATH), f"PDF template not found at {PDF_TEMPLATE_PATH}"
    form_fields = fillpdfs.get_form_fields(PDF_TEMPLATE_PATH)
    assert isinstance(form_fields, dict), "Form fields should be a dictionary."
    assert form_fields, "No fields found in sf95.pdf by fillpdfs."
    # Optionally, check for specific expected field names
    # expected_fields = ["field1", "field2", ...]
    # for field in expected_fields:
    #     assert field in form_fields, f"Expected field '{field}' not found in PDF."

# Optionally, add more tests for field values, types, etc.
