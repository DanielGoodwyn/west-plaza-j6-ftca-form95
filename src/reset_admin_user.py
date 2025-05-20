import sys
import os
import importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Dynamically import app
app_spec = importlib.util.spec_from_file_location("app", os.path.join(os.path.dirname(__file__), "app.py"))
app_module = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(app_module)
app = app_module.app

# Dynamically import helpers
helpers_spec = importlib.util.spec_from_file_location("helpers", os.path.join(os.path.dirname(__file__), "utils", "helpers.py"))
helpers_module = importlib.util.module_from_spec(helpers_spec)
helpers_spec.loader.exec_module(helpers_module)
get_db = helpers_module.get_db

from werkzeug.security import generate_password_hash

with app.app_context():
    db = get_db()
    db.execute("DELETE FROM users WHERE username=?", ('admin',))
db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ('admin', generate_password_hash('SuperSecret123!')))
db.commit()
print('Admin user reset.')
