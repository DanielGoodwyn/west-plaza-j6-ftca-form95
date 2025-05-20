# Development Roadmap: FTCA Form 95 Intake Web App

This document outlines a unified, step-by-step plan for building the FTCA Form 95 Intake web application, from MVP to production, using a consistent checklist format for all phases, steps, and tasks.

---

## Phase 0: Codebase Reconciliation (Critical Path)

**Goal:** Achieve reliable PDF generation on both local and FastComet server environments.

### Step 0.1: Analyze Key Commits
- **Local Working Version:** [`370709f`](https://github.com/DanielGoodwyn/west-plaza-j6-ftca-form95/commit/370709f23fb1e97b5385eb2423d78a1688ffc6c3) (_All form-to-PDF functionality works locally._)
- **First Server Success (No PDF):** [`4d9225c`](https://github.com/DanielGoodwyn/west-plaza-j6-ftca-form95/commit/4d9225cb29f9f097db8968169a32830c58ef1219) (_App runs on FastComet, but PDF generation does not work._)
- **Test PDF Button Works on Server:** [`13ecb37`](https://github.com/DanielGoodwyn/west-plaza-j6-ftca-form95/commit/13ecb374d31acac12d570dc2e3580c521e768019) (_Test route proves PDF can be filled and saved on FastComet, but only via a test field/button._)
- [✅] Review canonical form submission and PDF filling logic (370709f)
- [✅] Note changes that enabled server compatibility (env, paths, etc.) (4d9225c)
- [✅] Compare PDF generation logic in test route vs. main form submission (13ecb37)

### Step 0.2: Reconciliation Checklist
- [✅] Local form submission fills and saves PDF correctly
- [✅] FastComet server runs app and test PDF route works
- [🔲] Main form submission on FastComet server fills and saves PDF correctly
- [🔲] Unified codebase: merge/test working PDF logic from test route into main form submission
- [🔲] Remove/hide test PDF field/button from UI (temporarily hidden, not fully removed)
- [🔲] End-to-end test: user submits real form, PDF is generated and downloadable/admin-viewable on server
- [🔲] Document reconciliation process and update all docs (plan.md, project.md, stack.md, README.md)

---

## Phase 1: Foundation & Core MVP

**Goal:** Create a basic, functional application that can accept data for key fields, store it, and fill a PDF.

### Step 1.1: Project Setup & Environment
- [✅] Initialize Git repository
- [✅] Set up Python virtual environment
- [✅] Create basic Flask application structure (`app.py`, `templates/`, `static/`, `utils/`, `data/`)
- [✅] Create initial `requirements.txt` (Flask)
- [✅] Draft `README.md`, `project.md`, `plan.md`, `python-flask-stack.md`
- [✅] Download the SF-95 PDF (`data/sf95.pdf`)

### Step 1.2: PDF Field Name Discovery
- [✅] Identify all fillable field names in `sf95.pdf`
- [✅] Use PDF analysis tools to list field names and their types
- [✅] Deliver a machine-readable mapping file (`data/pdf_field_map.json`)
- [✅] Update PDF filling logic to use this map

### Step 1.3: Basic HTML Form
- [✅] Create frontend HTML form in `templates/form.html`
- [✅] Include input fields for user-filled and pre-filled sections
- [✅] Add 'Email Address' and supplemental essay questions (store in DB, not PDF)
- [✅] Pre-populate fields with specified defaults
- [🔲] Basic styling with `static/css/style.css` for usability

### Step 1.4: Backend Form Handling & Data Storage
- [✅] Flask route (`/submit`) to handle POST requests
- [✅] Basic server-side validation for submitted data
    - [✅] All required fields present and not empty
    - [✅] Correct data formats for dates, numbers
    - [🔲] Reasonable string lengths for text areas
    - [✅] User-friendly error messages and form repopulation
- [✅] Set up SQLite database and schema for all fields
- [✅] Insert validated data into SQLite
- [✅] Add `sqlite3` to `requirements.txt`

### Step 1.5: PDF Filling Logic
- [✅] Fill the `sf95.pdf` with data from a submission
- [✅] Choose and install PDF filling library
- [✅] Create PDF filler script/function
- [✅] Save filled PDF to output directory with unique filenames
- [✅] Integrate into `/submit` route
- [✅] Verify all data is accurately transferred to PDF
    *   [X] Task: Create `utils/pdf_filler.py`. Write a function that takes the form data (and the PDF field name mapping from Step 2) and fills `sf95.pdf`. (Logic integrated into `app.py`)
    *   [X] Task: Save the filled PDF to a designated output directory (e.g., `data/filled_forms/`). Name files uniquely (e.g., `submission_id_timestamp.pdf`).
    *   [X] Integrate this into the `/submit` route in `app.py` after data storage.
    *   [X] Crucially, this step includes thorough verification that all data (user-input, pre-filled, and calculated values) is accurately transferred from the web form submission, through backend processing, and correctly placed into the designated fields within the generated PDF. This confirms the integrity of the PDF field mapping (Step 2) and data handling (Step 4).

6.  **Step 6: Basic Notification (Day 8-9)**
    *   [/] Objective: Send a simple notification upon successful PDF generation. (Logging done, not email)
    *   [ ] Task: Create `utils/notifier.py`. Write a function to send an email using `smtplib`.
    *   [ ] Configuration: Allow setting SMTP server, sender/recipient emails (e.g., via environment variables or a config file - keep sensitive info out of Git).
    *   [/] Integrate into `/submit` route. (Logging is integrated)
    *   [/] For MVP, this could just log to console: "Notification: PDF generated for [Claimant Name]".

7.  **Step 7: MVP Review & Testing (Day 9-10)**
    *   [X] Internal testing of the complete flow: form submission -> data storage -> PDF generation -> notification (or log).
    *   [X] Verify all pre-filled fields are correct and user inputs are accurately reflected in the PDF.
    *   [X] Check basic error handling (e.g., what happens if PDF template is missing?).

## Phase 2: Enhancements & Production Readiness

**Goal:** Refine the MVP, add robustness, improve user experience, and prepare for deployment.

1.  **Step 8: Advanced Form Features & Validation (Iterative)**
    *   [ ] Client-side JavaScript validation (`static/js/script.js`) for better UX (e.g., required fields, data types like date/email, character limits for text areas like 8, 10, and supplemental questions).
    *   [X] Server-side validation enhancement: More comprehensive checks.
    *   [X] Implement calculation for Field 12d (Total) on the frontend (JS) and ensure backend recalculates for accuracy.
    *   [X] Improve handling of checkbox for Field 3.

2.  **Step 9: Interactive PDF Review & Signing Workflow (New Major Feature)**
    *   [X] Objective: Allow users to review the generated PDF, sign it digitally (typed name), and download the signed version.
    *   [X] Task: Add "Next/Review PDF" button to the main intake form (`templates/form.html`). (Implicitly Step 1 submit)
    *   [X] Task: Create a new HTML template for the PDF review page. This page will display the generated (unsigned) PDF (e.g., using an `<embed>` or `<object>` tag, or a JS PDF viewer library). (`signature.html`, no direct PDF embed)
    *   [X] Task: Implement a route in `app.py` to serve this review page and pass the path to the generated PDF. (`/sign` route)
    *   [ ] Task: Add an "Edit" button on the review page that navigates the user back to the main form, pre-filling it with their previously entered data.
    *   [X] Task: Add a "Signature" input field (text input for typed name) on the review page.
    *   [X] Task: (Prerequisite/Parallel) Modify the master `sf95.pdf` template: move the signature block from its current location (likely page 1) to page 2. Update `data/pdf_field_map.json` if the PDF signature field's internal name changes. (Current setup works without moving block)
    *   [X] Task: Update `utils/pdf_filler.py` to accept the typed signature from the review page and fill the designated signature field in the PDF. (Logic in `app.py`)
    *   [X] Task: Upon submission of the signature, regenerate the PDF (now including the signature). Redisplay this signed PDF on the same (or a dedicated confirmation) page. (Success page with download link)
    *   [X] Task: Provide a "Download Signed PDF" button for the user to download the finalized, signed document.

3.  **Step 10: Improved Styling & Responsiveness** 
    *   [ ] Enhance `static/css/style.css` for a professional look and feel.
    *   [ ] Ensure the form is responsive and works well on different screen sizes.

4.  **Step 11: Robust Error Handling & Logging** 
    *   [ ] Implement comprehensive error handling throughout the backend (database errors, file system errors, PDF generation errors, notification failures).
    *   [ ] Provide user-friendly error messages on the frontend.
    *   [/] Set up structured logging for application events and errors.

5.  **Step 12: Security Hardening** 
    *   [ ] Implement CSRF protection (Flask-WTF can help).
    *   [ ] Ensure proper input sanitization to prevent XSS and SQL injection (ORM like SQLAlchemy can help with SQLi).
    *   [ ] Review file permissions for `data/` directory and database file.
    *   [ ] Consider rate limiting for form submissions if abuse is a concern.

6.  **Step 13: Configuration Management** 
    *   [ ] Move configurable parameters (email settings, database path if not fixed) to environment variables or a configuration file (e.g., `config.py`, `.env`).

7.  **Step 14: Admin Portal Features (New Major Feature)**
    *   [X] Objective: Provide a secure and comprehensive backend interface for administrators to manage submissions and data.
    *   [X] Task: Implement secure admin authentication and authorization (e.g., login for authorized personnel).
    *   [X] Task: Create an admin dashboard/interface (new HTML templates and Flask routes).
    *   [X] Task: Develop an interactive data grid/table view of all submissions:
        *   [X] Display key claimant information (e.g., Name, Email Address).
        *   [/] Show status indicators: `PDF Created Timestamp`, `PDF Signed Timestamp`, `Signature Status` (e.g., Unsigned, Signed).
        *   [ ] Allow sorting of the data by various columns.
        *   [ ] Implement filtering capabilities (e.g., by signature status, date range).
        *   [X] Provide an option to download the displayed/filtered data as a CSV file.
    *   [X] Task: PDF Management and Access:
        *   [X] Ensure PDF filenames are standardized, ideally based on the claimant's name (e.g., `John_Doe.pdf`), with only one (the latest signed) PDF version per person stored in `data/filled_forms/` or a configured production path.
        *   [X] Provide secure links or buttons for admins to download individual signed PDFs. (Download on success page, admin could be enhanced)
    *   [ ] Task: Consolidated PDF Download Feature:
        *   [ ] Implement checkboxes next to each entry in the admin data grid.
        *   [ ] Add functionality for admins to select multiple entries.
        *   [ ] Create a feature to generate and download a single, consolidated PDF file containing the latest version of each selected claimant's signed SF-95 form.
    *   [X] (Implied database update for `claims` table: add `pdf_created_timestamp`, `pdf_signed_timestamp`, `signature_status` columns. This is also relevant to Step 9: Interactive PDF Review & Signing Workflow). (Timestamps present, `filled_pdf_filename` serves as status)

8.  **Step 15: Dockerization** 
    *   [ ] Create a `Dockerfile` to containerize the application.
    *   [ ] Include Python, dependencies, and application code.
    *   [ ] Test running the application via Docker.

9.  **Step 16: Unit & Integration Testing** 
    *   [ ] Write unit tests for utility functions (PDF filling, notification, data handling, new supplemental field processing).
    *   [ ] Write integration tests for the main application flow, including the new review/sign workflow and admin functionalities.
    *   [ ] Consider using `pytest`.

10. **Step 17: Deployment Preparation** 
    *   [ ] Plan deployment strategy (e.g., which server, how to manage the Docker container, web server like Gunicorn/Nginx in front of Flask).
    *   [ ] Note: Target deployment domain: `investigateJ6.org/west-plaza-lawsuit`.
    *   [ ] Set up DNS for the target URL to point to the server.
    *   [ ] Configure HTTPS (e.g., Let's Encrypt).
    *   [ ] Add sub-task: Prepare detailed step-by-step instructions for setting up the application, database, and PDF storage on the target server environment.

## Phase 3: Post-Deployment & Maintenance

1.  **Step 18: User Acceptance Testing (UAT)** 
    *   [ ] Allow actual users (internal team first) to test the application, including the new review/sign flow and admin access (if applicable to testers).
    *   [ ] Gather feedback and iterate.

2.  **Step 19: Documentation Review & Update** 
    *   [ ] Ensure `README.md` is up-to-date with deployment and usage instructions, including details about new features.
    *   [ ] Document any operational procedures (backups, monitoring, admin portal usage).

3.  **Step 20: Ongoing Monitoring & Maintenance** 
    *   [ ] Monitor application logs for errors.
    *   [ ] Perform regular backups of the database and filled PDFs.
    *   [ ] Update dependencies as needed.

This roadmap provides a structured approach. Timelines are estimates and can be adjusted based on complexity encountered, especially with PDF field mapping, the new review/signing workflow, admin portal development, and external dependencies like SMTP server setup.
