# نقطة دخول تطبيق ITDS-AI
import os

from flask import Flask

from config import SECRET_KEY
from database import init_database
from routes.admin_routes import admin_bp
from routes.api import api_bp
from routes.auth import auth_bp
from routes.employee_routes import employee_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY

init_database()

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(api_bp)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)
