# إعدادات تطبيق ITDS-AI
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "itds.db")
SECRET_KEY = os.environ.get("ITDS_SECRET_KEY", "itds-ai-local-dev-key-change-in-production")

