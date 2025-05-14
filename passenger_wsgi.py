import os
import sys

# Determine the project directory (where this passenger_wsgi.py file is located)
project_directory = os.path.dirname(os.path.abspath(__file__))

# Add the project directory to Python's search path
if project_directory not in sys.path:
    sys.path.insert(0, project_directory)

# Determine the path to the 'src' directory, where app.py is located
# This assumes app.py is directly inside a 'src' folder within your project_directory
src_directory = os.path.join(project_directory, 'src')

# Import the Flask application instance
# 'app' is the variable name of your Flask application instance in src/app.py
# Passenger (and other WSGI servers) typically look for an 'application' callable.
from src.app import app as application

# If you need to set any environment variables specifically for the production environment
# and can't do it through cPanel or .env, you could potentially do it here, e.g.:
# os.environ['FLASK_ENV'] = 'production'
