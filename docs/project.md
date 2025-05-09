# Project Specification: FTCA Form 95 Intake Web App

## 1. Introduction

This document outlines the high-level specification and architecture for the FTCA Form 95 Intake web application. The primary goal is to provide a secure, self-hosted solution for users to submit information that will be used to populate the Standard Form 95 (SF-95).

The application URL will be `investigatej6.org/west-plaza-lawsuit` (Note: DNS and web server configuration for this URL are outside the immediate scope of application development but should be planned for deployment).

## 2. Core Features

1.  **Front End Online User Form Intake:**
    *   A responsive, user-friendly HTML form.
    *   Fields will directly correspond to designated locations on the SF-95 PDF.
    *   Specific fields will be pre-filled with default text; some pre-filled fields will be editable by the user, while others will be fixed.

2.  **Data Storage Backend:**
    *   Submitted form data will be saved in a structured format using an SQLite database.
    *   The database will be self-hosted and stored locally on the server.

3.  **PDF Generator:**
    *   The backend will use the submitted (and pre-filled) form data to populate a fillable SF-95 PDF template.
    *   A critical step involves mapping HTML form field names to the actual internal field names of the fillable PDF.

4.  **Notifier:**
    *   Upon successful PDF generation, an email notification (or an internal system alert placeholder) will be sent to a designated internal team.

## 3. Pre-filled and User-filled Fields Specifics

(Based on the GSA SF-95 form structure)

*   **Fixed Pre-filled Fields:**
    *   Field 1: "US Capitol Police"
    *   Field 6: "01/06/2021"
    *   Field 7: "1:00 PM"
    *   Field 9 (Box 1 & 2): "N/A"
    *   Field 11 ("Name"): "See FBI and Capitol Police database."
    *   Field 11 ("Address"): "The FBI and Capitol Police already maintain a database of 1,000+ witnesses."
    *   Field 12a ("Property Damage"): "0.00"

*   **Editable Pre-filled Fields (User can modify/add):**
    *   Field 8 (Basis of Claim): Pre-filled with a detailed statement; users can add a few sentences.
        *   Default: "While the claimant was protesting on January 6, 2021 at the West side of the U.S. Capitol, the Capitol Police and D.C. Metropolitan Police acting on behalf of the Capitol Police used excessive force against the claimant causing claimant physical injuries. The excessive force took the form of various munitions launched against the protesters including but not limited to: pepper balls, rubber balls or bullets some filled with Oleoresin Capsicum (\"OC\"), FM 303 projectiles, sting balls, flash bang, sting bomb and tear gas grenades, tripple chasers,pepper spray, CS Gas and physical strikes with firsts or batons."
    *   Field 10 (Nature and Extent of Injury): Pre-filled; users can add a few sentences.
        *   Default: "The claimant went to the U.S. Capitol to peacefully protest the presidential election. While the claimant was in the area of the West Side of the U.S. Capitol building police launched weapons referenced above and used excessive force. The claimant was struck and or exposed to the launched munitions and/or OC or CS Gas and suffered injuries as a result."
    *   Field 12b ("Personal Injury"): Pre-filled with "90,000.00"; user can change this amount.
    *   Field 12c ("Wrongful Death"): Pre-filled with "0.00"; user can change this amount (though typically one wouldn't claim both personal injury and wrongful death for oneself).

*   **User-Input Fields (User must fill):**
    *   Field 2: Claimant's personal information (Name, Address, DOB, Phone, etc.).
    *   Field 3: Type of employment (Checkbox for Military, Civilian, Other).
    *   Field 4: Marital Status.
    *   Field 5: Name and Address of Spouse (if any).
    *   Field 13b: Signature of Claimant (Digital representation or typed name, depending on legal acceptance for this context. For initial MVP, a typed name will suffice).
    *   Field 14: Date Signed.

*   **Calculated Fields:**
    *   Field 12d ("Total"): Sum of 12a, 12b, 12c. This will be calculated by the backend.

## 4. Architecture Overview

*   **Client-Side (Browser):**
    *   Renders HTML form (`form.html`).
    *   Uses CSS (`style.css`) for styling.
    *   Uses JavaScript (`script.js`) for client-side validation (e.g., required fields, data formats) and potentially dynamic updates (e.g., calculating 12d live, though backend calculation is also essential).

*   **Server-Side (Flask Application - `app.py`):**
    *   **Routes:**
        *   `/` or `/form`: HTTP GET to display the form.
        *   `/submit`: HTTP POST to receive form data.
    *   **Logic:**
        *   Handles form submission.
        *   Validates and sanitizes data.
        *   Merges user input with pre-filled data.
        *   Calculates derived fields (e.g., Field 12d Total).
        *   Stores data in the SQLite database (`form_data.db` via `utils/database_handler.py` - to be created).
        *   Invokes PDF filling logic (`utils/pdf_filler.py`).
        *   Triggers notification (`utils/notifier.py`).
        *   Returns a success/failure response to the user.

*   **Data Layer (`data/`):**
    *   `sf95.pdf`: The original fillable PDF template.
    *   `form_data.db`: SQLite database file.
    *   `filled_forms/`: (Proposed directory) To store generated PDFs, possibly named by a unique ID or claimant name + timestamp.

*   **Utilities (`src/utils/`):**
    *   `pdf_filler.py`: Contains functions to interact with the PDF template using a library like `fillpdf`.
    *   `notifier.py`: Contains functions to send email notifications using `smtplib`.

## 5. Constraints Reminder

*   Entirely self-hosted.
*   No third-party APIs or cloud services for core functionality.
*   All logic runs on infrastructure under direct control.
*   Cross-platform compatible and containerizable (Docker).

## 6. Key Considerations & Future Work

*   **PDF Field Mapping:** The most critical initial task is to accurately identify the field names within the `sf95.pdf` template. This is essential for `pdf_filler.py`.
*   **Security:** Sanitize all user inputs. Protect against common web vulnerabilities (XSS, CSRF - Flask provides some protection). Secure the database file and generated PDFs.
*   **Error Handling:** Robust error handling for form validation, database operations, PDF generation, and notifications.
*   **Scalability:** While SQLite is chosen for simplicity, if high concurrency is expected, PostgreSQL could be considered, though it adds setup complexity.
*   **Legal Compliance for Signature:** Clarify requirements for what constitutes an acceptable signature (e.g., typed name vs. actual digital signature capabilities which are more complex).
*   **Data Management:** Plan for how submitted data and generated PDFs will be managed, backed up, and potentially archived or deleted according to policy.
