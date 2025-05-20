# West Plaza J6 FTCA Form 95 Intake

This project is a secure, self-hosted web application designed to facilitate the intake of user information for filling out the Standard Form 95 (SF-95) - Claim for Damage, Injury, or Death.

## Project Overview

- **Multi-Step Frontend User Form:** A responsive web form guides users through data entry and a separate signature step, corresponding to fields on the SF-95 PDF.
- **Data Storage:** Submitted data is stored securely in a local SQLite database.
- **PDF Generator:** The backend uses the submitted data to automatically fill the SF-95 PDF template.
- **Admin Interface:** A basic admin view to see submitted claims and download all data as a CSV file.

This application is built with a focus on self-hosting and data control.

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python (Flask)
- **Session Management:** Flask-Session (Filesystem-based)
- **Database:** SQLite
- **PDF Filling:** `fillpdf` (Python library)
- **Containerization:** Docker (optional)

## Development Setup

---

### Updating Production Deployment (investigatej6.org/west-plaza-lawsuit)

To update your deployment at investigatej6.org/west-plaza-lawsuit, SSH into your FastComet server and run:

```sh
cd /path/to/your/west-plaza-j6-ftca-form95
# Pull the latest changes from GitHub
git pull origin main
# (If using virtualenv)
source venv/bin/activate
pip install -r requirements.txt
# Restart your Flask app (adjust as needed):
# For gunicorn:
# systemctl restart west-plaza-j6-ftca-form95
# Or for nohup/python:
pkill -f app.py
nohup python3 src/app.py &
```

*Replace `/path/to/your/west-plaza-j6-ftca-form95` with your actual project path. Your database will persist between updates.*

---

1.  **Prerequisites:**
    *   Python 3.8+
    *   Pip (Python package installer)
    *   Docker (optional, for containerized deployment)
    *   Git

2.  **Clone the Repository:**
    ```bash
    git clone <repository-url> # Replace <repository-url> with the actual URL
    cd west-plaza-j6-ftca-form95
    ```

3.  **Create and Activate a Virtual Environment:**
    ```bash
    python3 -m venv venv  # Or python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

---

## 🚀 Deployment & Update Instructions (FastComet / investigatej6.org/west-plaza-lawsuit)

To update your deployment on FastComet:

1. **SSH into your FastComet server**
2. **Navigate to your project directory:**
   ```sh
   cd /path/to/your/west-plaza-j6-ftca-form95
   ```
   *(Replace with the actual path on your server)*
3. **Pull the latest code:**
   ```sh
   git pull origin main
   ```
4. **(If using a virtualenv) Activate it and install requirements:**
   ```sh
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. **Restart your Flask app:**
   - If using gunicorn:
     ```sh
     systemctl restart west-plaza-j6-ftca-form95
     ```
   - Or if running with nohup/python:
     ```sh
     pkill -f app.py
     nohup python3 src/app.py &
     ```

**Note:**
- Your database is now persistent and will NOT be reset on app restart.
- Adjust the restart commands as needed for your server/process manager.
- If you need help with deployment automation, see the project issues or contact the maintainer.


4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **PDF Template:**
    *   The SF-95 PDF template (`sf95.pdf`) is included in the `data/` directory.

6.  **Environment Variables (Optional):**
    *   `FLASK_SECRET_KEY`: Set this for production or if you want to override the default development key. Create a `.env` file in the project root (add it to `.gitignore` if you haven't already):
      ```
      FLASK_SECRET_KEY='your_very_strong_random_secret_key'
      ```

## Running the Application Locally

1.  **Ensure virtual environment is activated.**
2.  **Navigate to the `src` directory:**
    ```bash
    cd src
    ```
3.  **Run the Flask development server:**
    ```bash
    python3 app.py # Or python app.py
    ```
4.  Open your web browser and go to `http://127.0.0.1:61663` (or the port specified in `app.py`).

## Docker (Optional)

1.  **Build the Docker image (from the project root directory):**
    ```bash
    docker build -t west-plaza-form .
    ```
2.  **Run the Docker container:**
    ```bash
    docker run -p 61663:61663 west-plaza-form # Match the port used in app.py
    ```

## Project Structure

```
west-plaza-j6-ftca-form95/
├── data/
│   ├── sf95.pdf            # Template PDF
│   ├── database/
│   │   └── claims.db       # SQLite database (created on first run)
│   ├── filled_forms/       # Stores generated PDFs (gitignored contents)
│   └── csv/                # Stores CSV exports (gitignored contents)
├── docs/
│   ├── project.md
│   ├── plan.md
│   └── python-flask-stack.md
├── src/
│   ├── app.py              # Main Flask application
│   ├── static/             # CSS, JavaScript, Images
│   │   ├── css/style.css
│   │   └── js/script.js    # (currently minimal)
│   ├── templates/          # HTML templates (form.html, signature.html, etc.)
│   └── utils/              # Utility scripts (currently minimal)
│       └── __init__.py
├── venv/                   # Python virtual environment (gitignored)
├── flask_session/          # Flask session files (gitignored)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── .gitignore              # Specifies intentionally untracked files by Git
└── README.md               # This file
└── debugging-logs.txt      # Log file (gitignored)
