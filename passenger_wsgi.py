import os
import sys

# NOTE: Passenger should use the venv's Python interpreter via PassengerPython directive in .htaccess or server config.
# Remove activate_this.py logic (not present in modern venvs).

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
