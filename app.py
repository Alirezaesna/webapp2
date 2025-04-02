import os
import logging
from flask import Flask
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')
    
# Create empty JSON files if they don't exist
data_files = ['users.json', 'loans.json', 'installments.json']
for file in data_files:
    filepath = os.path.join('data', file)
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            f.write('[]')

# Import routes after initializing app to avoid circular imports
from routes import *
