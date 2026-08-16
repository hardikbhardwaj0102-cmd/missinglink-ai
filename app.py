import os
import uuid
from itsdangerous import URLSafeSerializer
from ai.face_service import get_face_embedding
import json
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from flask import session
from ai.face_matcher import find_best_matches
from flask_mail import Mail, Message
from dotenv import load_dotenv
from supabase import create_client, Client
load_dotenv()
from config import Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
from models import (
    db,
    MissingPerson,
    FoundPerson,
    Organization
)

# ==========================================
# Flask App
# ==========================================

app = Flask(__name__)

app.config.from_object(Config)

mail = Mail(app)
serializer = URLSafeSerializer(app.config["SECRET_KEY"])
@app.route("/test-email")
def test_email():

    try:
        msg = Message(
            subject="MissingLink AI - Email Test",
            sender=app.config["MAIL_USERNAME"],
            recipients=["missinglinkai0@gmail.com"]
        )

        msg.body = """
Hello,

This is a test email from MissingLink AI.

If you received this email, the Flask email system is working correctly.

MissingLink AI
"""

        mail.send(msg)

        return "EMAIL SENT SUCCESSFULLY"

    except Exception as e:
        return f"EMAIL ERROR: {str(e)}"


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

@app.route("/report-missing", methods=["GET", "POST"])
def report_missing():

    if request.method == "POST":

        # -----------------------------
        # Validate last seen date
        # -----------------------------

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

            # Last seen date must be before today
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

        # -----------------------------
        # Get uploaded photo
        # -----------------------------

        photo = request.files.get("photo")

        # -----------------------------
        # Validate photo
        # -----------------------------

        if not photo or photo.filename == "":
            return render_template(
                "report_missing.html",
                face_error="Please upload a photo."
            )

        extension = os.path.splitext(photo.filename)[1]
        filename = str(uuid.uuid4()) + extension

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        # -----------------------------
        # Temporary local save
        # -----------------------------

        photo.save(filepath)

        # -----------------------------
        # AI Face Detection
        # -----------------------------

        success, embedding, message = get_face_embedding(filepath)

        if not success:

            if os.path.exists(filepath):
                os.remove(filepath)

            return render_template(
                "report_missing.html",
                face_error=message
            )

        # -----------------------------
        # Convert embedding
        # -----------------------------

        embedding_json = json.dumps(embedding)

        # -----------------------------
        # Upload image to Supabase
        # -----------------------------

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

            # Remove temporary local file
            if os.path.exists(filepath):
                os.remove(filepath)

        except Exception as e:

            if os.path.exists(filepath):
                os.remove(filepath)

            return render_template(
                "report_missing.html",
                face_error=f"Photo upload failed: {str(e)}"
            )

        # -----------------------------
        # Save database record
        # -----------------------------

        report_id = f"ML-{str(uuid.uuid4())[:8].upper()}"

        person = MissingPerson(

            name=request.form.get("name"),

            age=request.form.get("age"),

            gender=request.form.get("gender"),

            height=request.form.get("height"),

            clothing=request.form.get("clothing"),

            last_seen_location=request.form.get(
                "last_seen_location"
            ),

            last_seen_date=request.form.get(
                "last_seen_date"
            ),

            description=request.form.get(
                "description"
            ),

            photo_path=storage_path,

            embedding=embedding_json,

            reporter_name=request.form.get(
                "reporter_name"
            ),

            relationship=request.form.get(
                "relationship"
            ),

            phone=request.form.get("phone"),

            email=request.form.get("email")
        )

        db.session.add(person)

        db.session.commit()

        return render_template(
            "success.html",
            report_id=report_id
        )

    return render_template("report_missing.html")
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

@app.route("/report-found", methods=["GET", "POST"])
def report_found():

    if request.method == "POST":

        # -----------------------------
        # Validate found date
        # -----------------------------

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

            # Found date must be before today
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

        # -----------------------------
        # Get uploaded photo
        # -----------------------------

        photo = request.files.get("photo")

        filename = ""
        storage_path = ""
        embedding_json = None

        # -----------------------------
        # Photo + AI Processing
        # -----------------------------

        if photo and photo.filename != "":

            extension = os.path.splitext(photo.filename)[1]

            filename = str(uuid.uuid4()) + extension

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            # Temporary local save
            photo.save(filepath)

            # -----------------------------
            # AI Face Detection
            # -----------------------------

            success, embedding, message = get_face_embedding(filepath)

            if not success:

                if os.path.exists(filepath):
                    os.remove(filepath)

                return render_template(
                    "report_found.html",
                    face_error=message
                )

            embedding_json = json.dumps(embedding)

            # -----------------------------
            # Upload to Supabase
            # -----------------------------

            try:

                storage_path = f"found-person-photos/{filename}"

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

                # Delete temporary local file
                if os.path.exists(filepath):
                    os.remove(filepath)

            except Exception as e:

                if os.path.exists(filepath):
                    os.remove(filepath)

                return render_template(
                    "report_found.html",
                    face_error=f"Photo upload failed: {str(e)}"
                )

        # -----------------------------
        # Save Found Person
        # -----------------------------

        found_person = FoundPerson(

            estimated_age=request.form.get(
                "estimated_age"
            ),

            gender=request.form.get(
                "gender"
            ),

            height=request.form.get(
                "height"
            ),

            clothing=request.form.get(
                "clothing"
            ),

            found_location=request.form.get(
                "found_location"
            ),

            found_date=request.form.get(
                "found_date"
            ),

            found_time=request.form.get(
                "found_time"
            ),

            condition=request.form.get(
                "condition"
            ),

            description=request.form.get(
                "description"
            ),

            embedding=embedding_json,

            photo_path=storage_path,

            finder_name=request.form.get(
                "finder_name"
            ),

            phone=request.form.get(
                "phone"
            ),

            email=request.form.get(
                "email"
            ),

            organization=request.form.get(
                "organization"
            ),

            police_station=request.form.get(
                "police_station"
            )
        )

        db.session.add(found_person)
        db.session.commit()

        # -----------------------------
        # Generate Report ID
        # -----------------------------

        report_id = f"ML-F-{found_person.id:06d}"

        # -----------------------------
        # Success Page
        # -----------------------------

        return render_template(
            "success.html",
            report_id=report_id
        )

    return render_template("report_found.html")
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

        username = request.form["username"]
        password = request.form["password"]

        if username == "Hardik" and password == "Hardik@123":

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

    # Approve organization
    org.verified = True

    db.session.commit()

    # Send approval email
    msg = Message(
        subject="MissingLink AI - Organization Approved",
        sender=app.config["MAIL_USERNAME"],
        recipients=[org.email]
    )

    msg.body = f"""
Hello {org.full_name},

We are pleased to inform you that your organization registration
with MissingLink AI has been approved.

Organization: {org.organization}

You can now log in to your MissingLink AI account and access
the features available to verified organizations.

Thank you for joining MissingLink AI.

Regards,
MissingLink AI Team
"""

    mail.send(msg)

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
    msg = Message(
        subject="MissingLink AI - Organization Registration Update",
        sender=app.config["MAIL_USERNAME"],
        recipients=[email]
    )

    msg.body = f"""
Hello {full_name},

Thank you for registering your organization with MissingLink AI.

After reviewing your registration and submitted information,
we regret to inform you that your organization registration
could not be approved at this time.

Organization: {organization_name}

If you believe this decision was made in error or would like
further clarification, please contact the MissingLink AI
administration team.

Regards,
MissingLink AI Team
"""

    mail.send(msg)

    flash(
        "Organization rejected and rejection email sent.",
        "warning"
    )

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect(url_for("admin_login"))
@app.route("/logout")
def logout():
    session.pop("organization", None)
    return redirect(url_for("login"))

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