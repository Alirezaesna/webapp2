from app import app
from utils import create_admin_if_not_exists

# Initialize admin user when running the application directly
if __name__ == "__main__":
    with app.app_context():
        create_admin_if_not_exists()
    app.run(host="0.0.0.0", port=5000, debug=True)
