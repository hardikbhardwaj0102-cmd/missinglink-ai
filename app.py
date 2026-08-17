import os
import uuid
from itsdangerous import URLSafeSerializer
from ai.face_service import get_face_embedding
import json
from brevo import Brevo
from brevo.transactional_emails import (
    SendTransacEmailRequestSender,
    SendTransacEmailRequestToItem,
)
import secrets
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from ai.face_matcher import find_best_matches
from dotenv import load_dotenv
from supabase import create_client, Client
load_dotenv()
from config import Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
from datetime import timedelta


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
from models import (
    db,
    MissingPerson,
    FoundPerson,
    PendingReport,
    Organization
)

# ==========================================
# Flask App
# ==========================================

app = Flask(__name__)

app.config.from_object(Config)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
@app.after_request
def add_security_headers(response):

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, "
        "post-check=0, pre-check=0, max-age=0"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

brevo_client = Brevo(
    api_key=os.getenv("BREVO_API_KEY")
)

serializer = URLSafeSerializer(app.config["SECRET_KEY"])

def send_email(to_email, to_name, subject, html_content):
    try:
        result = brevo_client.transactional_emails.send_transac_email(
            subject=subject,
            html_content=html_content,
            sender=SendTransacEmailRequestSender(
                name=os.getenv("BREVO_SENDER_NAME", "MissingLink AI"),
                email=os.getenv("BREVO_SENDER_EMAIL"),
            ),
            to=[
                SendTransacEmailRequestToItem(
                    email=to_email,
                    name=to_name
                )
            ]
        )

        print("BREVO EMAIL SENT:", result.message_id)
        return True

    except Exception as e:
        print("BREVO EMAIL ERROR:", e)
        return False
# ==========================================
# OTP VERIFICATION
# ==========================================

def generate_otp():
    return str(secrets.randbelow(900000) + 100000)


def send_otp_email(to_email, to_name, otp):

    return send_email(
        to_email=to_email,
        to_name=to_name or "User",
        subject="MissingLink AI - Email Verification OTP",
        html_content=f"""
            <div style="
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: auto;
                padding: 30px;
                color: #1f2937;
            ">

                <h2 style="color:#2563eb;">
                    MissingLink AI
                </h2>

                <p>Hello {to_name or "User"},</p>

                <p>
                    We received a request to submit a report
                    on MissingLink AI using this email address.
                </p>

                <p>
                    Your verification code is:
                </p>

                <div style="
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    text-align: center;
                    padding: 20px;
                    margin: 20px 0;
                    background: #f3f4f6;
                    border-radius: 10px;
                    color: #2563eb;
                ">
                    {otp}
                </div>

                <p>
                    This OTP will expire in <strong>5 minutes</strong>.
                </p>

                <p>
                    If you did not request this verification,
                    you can safely ignore this email.
                </p>

                <p>
                    Regards,<br>
                    <strong>MissingLink AI Team</strong>
                </p>

            </div>
        """
    )
# Upload folders
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["ID_CARD_FOLDER"] = "static/id_cards"

# Create folders if they don't exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["ID_CARD_FOLDER"], exist_ok=True)

# Database
db.init_app(app)

with app.app_context():
    db.create_all()

# ==========================================
# Home
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# Report Missing
# ==========================================

# ==========================================
# Report Missing
# ==========================================

@app.route("/report-missing", methods=["GET", "POST"])
def report_missing():

    if request.method == "POST":

        # ==========================================
        # Validate Last Seen Date
        # ==========================================

        last_seen_date_str = request.form.get("last_seen_date")

        if not last_seen_date_str:
            return render_template(
                "report_missing.html",
                face_error="Please enter the last seen date."
            )

        try:

            last_seen_date = datetime.strptime(
                last_seen_date_str,
                "%Y-%m-%d"
            ).date()

            if last_seen_date >= date.today():

                return render_template(
                    "report_missing.html",
                    face_error="Last seen date must be before today's date."
                )

        except ValueError:

            return render_template(
                "report_missing.html",
                face_error="Please enter a valid last seen date."
            )

        # ==========================================
        # Reporter Email
        # ==========================================

        email = request.form.get("email", "").strip()

        if not email:

            return render_template(
                "report_missing.html",
                face_error="Please enter your email address."
            )

        # ==========================================
        # Get Uploaded Photo
        # ==========================================

        photo = request.files.get("photo")

        if not photo or photo.filename == "":

            return render_template(
                "report_missing.html",
                face_error="Please upload a photo."
            )

        # ==========================================
        # Generate Filename
        # ==========================================

        extension = os.path.splitext(photo.filename)[1]

        filename = str(uuid.uuid4()) + extension

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        # ==========================================
        # Temporary Local Save
        # ==========================================

        photo.save(filepath)

        # ==========================================
        # AI Face Detection
        # ==========================================

        success, embedding, message = get_face_embedding(filepath)

        if not success:

            if os.path.exists(filepath):
                os.remove(filepath)

            return render_template(
                "report_missing.html",
                face_error=message
            )

        embedding_json = json.dumps(embedding)

        # ==========================================
        # Upload Image To Supabase
        # ==========================================

        try:

            storage_path = f"missing-person-photos/{filename}"

            with open(filepath, "rb") as image_file:

                supabase.storage.from_(
                    "missing-person-photos"
                ).upload(
                    storage_path,
                    image_file,
                    {
                        "content-type": photo.content_type
                    }
                )

            if os.path.exists(filepath):
                os.remove(filepath)

        except Exception as e:

            if os.path.exists(filepath):
                os.remove(filepath)

            return render_template(
                "report_missing.html",
                face_error=f"Photo upload failed: {str(e)}"
            )

        # ==========================================
        # Generate OTP
        # ==========================================

        otp = generate_otp()

        otp_hash = generate_password_hash(otp)

        otp_expires_at = datetime.utcnow() + timedelta(minutes=5)

        pending_token = secrets.token_urlsafe(32)

        # ==========================================
        # Store Report Data Temporarily
        # ==========================================

        report_data = {

            "name": request.form.get("name"),

            "age": request.form.get("age"),

            "gender": request.form.get("gender"),

            "height": request.form.get("height"),

            "clothing": request.form.get("clothing"),

            "last_seen_location": request.form.get(
                "last_seen_location"
            ),

            "last_seen_date": request.form.get(
                "last_seen_date"
            ),

            "description": request.form.get(
                "description"
            ),

            "reporter_name": request.form.get(
                "reporter_name"
            ),

            "relationship": request.form.get(
                "relationship"
            ),

            "phone": request.form.get(
                "phone"
            ),

            "email": email
        }

        pending_report = PendingReport(

            token=pending_token,

            report_type="missing",

            report_data=json.dumps(report_data),

            photo_path=storage_path,

            embedding=embedding_json,

            email=email,

            otp_hash=otp_hash,

            otp_expires_at=otp_expires_at,

            otp_attempts=0
        )

        db.session.add(pending_report)

        db.session.commit()

        # ==========================================
        # Send OTP
        # ==========================================

        email_sent = send_otp_email(
            to_email=email,
            to_name=request.form.get("reporter_name"),
            otp=otp
        )

        if not email_sent:

            db.session.delete(pending_report)

            db.session.commit()

            # Remove uploaded Supabase image
            try:

                supabase.storage.from_(
                    "missing-person-photos"
                ).remove([storage_path])

            except Exception as cleanup_error:

                print(
                    "SUPABASE CLEANUP ERROR:",
                    cleanup_error
                )

            return render_template(
                "report_missing.html",
                face_error=(
                    "Unable to send verification email. "
                    "Please try again."
                )
            )

        # ==========================================
        # Store Pending Token In Session
        # ==========================================

        session["pending_report_token"] = pending_token

        # ==========================================
        # Redirect To OTP Verification
        # ==========================================

        return redirect(
            url_for("verify_report_otp")
        )

    return render_template("report_missing.html")
# ==========================================
# Verify Report OTP
# ==========================================

@app.route("/verify-report-otp", methods=["GET", "POST"])
def verify_report_otp():

    token = session.get("pending_report_token")

    if not token:

        flash(
            "Your verification session has expired. Please submit the report again.",
            "danger"
        )

        return redirect(
            url_for("report_missing")
        )

    pending_report = PendingReport.query.filter_by(
        token=token
    ).first()

    if not pending_report:

        session.pop(
            "pending_report_token",
            None
        )

        flash(
            "Verification request not found. Please submit the report again.",
            "danger"
        )

        return redirect(
            url_for("report_missing")
        )

    # ==========================================
    # GET - Show OTP Page
    # ==========================================

    if request.method == "GET":

        return render_template(
            "verify_otp.html",
            email=pending_report.email
        )

    # ==========================================
    # POST - Verify OTP
    # ==========================================

    otp = request.form.get(
        "otp",
        ""
    ).strip()

    if not otp or len(otp) != 6 or not otp.isdigit():

        return render_template(
            "verify_otp.html",
            email=pending_report.email,
            otp_error="Please enter the 6-digit OTP."
        )

    # ==========================================
    # Check OTP Expiry
    # ==========================================

    if datetime.utcnow() > pending_report.otp_expires_at:

        db.session.delete(
            pending_report
        )

        db.session.commit()

        session.pop(
            "pending_report_token",
            None
        )

        return render_template(
            "verify_otp.html",
            email=pending_report.email,
            otp_error=(
                "This OTP has expired. "
                "Please submit the report again."
            )
        )

    # ==========================================
    # Check OTP Attempts
    # ==========================================

    if pending_report.otp_attempts >= 5:

        db.session.delete(
            pending_report
        )

        db.session.commit()

        session.pop(
            "pending_report_token",
            None
        )

        return render_template(
            "verify_otp.html",
            email=pending_report.email,
            otp_error=(
                "Too many incorrect attempts. "
                "Please submit the report again."
            )
        )

    # ==========================================
    # Verify OTP
    # ==========================================

    if not check_password_hash(
        pending_report.otp_hash,
        otp
    ):

        pending_report.otp_attempts += 1

        db.session.commit()

        remaining = (
            5 - pending_report.otp_attempts
        )

        return render_template(
            "verify_otp.html",
            email=pending_report.email,
            otp_error=(
                f"Incorrect OTP. "
                f"{remaining} attempts remaining."
            )
        )

    # ==========================================
    # OTP VERIFIED
    # ==========================================

    report_data = json.loads(
        pending_report.report_data
    )

    # ==========================================
    # MISSING REPORT
    # ==========================================

    if pending_report.report_type == "missing":

        # Generate permanent report ID
        report_id = (
            f"ML-{str(uuid.uuid4())[:8].upper()}"
        )

        person = MissingPerson(

            # Report Tracking
            report_id=report_id,
            status="submitted",

            # Missing Person Details
            name=report_data.get(
                "name"
            ),

            age=report_data.get(
                "age"
            ),

            gender=report_data.get(
                "gender"
            ),

            height=report_data.get(
                "height"
            ),

            clothing=report_data.get(
                "clothing"
            ),

            last_seen_location=report_data.get(
                "last_seen_location"
            ),

            last_seen_date=report_data.get(
                "last_seen_date"
            ),

            description=report_data.get(
                "description"
            ),

            # AI + Photo
            photo_path=pending_report.photo_path,

            embedding=pending_report.embedding,

            # Reporter Details
            reporter_name=report_data.get(
                "reporter_name"
            ),

            relationship=report_data.get(
                "relationship"
            ),

            phone=report_data.get(
                "phone"
            ),

            email=report_data.get(
                "email"
            )
        )

        db.session.add(
            person
        )

    # ==========================================
    # FOUND REPORT
    # ==========================================

    elif pending_report.report_type == "found":

        # Generate permanent report ID
        report_id = (
            f"ML-{str(uuid.uuid4())[:8].upper()}"
        )

        found_person = FoundPerson(

            # Report Tracking
            report_id=report_id,
            status="submitted",

            # Found Person Details
            estimated_age=report_data.get(
                "estimated_age"
            ),

            gender=report_data.get(
                "gender"
            ),

            height=report_data.get(
                "height"
            ),

            clothing=report_data.get(
                "clothing"
            ),

            found_location=report_data.get(
                "found_location"
            ),

            found_date=report_data.get(
                "found_date"
            ),

            found_time=report_data.get(
                "found_time"
            ),

            condition=report_data.get(
                "condition"
            ),

            description=report_data.get(
                "description"
            ),

            # AI + Photo
            embedding=pending_report.embedding,

            photo_path=pending_report.photo_path,

            # Finder Details
            finder_name=report_data.get(
                "finder_name"
            ),

            phone=report_data.get(
                "phone"
            ),

            email=report_data.get(
                "email"
            ),

            organization=report_data.get(
                "organization"
            ),

            police_station=report_data.get(
                "police_station"
            )
        )

        db.session.add(
            found_person
        )

    # ==========================================
    # INVALID REPORT TYPE
    # ==========================================

    else:

        db.session.rollback()

        session.pop(
            "pending_report_token",
            None
        )

        return render_template(
            "verify_otp.html",
            email=pending_report.email,
            otp_error="Invalid report type."
        )

    # ==========================================
    # Delete Temporary Report
    # ==========================================

    db.session.delete(
        pending_report
    )

    session.pop(
        "pending_report_token",
        None
    )

    # ==========================================
    # Save Report
    # ==========================================

    db.session.commit()

    # ==========================================
    # SUCCESS
    # ==========================================

    return render_template(
        "success.html",
        report_id=report_id
    )
@app.route("/ai-match/<int:found_id>")
def ai_match(found_id):

    found_person = FoundPerson.query.get_or_404(found_id)

    missing_people = MissingPerson.query.all()

    matches = find_best_matches(
        found_person,
        missing_people
    )

    # ==========================================
    # FOUND PERSON IMAGE
    # ==========================================

    found_person.photo_url = None

    if found_person.photo_path:

        try:

            response = supabase.storage.from_(
                "found-person-photos"
            ).create_signed_url(
                found_person.photo_path,
                3600
            )

            print("FOUND SUPABASE RESPONSE:", response)

            if isinstance(response, dict):

                found_person.photo_url = (
                    response.get("signedURL")
                    or response.get("signedUrl")
                )

        except Exception as e:

            print("FOUND PHOTO ERROR:", e)

    # ==========================================
    # MATCHING PERSON IMAGES
    # ==========================================

    for match in matches[:5]:

        person = match["person"]

        person.photo_url = None

        if person.photo_path:

            try:

                response = supabase.storage.from_(
                    "missing-person-photos"
                ).create_signed_url(
                    person.photo_path,
                    3600
                )

                print(
                    "MISSING SUPABASE RESPONSE:",
                    response
                )

                if isinstance(response, dict):

                    person.photo_url = (
                        response.get("signedURL")
                        or response.get("signedUrl")
                    )

            except Exception as e:

                print(
                    "MISSING PHOTO ERROR:",
                    e
                )

    return render_template(
        "ai_result.html",
        found_person=found_person,
        matches=matches[:5]
    )
@app.route("/missing/<int:id>")
def view_missing_profile(id):

    person = MissingPerson.query.get_or_404(id)

    # ==========================================
    # Generate Supabase Signed URL
    # ==========================================

    person.photo_url = None

    if person.photo_path:

        try:

            response = supabase.storage.from_(
                "missing-person-photos"
            ).create_signed_url(
                person.photo_path,
                3600
            )

            print("PROFILE PHOTO RESPONSE:", response)

            if isinstance(response, dict):

                person.photo_url = (
                    response.get("signedURL")
                    or response.get("signedUrl")
                )

        except Exception as e:

            print("PROFILE PHOTO ERROR:", e)

    return render_template(
        "missing_profile.html",
        person=person
    )
# ==========================================
# Report Found
# ==========================================

# ==========================================
# Report Found
# ==========================================

@app.route("/report-found", methods=["GET", "POST"])
def report_found():

    if request.method == "POST":

        # ==========================================
        # Validate Found Date
        # ==========================================

        found_date_str = request.form.get("found_date")

        if not found_date_str:
            return render_template(
                "report_found.html",
                face_error="Please enter the found date."
            )

        try:
            found_date = datetime.strptime(
                found_date_str,
                "%Y-%m-%d"
            ).date()

            if found_date >= date.today():
                return render_template(
                    "report_found.html",
                    face_error="Found date must be before today's date."
                )

        except ValueError:
            return render_template(
                "report_found.html",
                face_error="Please enter a valid found date."
            )

        # ==========================================
        # Finder Email
        # ==========================================

        email = request.form.get("email", "").strip()

        if not email:
            return render_template(
                "report_found.html",
                face_error="Please enter your email address."
            )

        # ==========================================
        # Get Uploaded Photo
        # ==========================================

        photo = request.files.get("photo")

        if not photo or photo.filename == "":
            return render_template(
                "report_found.html",
                face_error="Please upload a photo."
            )

        # ==========================================
        # Generate Filename
        # ==========================================

        extension = os.path.splitext(photo.filename)[1].lower()

        if extension not in [".jpg", ".jpeg", ".png", ".webp"]:
            return render_template(
                "report_found.html",
                face_error="Please upload a valid image file."
            )

        filename = str(uuid.uuid4()) + extension

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        # ==========================================
        # Save Photo Temporarily
        # ==========================================

        try:
            photo.save(filepath)

        except Exception as e:
            return render_template(
                "report_found.html",
                face_error=f"Unable to process photo: {str(e)}"
            )

        # ==========================================
        # AI FACE DETECTION + EMBEDDING
        # ==========================================

        success, embedding, message = get_face_embedding(filepath)

        if not success:

            if os.path.exists(filepath):
                os.remove(filepath)

            return render_template(
                "report_found.html",
                face_error=message
            )

        embedding_json = json.dumps(embedding)

        # ==========================================
        # Upload Photo To Supabase
        # ==========================================

        storage_path = filename

        try:

            with open(filepath, "rb") as image_file:

                supabase.storage.from_(
                    "found-person-photos"
                ).upload(
                    storage_path,
                    image_file,
                    {
                        "content-type": photo.content_type
                    }
                )

            # Remove local temporary file
            if os.path.exists(filepath):
                os.remove(filepath)

        except Exception as e:

            if os.path.exists(filepath):
                os.remove(filepath)

            return render_template(
                "report_found.html",
                face_error=f"Photo upload failed: {str(e)}"
            )

        # ==========================================
        # Generate OTP
        # ==========================================

        otp = generate_otp()

        otp_hash = generate_password_hash(otp)

        otp_expires_at = (
            datetime.utcnow()
            + timedelta(minutes=5)
        )

        pending_token = secrets.token_urlsafe(32)

        # ==========================================
        # Store Report Data
        # ==========================================

        report_data = {

            "estimated_age": request.form.get(
                "estimated_age"
            ),

            "gender": request.form.get(
                "gender"
            ),

            "height": request.form.get(
                "height"
            ),

            "clothing": request.form.get(
                "clothing"
            ),

            "found_location": request.form.get(
                "found_location"
            ),

            "found_date": request.form.get(
                "found_date"
            ),

            "found_time": request.form.get(
                "found_time"
            ),

            "condition": request.form.get(
                "condition"
            ),

            "description": request.form.get(
                "description"
            ),

            "finder_name": request.form.get(
                "finder_name"
            ),

            "phone": request.form.get(
                "phone"
            ),

            "email": email,

            "organization": request.form.get(
                "organization"
            ),

            "police_station": request.form.get(
                "police_station"
            )
        }

        # ==========================================
        # Create Pending Report
        # ==========================================

        pending_report = PendingReport(

            token=pending_token,

            report_type="found",

            report_data=json.dumps(report_data),

            photo_path=storage_path,

            embedding=embedding_json,

            email=email,

            otp_hash=otp_hash,

            otp_expires_at=otp_expires_at,

            otp_attempts=0
        )

        db.session.add(pending_report)

        try:
            db.session.commit()

        except Exception as e:

            db.session.rollback()

            # Cleanup uploaded photo
            try:
                supabase.storage.from_(
                    "found-person-photos"
                ).remove([storage_path])
            except Exception:
                pass

            return render_template(
                "report_found.html",
                face_error=f"Unable to save report: {str(e)}"
            )

        # ==========================================
        # Send OTP
        # ==========================================

        email_sent = send_otp_email(
            to_email=email,
            to_name=request.form.get("finder_name"),
            otp=otp
        )

        # ==========================================
        # Email Failed
        # ==========================================

        if not email_sent:

            db.session.delete(pending_report)
            db.session.commit()

            try:

                supabase.storage.from_(
                    "found-person-photos"
                ).remove([storage_path])

            except Exception as cleanup_error:

                print(
                    "SUPABASE CLEANUP ERROR:",
                    cleanup_error
                )

            return render_template(
                "report_found.html",
                face_error=(
                    "Unable to send verification email. "
                    "Please try again."
                )
            )

        # ==========================================
        # Store Token In Session
        # ==========================================

        session["pending_report_token"] = pending_token

        # ==========================================
        # Redirect To OTP
        # ==========================================

        return redirect(
            url_for("verify_report_otp")
        )

    return render_template(
        "report_found.html"
    )
# ==========================================
# Login
# ==========================================

from werkzeug.security import check_password_hash

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = Organization.query.filter_by(email=email).first()

        # Email not found
        if user is None:

            return render_template(
                "login.html",
                login_error={
                    "title": "Login Failed",
                    "message": "No organization account was found with this email address."
                }
            )

        # Wrong password
        if not check_password_hash(user.password, password):

            return render_template(
                "login.html",
                login_error={
                    "title": "Incorrect Password",
                    "message": "The password you entered is incorrect. Please try again."
                }
            )

        # Account awaiting approval
        if not user.verified:

            return render_template(
                "login.html",
                login_error={
                    "title": "Verification Pending",
                    "message": "Your organization account is awaiting administrator approval."
                }
            )

        session.permanent = True
        session["organization"] = user.id

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ==========================================
# Register Organization
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        organization = request.form["organization"]
        role = request.form["role"]
        full_name = request.form["full_name"]
        government_id = request.form["government_id"]
        email = request.form["email"]
        phone = request.form["phone"]

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # ==========================================
        # Password Match
        # ==========================================

        if password != confirm_password:

            return render_template(
                "register.html",
                popup={
                    "type": "error",
                    "title": "Registration Failed",
                    "message": "Passwords do not match."
                }
            )

        # ==========================================
        # Duplicate Email
        # ==========================================

        existing_email = Organization.query.filter_by(
            email=email
        ).first()

        if existing_email:

            return render_template(
                "register.html",
                popup={
                    "type": "error",
                    "title": "Registration Failed",
                    "message": "Email already registered."
                }
            )

        # ==========================================
        # Duplicate Government ID
        # ==========================================

        existing_id = Organization.query.filter_by(
            government_id=government_id
        ).first()

        if existing_id:

            return render_template(
                "register.html",
                popup={
                    "type": "error",
                    "title": "Registration Failed",
                    "message": "Government ID already registered."
                }
            )

        # ==========================================
        # Upload ID Card
        # ==========================================

        file = request.files.get("id_card")

        if not file or file.filename == "":

            return render_template(
                "register.html",
                popup={
                    "type": "error",
                    "title": "Upload Required",
                    "message": "Please upload your identity card."
                }
            )

        filename = (
            str(uuid.uuid4())
            + "_"
            + secure_filename(file.filename)
        )

        # ==========================================
        # Temporary Local File
        # ==========================================

        temp_filepath = os.path.join(
            app.config["ID_CARD_FOLDER"],
            filename
        )

        file.save(temp_filepath)

        # ==========================================
        # Upload ID Card to Supabase
        # ==========================================

        try:

            storage_path = f"organization-documents/{filename}"

            with open(temp_filepath, "rb") as id_file:

                supabase.storage.from_(
                    "organization-documents"
                ).upload(
                    storage_path,
                    id_file,
                    {
                        "content-type": file.content_type
                    }
                )

            # Delete temporary file
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

        except Exception as e:

            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

            return render_template(
                "register.html",
                popup={
                    "type": "error",
                    "title": "Upload Failed",
                    "message": f"Identity document upload failed: {str(e)}"
                }
            )

        # ==========================================
        # Create Organization
        # ==========================================

        organization_data = Organization(

            organization=organization,

            role=role,

            full_name=full_name,

            government_id=government_id,

            email=email,

            phone=phone,

            password=generate_password_hash(password),

            id_card=storage_path,

            email_verified=False,

            verified=False
        )

        db.session.add(organization_data)

        db.session.commit()

        # ==========================================
        # Generate Email Verification Token
        # ==========================================

        token = serializer.dumps(
            organization_data.email
        )

        organization_data.email_verification_token = token

        db.session.commit()

        # ==========================================
        # Registration Success
        # ==========================================

        return render_template(
            "register.html",
            popup={
                "type": "warning",
                "title": "Registration Submitted",
                "message": "Your organization has been registered successfully and is awaiting administrator approval."
            }
        )

    # ==========================================
    # GET Request
    # ==========================================

    return render_template("register.html")

# ==========================================
# Dashboard
# ==========================================
# ==========================================
# Admin Login
# ==========================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")

        if not admin_username or not admin_password_hash:
            app.logger.error("Admin credentials are not configured.")
            flash("Admin login is temporarily unavailable.", "danger")
            return render_template("admin_login.html")

        if (
            username == admin_username
            and check_password_hash(admin_password_hash, password)
        ):
            session.permanent = True
            session["admin"] = True

            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials.", "danger")

    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    pending = Organization.query.filter_by(
        verified=False
    ).all()

    verified = Organization.query.filter_by(
        verified=True
    ).all()

    # Generate temporary signed URLs for ID cards
    for org in pending:

        org.id_card_url = None

        if org.id_card:

            try:

                signed_response = supabase.storage.from_(
                    "organization-documents"
                ).create_signed_url(
                    org.id_card,
                    3600
                )

                # Supabase response handling
                if isinstance(signed_response, dict):

                    org.id_card_url = (
                        signed_response.get("signedURL")
                        or signed_response.get("signedUrl")
                    )

            except Exception as e:

                print(
                    f"ID card URL error for organization {org.id}: {e}"
                )

    return render_template(
        "admin_dashboard.html",

        pending=pending,

        verified=verified,

        pending_count=len(pending),

        verified_count=len(verified),

        missing_count=MissingPerson.query.count(),

        found_count=FoundPerson.query.count()
    )
@app.route("/admin/approve/<int:id>")
def approve_org(id):

    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    org = Organization.query.get_or_404(id)
    org.verified = True
    db.session.commit()
    # Approve organization
    # Send approval email
    email_sent = send_email(
        to_email=org.email,
        to_name=org.full_name,
        subject="MissingLink AI - Organization Approved",
        html_content=f"""
            <h2>MissingLink AI</h2>

            <p>Hello {org.full_name},</p>

            <p>
                We are pleased to inform you that your organization
                registration with MissingLink AI has been approved.
            </p>

            <p>
                <strong>Organization:</strong> {org.organization}
            </p>

            <p>
                You can now log in to your MissingLink AI account
                and access the features available to verified
                organizations.
            </p>

            <p>
                Thank you for joining MissingLink AI.
            </p>

            <p>
                Regards,<br>
                MissingLink AI Team
            </p>
        """
    )

    if not email_sent:
        flash(
            "Organization approved, but approval email could not be sent.",
            "warning"
        )
    else:
        flash(
            "Organization approved successfully and approval email sent.",
            "success"
        )

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reject/<int:id>")
def reject_org(id):

    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    org = Organization.query.get_or_404(id)

    # Store details before deleting the organization
    organization_name = org.organization
    full_name = org.full_name
    email = org.email

    # Delete organization
    db.session.delete(org)
    db.session.commit()

    # Send rejection email
    email_sent = send_email(
        to_email=email,
        to_name=full_name,
        subject="MissingLink AI - Organization Registration Update",
        html_content=f"""
            <h2>MissingLink AI</h2>

            <p>Hello {full_name},</p>

            <p>
                Thank you for registering your organization
                with MissingLink AI.
            </p>

            <p>
                After reviewing your registration and submitted
                information, we regret to inform you that your
                organization registration could not be approved
                at this time.
            </p>

            <p>
                <strong>Organization:</strong> {organization_name}
            </p>

            <p>
                If you believe this decision was made in error
                or would like further clarification, please
                contact the MissingLink AI administration team.
            </p>

            <p>
                Regards,<br>
                MissingLink AI Team
            </p>
        """
    )

    if not email_sent:
        flash(
            "Organization rejected, but rejection email could not be sent.",
            "warning"
        )
    else:
        flash(
            "Organization rejected and rejection email sent.",
            "warning"
        )

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/logout")
def admin_logout():
    session.clear()

    response = redirect(url_for("admin_login"))

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response
@app.route("/logout")
def logout():

    session.clear()

    response = redirect(url_for("login"))

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, "
        "post-check=0, pre-check=0, max-age=0"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

@app.route("/dashboard")
def dashboard():

    if not session.get("organization"):
        return redirect(url_for("login"))

    missing_people = MissingPerson.query.order_by(
        MissingPerson.created_at.desc()
    ).all()

    found_people = FoundPerson.query.order_by(
        FoundPerson.created_at.desc()
    ).all()

    # ==========================================
    # Generate Signed URLs for Missing Photos
    # ==========================================

    for person in missing_people:

        person.photo_url = None

        if person.photo_path:

            try:

                signed_response = supabase.storage.from_(
                    "missing-person-photos"
                ).create_signed_url(
                    person.photo_path,
                    3600
                )

                if isinstance(signed_response, dict):

                    person.photo_url = (
                        signed_response.get("signedURL")
                        or signed_response.get("signedUrl")
                    )

            except Exception as e:

                print(
                    f"Missing photo URL error for {person.id}: {e}"
                )

    # ==========================================
    # Generate Signed URLs for Found Photos
    # ==========================================

    for person in found_people:

        person.photo_url = None

        if person.photo_path:

            try:

                signed_response = supabase.storage.from_(
                    "found-person-photos"
                ).create_signed_url(
                    person.photo_path,
                    3600
                )

                if isinstance(signed_response, dict):

                    person.photo_url = (
                        signed_response.get("signedURL")
                        or signed_response.get("signedUrl")
                    )

            except Exception as e:

                print(
                    f"Found photo URL error for {person.id}: {e}"
                )

    # ==========================================
    # Dashboard
    # ==========================================

    missing_count = MissingPerson.query.count()

    found_count = FoundPerson.query.count()

    return render_template(

        "dashboard.html",

        missing_people=missing_people,

        found_people=found_people,

        missing_count=missing_count,

        found_count=found_count

    )
# ==========================================
# UPDATE REPORT STATUS
# ==========================================

@app.route("/update-report-status", methods=["POST"])
def update_report_status():

    # ==========================================
    # ORGANIZATION LOGIN CHECK
    # ==========================================

    if not session.get("organization"):

        return {
            "success": False,
            "message": "Authentication required."
        }, 401

    # ==========================================
    # GET REQUEST DATA
    # ==========================================

    data = request.get_json(silent=True) or request.form

    report_id = data.get(
        "report_id",
        ""
    ).strip()

    new_status = data.get(
        "status",
        ""
    ).strip()

    report_type = data.get(
        "report_type",
        ""
    ).strip()

    # ==========================================
    # VALIDATE REPORT ID
    # ==========================================

    if not report_id:

        return {
            "success": False,
            "message": "Report ID is required."
        }, 400

    # ==========================================
    # ALLOWED STATUSES
    # ==========================================

    allowed_statuses = {
        "submitted",
        "investigating",
        "potential_match",
        "found"
    }

    if new_status not in allowed_statuses:

        return {
            "success": False,
            "message": "Invalid report status."
        }, 400

    # ==========================================
    # FIND REPORT
    # ==========================================

    report = None

    if report_type == "missing":

        report = MissingPerson.query.filter_by(
            report_id=report_id
        ).first()

    elif report_type == "found":

        report = FoundPerson.query.filter_by(
            report_id=report_id
        ).first()

    else:

        # Fallback search if report_type wasn't supplied

        report = MissingPerson.query.filter_by(
            report_id=report_id
        ).first()

        if not report:

            report = FoundPerson.query.filter_by(
                report_id=report_id
            ).first()

    # ==========================================
    # REPORT NOT FOUND
    # ==========================================

    if not report:

        return {
            "success": False,
            "message": "Report not found."
        }, 404

    # ==========================================
    # UPDATE STATUS
    # ==========================================

    report.status = new_status

    # ==========================================
    # SAVE
    # ==========================================

    try:

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "STATUS UPDATE ERROR:",
            e
        )

        return {
            "success": False,
            "message": "Unable to update report status."
        }, 500

    # ==========================================
    # SUCCESS
    # ==========================================

    return {
        "success": True,
        "message": "Report status updated successfully.",
        "report_id": report_id,
        "status": new_status
    }, 200
# ==========================================
# REPORT STATUS TRACKING
# ==========================================

@app.route("/track-report", methods=["GET", "POST"])
def track_report():

    report = None
    report_type = None
    error = None

    if request.method == "POST":

        report_id = request.form.get(
            "report_id",
            ""
        ).strip().upper()

        if not report_id:

            error = "Please enter your Report ID."

        else:

            # Search missing reports
            report = MissingPerson.query.filter_by(
                report_id=report_id
            ).first()

            if report:

                report_type = "missing"

            else:

                # Search found reports
                report = FoundPerson.query.filter_by(
                    report_id=report_id
                ).first()

                if report:
                    report_type = "found"

            if not report:

                error = (
                    "No report was found with this Report ID. "
                    "Please check the ID and try again."
                )

    return render_template(
        "track_report.html",
        report=report,
        report_type=report_type,
        error=error
    )
@app.route("/admin/clear-data")
def clear_data():

    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    try:

        # ==========================================
        # DELETE DATABASE RECORDS
        # ==========================================

        MissingPerson.query.delete()
        FoundPerson.query.delete()
        Organization.query.delete()
        PendingReport.query.delete()
        db.session.commit()

        # ==========================================
        # DELETE MISSING PERSON PHOTOS
        # ==========================================

        try:

            bucket = supabase.storage.from_(
                "missing-person-photos"
            )

            files = bucket.list(
                "missing-person-photos"
            )

            if files:

                paths = [
                    "missing-person-photos/" + file["name"]
                    for file in files
                    if file.get("name")
                ]

                if paths:
                    bucket.remove(paths)

                print("Missing person photos deleted.")

        except Exception as e:

            print(
                "Missing photos cleanup error:",
                e
            )

        # ==========================================
        # DELETE FOUND PERSON PHOTOS
        # ==========================================

        try:

            bucket = supabase.storage.from_(
                "found-person-photos"
            )

            files = bucket.list(
                "found-person-photos"
            )

            if files:

                paths = [
                    "found-person-photos/" + file["name"]
                    for file in files
                    if file.get("name")
                ]

                if paths:
                    bucket.remove(paths)

                print("Found person photos deleted.")

        except Exception as e:

            print(
                "Found photos cleanup error:",
                e
            )

        # ==========================================
        # DELETE ORGANIZATION ID CARDS
        # ==========================================

        try:

            bucket = supabase.storage.from_(
                "organization-documents"
            )

            files = bucket.list(
                "organization-documents"
            )

            if files:

                paths = [
                    "organization-documents/" + file["name"]
                    for file in files
                    if file.get("name")
                ]

                if paths:
                    bucket.remove(paths)

                print("Organization documents deleted.")

        except Exception as e:

            print(
                "Organization documents cleanup error:",
                e
            )

        return """
        <h2>All test data cleared successfully.</h2>
        <p>Database records and Supabase files have been deleted.</p>
        <a href="/admin/dashboard">
            Back to Admin Dashboard
        </a>
        """

    except Exception as e:

        db.session.rollback()

        return f"""
        <h2>Error clearing data</h2>
        <p>{str(e)}</p>
        """

# ==========================================
# Run App
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)