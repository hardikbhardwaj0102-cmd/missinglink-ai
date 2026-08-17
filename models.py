from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class MissingPerson(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)

    # Missing Person Details
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    height = db.Column(db.String(20))
    clothing = db.Column(db.String(200))
    last_seen_location = db.Column(db.String(200))
    last_seen_date = db.Column(db.String(50))
    description = db.Column(db.Text)
    embedding = db.Column(db.Text)

    # Uploaded Image
    photo_path = db.Column(db.String(300))

    # Reporter Details
    reporter_name = db.Column(db.String(100))
    relationship = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FoundPerson(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)

    # Found Person Details
    estimated_age = db.Column(db.Integer)

    gender = db.Column(db.String(20))

    height = db.Column(db.String(20))

    clothing = db.Column(db.String(200))

    found_location = db.Column(db.String(200))

    found_date = db.Column(db.String(50))

    found_time = db.Column(db.String(20))

    condition = db.Column(db.String(100))

    description = db.Column(db.Text)
    embedding = db.Column(db.Text)
    photo_path = db.Column(db.String(300))
    

    # Finder Details
    finder_name = db.Column(db.String(100))

    phone = db.Column(db.String(20))

    email = db.Column(db.String(120))

    organization = db.Column(db.String(150))

    police_station = db.Column(db.String(150))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PendingReport(db.Model):

    __tablename__ = "pending_reports"

    id = db.Column(db.Integer, primary_key=True)

    # Unique verification identifier
    token = db.Column(db.String(100), unique=True, nullable=False)

    # missing / found
    report_type = db.Column(db.String(20), nullable=False)

    # Temporary report data
    report_data = db.Column(db.Text, nullable=False)

    # Temporary uploaded photo + embedding
    photo_path = db.Column(db.String(300))
    embedding = db.Column(db.Text)

    # Email verification
    email = db.Column(db.String(150), nullable=False)

    otp_hash = db.Column(db.String(255), nullable=False)

    otp_expires_at = db.Column(db.DateTime, nullable=False)

    otp_attempts = db.Column(db.Integer, default=0)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    
class Organization(db.Model):

    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)

    organization = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(100), nullable=False)

    full_name = db.Column(db.String(150), nullable=False)

    government_id = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(150), unique=True, nullable=False)

    phone = db.Column(db.String(20), nullable=False)

    password = db.Column(db.String(255), nullable=False)

    id_card = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    verified = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)