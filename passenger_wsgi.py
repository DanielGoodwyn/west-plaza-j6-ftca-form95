import os
import sys

# --- Activate the virtual environment for Passenger ---
venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'bin', 'activate_this.py')
if os.path.exists(venv_path):
    with open(venv_path) as f:
        exec(f.read(), {'__file__': venv_path})
else:
    raise RuntimeError(f"Virtualenv activate_this.py not found at {venv_path}")

# Determine the project directory (where this passenger_wsgi.py file is located)
project_directory = os.path.dirname(os.path.abspath(__file__))

# Add the project directory to Python's search path
if project_directory not in sys.path:
    sys.path.insert(0, project_directory)

# Determine the path to the 'src' directory, where app.py is located
src_directory = os.path.join(project_directory, 'src')

# Import the Flask application instance
from src.app import app as application

# Optionally set environment variables for production
# os.environ['FLASK_ENV'] = 'production'
