import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:

    # ==========================================
    # Flask Security
    # ==========================================

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "missinglink_secret_key"
    )


    # ==========================================
    # Database - PostgreSQL
    # ==========================================

    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set."
        )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # ==========================================
    # Upload Folders
    # ==========================================

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "static",
        "uploads"
    )

    ID_CARD_FOLDER = os.path.join(
        BASE_DIR,
        "static",
        "id_cards"
    )