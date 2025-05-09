# Tech Stack Implementation: Python-Flask for FTCA Form 95 App

This document details how the chosen Python-Flask stack will be used to implement the core features of the FTCA Form 95 Intake web application.

## 1. Frontend Online User Form Intake

*   **Technology:** HTML5, CSS3, Vanilla JavaScript, served by Flask.
*   **Implementation:**
    *   **HTML (`src/templates/form.html`):**
        *   A single HTML page containing the form.
        *   Standard HTML form elements (`<form>`, `<input>`, `<textarea>`, `<select>`, `<button>`) will be used for data entry.
        *   Input types will be chosen appropriately (e.g., `text`, `date`, `number`, `checkbox`).
        *   Pre-filled values will be set using the `value` attribute for inputs or directly in `textarea` elements.
        *   Fields that are fixed (e.g., Field 1: "US Capitol Police") can be displayed as static text or read-only input fields (`<input type="text" readonly>`).
        *   Accessibility considerations (e.g., `label` for inputs) will be included.
    *   **CSS (`src/static/css/style.css`):**
        *   Basic styling to ensure readability and usability.
        *   Will make the form responsive to different screen sizes (e.g., using media queries).
    *   **JavaScript (`src/static/js/script.js`):**
        *   Client-side validation (e.g., checking for required fields, correct data formats before submission).
        *   Dynamic calculation for Field 12d (Total) if desired for immediate user feedback.
        *   Enhancements for user experience (e.g., conditional display of fields if necessary, though the SF-95 is fairly static).
    *   **Flask (`src/app.py`):**
        *   A route (e.g., `/` or `/form`) will use `render_template('form.html')` to serve the HTML page.
        *   Flask will also serve static files (CSS, JS) from the `static` directory.

## 2. Data Storage Backend

*   **Technology:** SQLite, accessed via Python's built-in `sqlite3` module (or potentially SQLAlchemy for ORM capabilities if complexity grows).
*   **Implementation:**
    *   **Database File (`data/form_data.db`):**
        *   A single file on the server will store the database.
    *   **Schema Definition (within `app.py` or a dedicated `utils/database_handler.py`):
        *   A table (e.g., `submissions`) will be created to store data from each form submission.
        *   Columns will correspond to all relevant fields from the SF-95 form (user-input, pre-filled that might be logged, and calculated fields).
        *   An `id` (primary key, auto-incrementing) and a `timestamp` for each submission will be included.
    *   **Data Handling (`app.py` or `utils/database_handler.py`):
        *   On form submission (`/submit` route), Python functions will connect to the SQLite database.
        *   SQL `INSERT` statements will be used to save the validated and processed form data into the `submissions` table.
        *   Error handling for database operations (e.g., connection issues, write errors) will be implemented.

## 3. PDF Generator

*   **Technology:** `pdfcpu` (Go command-line tool), invoked via Python's `subprocess` module.
*   **Implementation:**
    *   **PDF Template (`data/sf95.pdf`):**
        *   The official, fillable SF-95 PDF downloaded from GSA.
        *   **Crucial Prerequisite:** The exact names of the fillable fields within this PDF must be identified (e.g., using Adobe Acrobat Pro or a PDF analysis tool).
    *   **Filling Logic (`src/utils/pdf_filler.py`):
        *   A Python function will take the submitted form data (as a dictionary or object) and the path to the template PDF.
        *   It will use the chosen library to map the application's field names (e.g., `claimant_name`, `basis_of_claim`) to the actual internal field names of the `sf95.pdf`.
        *   The library will fill these fields with the provided data.
        *   Checkboxes (like Field 3) will require specific values (e.g., 'Yes', 'Off') understood by the PDF library for checking/unchecking.
        *   The generated (filled) PDF will be saved to a designated directory (e.g., `data/filled_forms/`) with a unique filename (e.g., `submission_<id>_<timestamp>.pdf`).
    *   **Integration (`src/app.py`):
        *   After successfully saving data to the database in the `/submit` route, the PDF filling function will be called.

## 4. Notifier

*   **Technology:** Python's built-in `smtplib` for email.
*   **Implementation:**
    *   **Notification Logic (`src/utils/notifier.py`):
        *   A Python function will be responsible for constructing and sending an email.
        *   It will use `smtplib` to connect to an SMTP server (this server must be self-hosted or an accessible internal relay, as per constraints).
        *   Email details (sender, recipient(s), subject, body) will be configurable.
        *   The email body might include summary information about the submission or a link/attachment of the generated PDF (though attaching directly might be complex initially; a simple notification is MVP).
    *   **Configuration (e.g., environment variables, `config.py`):
        *   SMTP server address, port, username/password (if authentication is needed).
        *   Recipient email addresses.
    *   **Integration (`src/app.py`):
        *   After successful PDF generation in the `/submit` route, the notification function will be called.
        *   For MVP, this could be simplified to logging a message to the console or a file if SMTP setup is deferred.

## 5. Overall Application Flow (Flask - `src/app.py`)

1.  **User Access:** User navigates to the root URL (e.g., `http://localhost:5000/`).
2.  **Form Display:** Flask route for GET `/` renders `form.html`.
3.  **User Input:** User fills out the form and clicks "Submit".
4.  **Form Submission:** Browser sends a POST request to the `/submit` route.
5.  **Data Processing (`/submit` route in `app.py`):
    *   Receive form data.
    *   Perform server-side validation and sanitization.
    *   Merge user input with fixed pre-filled values.
    *   Calculate derived fields (e.g., Field 12d Total).
    *   Store the complete data set in the SQLite database.
    *   Call `pdf_filler.py` to generate the filled PDF.
    *   Call `notifier.py` to send a notification.
    *   Return a response to the user (e.g., a success page with a confirmation message, or an error page).

This stack provides a cohesive, self-hostable solution meeting the project's requirements, leveraging Python's strengths in web development, data handling, and utility scripting.
