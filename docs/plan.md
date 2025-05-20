# FTCA Form 95 Intake Web App – Task Checklist

[✅] Initialize Git repository
[✅] Set up Python virtual environment
[✅] Create basic Flask application structure (app.py, templates/, static/, utils/, data/)
[✅] Create initial requirements.txt (Flask)
[✅] Draft README.md, project.md, plan.md, python-flask-stack.md
[✅] Download the SF-95 PDF (data/sf95.pdf)
[✅] Identify all fillable field names in sf95.pdf
[✅] Use PDF analysis tools to list field names and their types
[✅] Deliver a machine-readable mapping file (data/pdf_field_map.json)
[✅] Update PDF filling logic to use this map
[✅] Create frontend HTML form in templates/form.html
[✅] Include input fields for user-filled and pre-filled sections
[✅] Add 'Email Address' and supplemental essay questions (store in DB, not PDF)
[✅] Pre-populate fields with specified defaults
[🔲] Basic styling with static/css/style.css for usability
[✅] Flask route (/submit) to handle POST requests
[✅] Basic server-side validation for submitted data
[✅] All required fields present and not empty
[✅] Correct data formats for dates, numbers
[🔲] Reasonable string lengths for text areas
[✅] User-friendly error messages and form repopulation
[✅] Set up SQLite database and schema for all fields
[✅] Insert validated data into SQLite
[✅] Add sqlite3 to requirements.txt
[✅] Fill the sf95.pdf with data from a submission
[✅] Choose and install PDF filling library
[✅] Create PDF filler script/function
[✅] Save filled PDF to output directory with unique filenames
[✅] Integrate into /submit route
[✅] Verify all data is accurately transferred to PDF
[🔲] User Login and Editing After Signature
[🔲] User account flow: users submit with email (no login required); email becomes username; only one submission per email (new replaces old); after submission, prompt to create password (optional); if skipped, store temp password in DB (user does not know it; admin can provide); users can set/reset password later via link
[🔲] Authentication & roles: login page for users, admins, superadmin; only admins/superadmin see admin dashboard; users can edit/download own submission/PDF; admins can manage all; superadmin can manage users/admins (add/remove/edit/promote/demote); only one superadmin
[🔲] Password management: passwords hashed in DB; users/admins can reset via email link
[🔲] Access control & security: all sensitive actions require authentication; no user can access another's PDF unless admin/superadmin
[🔲] Email verification (last phase): require before login/editing; prevents someone else using their email
[🔲] Admin impersonation (optional, low priority): admins may impersonate users for support
[🔲] Basic Notification
[✅] Objective: Send a simple notification upon successful PDF generation. (Logging done, not email)
[🔲] Task: Create utils/notifier.py. Write a function to send an email using smtplib.
[🔲] Configuration: Allow setting SMTP server, sender/recipient emails (via env or config file, keep sensitive info out of Git)
[🔲] Integrate into /submit route. (Logging is integrated)
[🔲] For MVP, just log to console: "Notification: PDF generated for [Claimant Name]".
[🔲] Add/Edit button on review page to allow user to edit submission before signing
[🔲] Client-side JavaScript validation for better UX (required fields, data types, char limits)
[🔲] Server-side validation enhancement: more comprehensive checks
[🔲] Calculation for Field 12d (Total) on frontend and backend
[🔲] Improve handling of checkbox for Field 3
[🔲] Interactive PDF review & signing workflow (review, sign, download signed PDF)
[🔲] Improved styling & responsiveness (static/css/style.css)
[🔲] Robust error handling & logging (comprehensive backend errors, user-friendly frontend messages, structured logging)
[🔲] Security hardening (CSRF protection, input sanitization, file permissions, rate limiting)
[🔲] Configuration management (move config to env/config file)
[🔲] Admin portal features (dashboard, data grid, CSV download, PDF management, consolidated PDF download)
[🔲] Dockerization (Dockerfile, dependencies, test Docker run)
[🔲] Unit & integration testing
[🔲] Documentation review & update (README.md, operational procedures)
[🔲] Ongoing monitoring & maintenance (logs, backups, dependency updates)
[🔲] User Acceptance Testing (UAT)
[🔲] Documentation Review & Update
[🔲] Ongoing Monitoring & Maintenance
[🔲] Only admins and superadmin see the admin dashboard.
[🔲] Users can log in to edit their own submission and download their own PDF, but cannot access or download others' PDFs.
[🔲] Admins can view/edit/download all submissions and PDFs.
[🔲] Superadmin can manage (add/remove/edit/promote/demote) users and admins, and has all admin powers.
[🔲] Only one superadmin account exists.
[🔲] Passwords are securely hashed in the database.
[🔲] Users and admins can reset their password via a "forgot password" flow (email-based link).
[🔲] All sensitive actions require authentication.
[🔲] No user can access or download another user's PDF unless they are admin or superadmin.
[🔲] Email verification will be required before allowing login/editing (to prevent someone else from using their email). Implement this as the final step after all other features are complete.
[🔲] Admins may impersonate users for support purposes, if not difficult to implement.
