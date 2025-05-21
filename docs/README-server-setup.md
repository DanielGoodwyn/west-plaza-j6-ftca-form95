# Server Setup and Environment Checklist for west-plaza-j6-ftca-form95

This guide ensures your application works both locally and on your production server (e.g., FastComet at https://investigatej6.org/west-plaza-lawsuit).

## 1. Python Environment
- Use **Python 3.8+** (match your local and server versions for consistency).
- Always use a **virtual environment** (`venv`).

## 2. Install Python Dependencies
- Ensure you are in your project root (`west-plaza-j6-ftca-form95`).
- Activate your virtual environment:
  ```sh
  python3 -m venv venv
  source venv/bin/activate
  ```
- Install dependencies:
  ```sh
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

### requirements.txt (key packages)
```
Flask
Flask-Login
Flask-Session
python-dotenv
fillpdf
pytz
flask-wtf
wtforms
Werkzeug
```

## 3. Install System Dependencies
- PDF form filling requires **pdftk** or **pdfcpu** (depending on your configuration).
- **On Ubuntu/Debian:**
  ```sh
  sudo apt-get update
  sudo apt-get install pdftk
  # or, for pdfcpu (if using):
  # Download from https://pdfcpu.io/download and place binary in your PATH
  ```
- **On macOS:**
  ```sh
  brew install pdftk-java
  # or, for pdfcpu:
  brew install pdfcpu
  ```
- **On FastComet:**
  - Use SSH to install `pdftk` or upload the `pdfcpu` binary.
  - Confirm the binary is in your `$PATH`.

## 4. Permissions

---

## 4a. Python Import Paths and Deployment Caveats

**Absolute Imports Required:**

When running your Flask app on shared hosting (e.g., FastComet with Passenger/cPanel), the application is often started from the project root, not from within the `src/` directory. This changes how Python resolves imports for your own modules.

- **Correct way:**
  ```python
  from src.utils.logging_config import setup_logging
  ```
- **Incorrect way (works locally, but not on server):**
  ```python
  from utils.logging_config import setup_logging
  ```

If you see errors like `ModuleNotFoundError: No module named 'utils'`, update your imports to use the absolute path from the project root (i.e., `src.utils`).

**Always Restart the App:**
After pulling updates or changing dependencies, always restart your application from the hosting control panel or with your process manager. This ensures all code and dependency changes take effect.

**Passenger/WSGI Specifics:**
- Passenger/cPanel may run your app from a different working directory than you expect. Always use absolute imports for your own modules.
- If you have a custom `passenger_wsgi.py`, ensure it imports your Flask app using the correct path (e.g., `from src.app import app as application`).

**Troubleshooting:**
- If you see import errors, check your import statements and ensure you are using the correct absolute path.
- Check your logs (e.g., `~/logs/passenger_west_plaza.log`) for any Python errors after restarting the app.

---

- Ensure the following directories are writable by your application:
  - `data/filled_forms/`
  - `data/uploads/`

## 5. Running the Application
- Always activate your virtual environment before running:
  ```sh
  source venv/bin/activate
  cd src
  python app.py
  ```
- For production, use a process manager (e.g., `supervisord`, `systemd`, or similar) and ensure the app restarts on failure.

## 6. Debugging PDF Filling Issues
- If PDFs are not generated:
  - Check logs for errors related to `fillpdf`, `pdftk`, or `pdfcpu`.
  - Ensure the system binary (`pdftk`/`pdfcpu`) is installed and executable.
  - Run a minimal PDF fill test script (see below) to isolate issues.

## 7. Minimal PDF Fill Test Script
Create a file `test_pdf_fill.py` with:
```python
from fillpdf import fillpdfs
import os

PDF_TEMPLATE_PATH = os.path.join('data', 'sf95.pdf')
output_pdf = os.path.join('data', 'filled_forms', 'test_output.pdf')

form_fields = fillpdfs.get_form_fields(PDF_TEMPLATE_PATH)
if not form_fields:
    print('No fields found in PDF!')
else:
    print('Fields:', form_fields)
    data = {key: 'test' for key in form_fields}
    fillpdfs.write_fillable_pdf(PDF_TEMPLATE_PATH, output_pdf, data)
    print(f'Filled PDF saved to {output_pdf}')
```
Run with:
```sh
python test_pdf_fill.py
```

---

**If you encounter issues:**
- Double-check all dependencies are installed.
- Check permissions on data directories.
- Review logs for errors.
- Ask for help with the error message and environment details.

---

**Maintainer:** Daniel Goodwyn
