from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ============================================================
# MISSING PERSON
# ============================================================

class MissingPerson(db.Model):

    __tablename__ = "missing_person"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ========================================================
    # REPORT TRACKING
    # ========================================================

    report_id = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="submitted"
    )

    # ========================================================
    # MISSING PERSON DETAILS
    # ========================================================

    name = db.Column(
        db.String(100),
        nullable=False
    )

    age = db.Column(
        db.Integer
    )

    gender = db.Column(
        db.String(20)
    )

    height = db.Column(
        db.String(20)
    )

    clothing = db.Column(
        db.String(200)
    )

    # ========================================================
    # LAST SEEN LOCATION
    # ========================================================

    last_seen_location = db.Column(
        db.String(200)
    )

    last_seen_latitude = db.Column(
        db.Float
    )

    last_seen_longitude = db.Column(
        db.Float
    )

    last_seen_date = db.Column(
        db.String(50)
    )

    description = db.Column(
        db.Text
    )

    # ========================================================
    # AI
    # ========================================================

    embedding = db.Column(
        db.Text
    )

    # ========================================================
    # UPLOADED IMAGE
    # ========================================================

    photo_path = db.Column(
        db.String(300)
    )

    # ========================================================
    # REPORTER DETAILS
    # ========================================================

    reporter_name = db.Column(
        db.String(100)
    )

    relationship = db.Column(
        db.String(100)
    )

    phone = db.Column(
        db.String(20)
    )

    email = db.Column(
        db.String(120)
    )

    # ========================================================
    # METADATA
    # ========================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# FOUND PERSON
# ============================================================

class FoundPerson(db.Model):

    __tablename__ = "found_person"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ========================================================
    # REPORT TRACKING
    # ========================================================

    report_id = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="submitted"
    )

    # ========================================================
    # FOUND PERSON DETAILS
    # ========================================================

    estimated_age = db.Column(
        db.Integer
    )

    gender = db.Column(
        db.String(20)
    )

    height = db.Column(
        db.String(20)
    )

    clothing = db.Column(
        db.String(200)
    )

    # ========================================================
    # FOUND LOCATION
    # ========================================================

    found_location = db.Column(
        db.String(200)
    )

    found_latitude = db.Column(
        db.Float
    )

    found_longitude = db.Column(
        db.Float
    )

    found_date = db.Column(
        db.String(50)
    )

    found_time = db.Column(
        db.String(20)
    )

    condition = db.Column(
        db.String(100)
    )

    description = db.Column(
        db.Text
    )

    # ========================================================
    # AI
    # ========================================================

    embedding = db.Column(
        db.Text
    )

    # ========================================================
    # UPLOADED IMAGE
    # ========================================================

    photo_path = db.Column(
        db.String(300)
    )

    # ========================================================
    # FINDER DETAILS
    # ========================================================

    finder_name = db.Column(
        db.String(100)
    )

    phone = db.Column(
        db.String(20)
    )

    email = db.Column(
        db.String(120)
    )

    organization = db.Column(
        db.String(150)
    )

    police_station = db.Column(
        db.String(150)
    )

    # ========================================================
    # METADATA
    # ========================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# PENDING REPORT
# ============================================================

class PendingReport(db.Model):

    __tablename__ = "pending_reports"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ========================================================
    # VERIFICATION
    # ========================================================

    token = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    # missing / found

    report_type = db.Column(
        db.String(20),
        nullable=False
    )

    # ========================================================
    # TEMPORARY REPORT DATA
    # ========================================================

    report_data = db.Column(
        db.Text,
        nullable=False
    )

    # ========================================================
    # TEMPORARY PHOTO + AI
    # ========================================================

    photo_path = db.Column(
        db.String(300)
    )

    embedding = db.Column(
        db.Text
    )

    # ========================================================
    # EMAIL VERIFICATION
    # ========================================================

    email = db.Column(
        db.String(150),
        nullable=False
    )

    otp_hash = db.Column(
        db.String(255),
        nullable=False
    )

    otp_expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    otp_attempts = db.Column(
        db.Integer,
        default=0
    )

    # ========================================================
    # METADATA
    # ========================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# ORGANIZATION
# ============================================================

class Organization(db.Model):

    __tablename__ = "organizations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    organization = db.Column(
        db.String(200),
        nullable=False
    )

    role = db.Column(
        db.String(100),
        nullable=False
    )

    full_name = db.Column(
        db.String(150),
        nullable=False
    )

    government_id = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    id_card = db.Column(
        db.String(255),
        nullable=False
    )

    email_verified = db.Column(
        db.Boolean,
        default=False
    )

    email_verification_token = db.Column(
        db.String(255),
        nullable=True
    )

    verified = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )