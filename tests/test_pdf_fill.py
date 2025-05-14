import os
import json
from PyPDF2 import PdfReader, PdfWriter
import traceback


def create_and_fill_test_pdf(test_value):
    """
    Fills the test.pdf template with the provided test_value using PyPDF2.
    The field name is loaded from data/test_field_map.json.
    The filled PDF is saved to data/filled_forms/test.pdf.
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_pdf = os.path.join(base_dir, 'src', 'pdf_templates', 'test.pdf')
        filled_forms_dir = os.path.join(base_dir, 'data', 'filled_forms')
        os.makedirs(filled_forms_dir, exist_ok=True)
        output_pdf = os.path.join(filled_forms_dir, 'test.pdf')
        field_map_path = os.path.join(base_dir, 'data', 'test_field_map.json')
        with open(field_map_path, 'r') as f:
            test_field_map = json.load(f)
        field_name = test_field_map['test_field']
        reader = PdfReader(template_pdf)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.update_page_form_field_values(writer.pages[0], {field_name: test_value})
        with open(output_pdf, 'wb') as f_out:
            writer.write(f_out)
        return output_pdf
    except Exception as e:
        tb = traceback.format_exc()
        try:
            from flask import current_app
            current_app.logger.error(f"[TEST_PDF_FILL] Error: {e}\nTraceback:\n{tb}")
        except Exception:
            print(f"[TEST_PDF_FILL] Error: {e}\nTraceback:\n{tb}")
        raise
