import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(BASE_DIR), "uploads"))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 8

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/bmp", "application/dicom"}
MAX_UPLOAD_SIZE = 20 * 1024 * 1024
