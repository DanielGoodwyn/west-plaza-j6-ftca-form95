# West Plaza J6 FTCA Form 95 Intake

This project is a secure, self-hosted web application designed to facilitate the intake of user information for filling out the Standard Form 95 (SF-95) - Claim for Damage, Injury, or Death.

## Project Overview

- **Frontend User Form:** A responsive web form where users input data corresponding to fields on the SF-95 PDF.
- **Data Storage:** Submitted data is stored securely in a local SQLite database.
- **PDF Generator:** The backend uses the submitted data to automatically fill the SF-95 PDF template.
- **Notifier:** An internal notification (email) is sent once a PDF is generated.

This application is built with a focus on self-hosting and data control, avoiding external APIs and cloud services.

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python (Flask)
- **Database:** SQLite
- **PDF Filling:** Python (`fillpdf` or similar library)
- **Notifications:** Python (`smtplib` for email)
- **Containerization:** Docker

## Development Setup

1.  **Prerequisites:**
    *   Python 3.8+
    *   Pip (Python package installer)
    *   Docker (optional, for containerized deployment)
    *   Git

2.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd west-plaza-j6-ftca-form95
    ```

3.  **Create and Activate a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r src/requirements.txt
    ```

5.  **Download PDF Template:**
    *   Download the SF-95 form from [GSA Forms Library](https://www.gsa.gov/reference/forms/claim-for-damage-injury-or-death).
    *   Save it as `sf95.pdf` in the `data/` directory.
    *   **Crucial Step:** Identify the exact field names within the fillable `sf95.pdf`. This may require Adobe Acrobat Pro or a PDF analysis tool. These names will be needed for mapping form inputs to PDF fields.

6.  **Configure Environment (if necessary):**
    *   Set up any environment variables, e.g., for email notifications (SMTP server details, recipient addresses). This might involve creating a `.env` file (ensure it's in `.gitignore`).

## Running the Application Locally

1.  **Ensure virtual environment is activated.**
2.  **Navigate to the `src` directory:**
    ```bash
    cd src
    ```
3.  **Run the Flask development server:**
    ```bash
    flask run
    # or python app.py
    ```
4.  Open your web browser and go to `http://127.0.0.1:5000` (or the port specified by Flask).

## Docker (Optional)

1.  **Build the Docker image:**
    ```bash
    docker build -t west-plaza-form .
    ```
2.  **Run the Docker container:**
    ```bash
    docker run -p 5000:5000 west-plaza-form
    ```

## Project Structure

```
west-plaza-j6-ftca-form95/
├── data/
│   └── sf95.pdf            # Template PDF (to be downloaded)
│   └── form_data.db        # SQLite database (will be created)
├── docs/
│   ├── README.md           # This file (will be moved here)
│   ├── project.md
│   ├── plan.md
│   └── python-flask-stack.md
├── src/
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── script.js
│   ├── templates/
│   │   └── form.html         # HTML form template
│   └── utils/
│       ├── __init__.py
│       ├── pdf_filler.py     # Logic for filling PDF
│       └── notifier.py       # Logic for sending notifications
├── venv/                   # Python virtual environment (ignored by Git)
├── Dockerfile
└── .gitignore
```
