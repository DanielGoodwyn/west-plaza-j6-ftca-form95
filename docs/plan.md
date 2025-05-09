# Development Roadmap: FTCA Form 95 Intake Web App

This document outlines a step-by-step plan for building the FTCA Form 95 Intake web application, from Minimum Viable Product (MVP) to a more production-ready state.

## Phase 1: Foundation & Core MVP

**Goal:** Create a basic, functional application that can accept data for key fields, store it, and fill a PDF.

1.  **Step 1: Project Setup & Environment (Day 1-2)**
    *   [X] Initialize Git repository.
    *   [X] Set up Python virtual environment.
    *   [X] Create basic Flask application structure (`app.py`, `templates/`, `static/`, `utils/`, `data/`).
    *   [X] Create initial `requirements.txt` (Flask).
    *   [X] Draft `README.md`, `project.md`, `plan.md`, `python-flask-stack.md`.
    *   Download the SF-95 PDF (`data/sf95.pdf`).

2.  **Step 2: PDF Field Name Discovery (Crucial - Day 2-3)**
    *   Objective: Identify all fillable field names in `sf95.pdf`.
    *   Task: Use Adobe Acrobat Pro, `pdfminer.six`, or other PDF analysis tools to list field names and their types (text, checkbox, etc.).
    *   Deliverable: A mapping document (e.g., a simple text file or spreadsheet) correlating PDF box numbers/descriptions to actual PDF field names.

3.  **Step 3: Basic HTML Form (Day 3-4)**
    *   Objective: Create the frontend HTML form in `templates/form.html`.
    *   Task: Include input fields for the user-filled sections (2, 3 (checkbox), 4, 5, 13b, 14) and the editable pre-filled fields (8, 10, 12b, 12c).
    *   Task: Pre-populate fields (1, 6, 7, 8, 9, 10, 11, 12a, 12b, 12c) with their default values as specified. Mark fixed fields as read-only or display them as static text if appropriate.
    *   Basic styling with `static/css/style.css` for usability.

4.  **Step 4: Backend Form Handling & Data Storage (Day 4-6)**
    *   Objective: Receive form data, validate, and store it.
    *   Task: Create a Flask route (`/submit`) in `app.py` to handle POST requests from the form.
    *   Task: Implement basic server-side validation for submitted data.
    *   Task: Set up SQLite database (`data/form_data.db`). Define a table schema to store all relevant fields (user-input, pre-filled, calculated).
    *   Task: Write Python code (potentially in `utils/database_handler.py`) to insert validated form data into the SQLite table.
    *   Add `sqlite3` to `requirements.txt` (it's built-in, but good to note; `SQLAlchemy` might be added later for ORM).

5.  **Step 5: PDF Filling Logic (Day 6-8)**
    *   Objective: Fill the `sf95.pdf` with data from a submission.
    *   Task: Choose and install a PDF filling library (e.g., `fillpdf`, `pdfrw`). Add to `requirements.txt`.
    *   Task: Create `utils/pdf_filler.py`. Write a function that takes the form data (and the PDF field name mapping from Step 2) and fills `sf95.pdf`.
    *   Task: Save the filled PDF to a designated output directory (e.g., `data/filled_forms/`). Name files uniquely (e.g., `submission_id_timestamp.pdf`).
    *   Integrate this into the `/submit` route in `app.py` after data storage.

6.  **Step 6: Basic Notification (Day 8-9)**
    *   Objective: Send a simple notification upon successful PDF generation.
    *   Task: Create `utils/notifier.py`. Write a function to send an email using `smtplib`.
    *   Configuration: Allow setting SMTP server, sender/recipient emails (e.g., via environment variables or a config file - keep sensitive info out of Git).
    *   Integrate into `/submit` route.
    *   For MVP, this could just log to console: "Notification: PDF generated for [Claimant Name]".

7.  **Step 7: MVP Review & Testing (Day 9-10)**
    *   Internal testing of the complete flow: form submission -> data storage -> PDF generation -> notification (or log).
    *   Verify all pre-filled fields are correct and user inputs are accurately reflected in the PDF.
    *   Check basic error handling (e.g., what happens if PDF template is missing?).

## Phase 2: Enhancements & Production Readiness

**Goal:** Refine the MVP, add robustness, improve user experience, and prepare for deployment.

1.  **Step 8: Advanced Form Features & Validation (Iterative)**
    *   Client-side JavaScript validation (`static/js/script.js`) for better UX (e.g., required fields, data types like date/email, character limits for text areas like 8 and 10).
    *   Server-side validation enhancement: More comprehensive checks.
    *   Implement calculation for Field 12d (Total) on the frontend (JS) and ensure backend recalculates for accuracy.
    *   Improve handling of checkbox for Field 3.

2.  **Step 9: Improved Styling & Responsiveness**
    *   Enhance `static/css/style.css` for a professional look and feel.
    *   Ensure the form is responsive and works well on different screen sizes.

3.  **Step 10: Robust Error Handling & Logging**
    *   Implement comprehensive error handling throughout the backend (database errors, file system errors, PDF generation errors, notification failures).
    *   Provide user-friendly error messages on the frontend.
    *   Set up structured logging for application events and errors.

4.  **Step 11: Security Hardening**
    *   Implement CSRF protection (Flask-WTF can help).
    *   Ensure proper input sanitization to prevent XSS and SQL injection (ORM like SQLAlchemy can help with SQLi).
    *   Review file permissions for `data/` directory and database file.
    *   Consider rate limiting for form submissions if abuse is a concern.

5.  **Step 12: Configuration Management**
    *   Move configurable parameters (email settings, database path if not fixed) to environment variables or a configuration file (e.g., `config.py`, `.env`).

6.  **Step 13: Dockerization**
    *   Create a `Dockerfile` to containerize the application.
    *   Include Python, dependencies, and application code.
    *   Test running the application via Docker.

7.  **Step 14: Unit & Integration Testing**
    *   Write unit tests for utility functions (PDF filling, notification, data handling).
    *   Write integration tests for the main application flow.
    *   Consider using `pytest`.

8.  **Step 15: Deployment Preparation**
    *   Plan deployment strategy (e.g., which server, how to manage the Docker container, web server like Gunicorn/Nginx in front of Flask).
    *   Set up DNS for `investigatej6.org/west-plaza-lawsuit` to point to the server.
    *   Configure HTTPS (e.g., Let's Encrypt).

## Phase 3: Post-Deployment & Maintenance

1.  **Step 16: User Acceptance Testing (UAT)**
    *   Allow actual users (internal team first) to test the application.
    *   Gather feedback and iterate.

2.  **Step 17: Documentation Review & Update**
    *   Ensure `README.md` is up-to-date with deployment and usage instructions.
    *   Document any operational procedures (backups, monitoring).

3.  **Step 18: Ongoing Monitoring & Maintenance**
    *   Monitor application logs for errors.
    *   Perform regular backups of the database and filled PDFs.
    *   Update dependencies as needed.

This roadmap provides a structured approach. Timelines are estimates and can be adjusted based on complexity encountered, especially with PDF field mapping and external dependencies like SMTP server setup.
