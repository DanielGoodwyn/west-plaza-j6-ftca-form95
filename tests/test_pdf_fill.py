import os
import json
from fillpdf import fillpdfs

def create_and_fill_test_pdf(test_value):
    """
    Fills the test.pdf template with the provided test_value in the only field.
    The field name is loaded from data/test_field_map.json.
    The filled PDF is saved to data/filled_forms/test.pdf.
    """
    # Locate paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_pdf = os.path.join(base_dir, 'src', 'pdf_templates', 'test.pdf')
    filled_forms_dir = os.path.join(base_dir, 'data', 'filled_forms')
    os.makedirs(filled_forms_dir, exist_ok=True)
    output_pdf = os.path.join(filled_forms_dir, 'test.pdf')
    field_map_path = os.path.join(base_dir, 'data', 'test_field_map.json')
    with open(field_map_path, 'r') as f:
        test_field_map = json.load(f)
    # Fill the field
    fillpdfs.write_fillable_pdf(
        template_pdf,
        output_pdf,
        {test_field_map['test_field']: test_value}
    )
    # Flatten the PDF to make the filled value visible everywhere
    fillpdfs.flatten_pdf(output_pdf, output_pdf)
    return output_pdf
