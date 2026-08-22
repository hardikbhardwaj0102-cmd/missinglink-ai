# ============================================================
# MissingLink AI
# Complete REST API Layer
# ============================================================

import os
import json
import uuid
import secrets

from datetime import datetime, date, timedelta
from functools import wraps
from io import BytesIO

from flask import (
    Blueprint,
    request,
    jsonify,
    send_file,
    current_app
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from models import (
    db,
    MissingPerson,
    FoundPerson,
    Organization,
    PendingReport
)

from ai.face_service import get_face_embedding
from ai.face_matcher import find_best_matches


# ============================================================
# API BLUEPRINT
# ============================================================

api = Blueprint(
    "api",
    __name__,
    url_prefix="/api"
)


# ============================================================
# API CONFIGURATION
# ============================================================

API_KEY = os.getenv(
    "MISSINGLINK_API_KEY"
)

ADMIN_API_KEY = os.getenv(
    "MISSINGLINK_ADMIN_API_KEY"
)


# ============================================================
# API AUTHENTICATION
# ============================================================

def api_key_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        provided_key = request.headers.get(
            "X-API-Key"
        )

        if not API_KEY:

            return jsonify({
                "success": False,
                "message": (
                    "API authentication is not configured."
                )
            }), 500

        if not provided_key:

            return jsonify({
                "success": False,
                "message": "API key is required."
            }), 401

        if provided_key != API_KEY:

            return jsonify({
                "success": False,
                "message": "Invalid API key."
            }), 401

        return function(
            *args,
            **kwargs
        )

    return decorated


# ============================================================
# ADMIN API AUTHENTICATION
# ============================================================

def admin_api_key_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        provided_key = request.headers.get(
            "X-Admin-API-Key"
        )

        if not ADMIN_API_KEY:

            return jsonify({
                "success": False,
                "message": (
                    "Admin API authentication "
                    "is not configured."
                )
            }), 500

        if provided_key != ADMIN_API_KEY:

            return jsonify({
                "success": False,
                "message": "Invalid admin API key."
            }), 401

        return function(
            *args,
            **kwargs
        )

    return decorated


# ============================================================
# HELPERS
# ============================================================

def get_supabase():

    # Import here to avoid circular imports.
    #
    # Your existing app already creates the Supabase client.
    #
    from app import supabase

    return supabase


def get_email_functions():

    # Import existing email functions from your app.
    #
    # Your current application already uses send_email()
    # and send_otp_email().
    #
    from app import (
        send_email,
        send_otp_email
    )

    return send_email, send_otp_email


def get_otp_generator():

    from app import generate_otp

    return generate_otp


def safe_date(value):

    if value is None:
        return None

    return str(value)


def safe_datetime(value):

    if value is None:
        return None

    if hasattr(value, "isoformat"):

        return value.isoformat()

    return str(value)


def normalize_report_id(report_id):

    return (
        report_id
        .strip()
        .upper()
    )


def get_photo_url(
    bucket_name,
    photo_path,
    expires=3600
):

    if not photo_path:
        return None

    try:

        supabase = get_supabase()

        clean_path = photo_path

        prefix = bucket_name + "/"

        if clean_path.startswith(prefix):

            clean_path = clean_path[
                len(prefix):
            ]

        response = (
            supabase.storage
            .from_(bucket_name)
            .create_signed_url(
                clean_path,
                expires
            )
        )

        if isinstance(response, dict):

            return (
                response.get("signedURL")
                or
                response.get("signedUrl")
            )

    except Exception as e:

        print(
            "API PHOTO URL ERROR:",
            e
        )

    return None


def validate_coordinates(
    latitude,
    longitude
):

    if latitude in (
        None,
        "",
    ) and longitude in (
        None,
        "",
    ):

        return (
            True,
            None,
            None,
            None
        )

    if (
        latitude in (None, "")
        or
        longitude in (None, "")
    ):

        return (
            False,
            None,
            None,
            "Both latitude and longitude are required."
        )

    try:

        latitude = float(latitude)
        longitude = float(longitude)

    except (
        TypeError,
        ValueError
    ):

        return (
            False,
            None,
            None,
            "Invalid location coordinates."
        )

    if not -90 <= latitude <= 90:

        return (
            False,
            None,
            None,
            "Latitude must be between -90 and 90."
        )

    if not -180 <= longitude <= 180:

        return (
            False,
            None,
            None,
            "Longitude must be between -180 and 180."
        )

    return (
        True,
        latitude,
        longitude,
        None
    )


# ============================================================
# SERIALIZERS
# ============================================================

def serialize_missing(
    person,
    include_private=False
):

    data = {

        "id":
            person.id,

        "report_id":
            person.report_id,

        "type":
            "missing",

        "name":
            person.name,

        "age":
            person.age,

        "gender":
            person.gender,

        "height":
            person.height,

        "clothing":
            person.clothing,

        "description":
            person.description,

        "last_seen_location":
            person.last_seen_location,

        "last_seen_date":
            safe_date(
                person.last_seen_date
            ),

        "latitude":
            getattr(
                person,
                "last_seen_latitude",
                None
            ),

        "longitude":
            getattr(
                person,
                "last_seen_longitude",
                None
            ),

        "status":
            person.status,

        "photo_path":
            person.photo_path,

        "photo_url":
            get_photo_url(
                "missing-person-photos",
                person.photo_path
            ),

        "created_at":
            safe_datetime(
                person.created_at
            )

    }

    if include_private:

        data.update({

            "reporter_name":
                person.reporter_name,

            "relationship":
                person.relationship,

            "phone":
                person.phone,

            "email":
                person.email

        })

    return data


def serialize_found(
    person,
    include_private=False
):

    data = {

        "id":
            person.id,

        "report_id":
            person.report_id,

        "type":
            "found",

        "estimated_age":
            person.estimated_age,

        "gender":
            person.gender,

        "height":
            person.height,

        "clothing":
            person.clothing,

        "description":
            person.description,

        "found_location":
            person.found_location,

        "found_date":
            safe_date(
                person.found_date
            ),

        "found_time":
            safe_date(
                person.found_time
            ),

        "latitude":
            getattr(
                person,
                "found_latitude",
                None
            ),

        "longitude":
            getattr(
                person,
                "found_longitude",
                None
            ),

        "condition":
            person.condition,

        "status":
            person.status,

        "photo_path":
            person.photo_path,

        "photo_url":
            get_photo_url(
                "found-person-photos",
                person.photo_path
            ),

        "created_at":
            safe_datetime(
                person.created_at
            )

    }

    if include_private:

        data.update({

            "finder_name":
                person.finder_name,

            "phone":
                person.phone,

            "email":
                person.email,

            "organization":
                person.organization,

            "police_station":
                person.police_station

        })

    return data


# ============================================================
# HEALTH
# ============================================================

@api.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "success": True,

        "service":
            "MissingLink AI",

        "message":
            "API is running.",

        "timestamp":
            datetime.utcnow().isoformat()

    }), 200


# ============================================================
# GET ALL MISSING REPORTS
# ============================================================

@api.route(
    "/missing",
    methods=["GET"]
)
@api_key_required
def get_missing():

    try:

        reports = (
            MissingPerson.query
            .order_by(
                MissingPerson.created_at.desc()
            )
            .all()
        )

        return jsonify({

            "success": True,

            "count":
                len(reports),

            "reports": [

                serialize_missing(
                    person,
                    include_private=False
                )

                for person in reports

            ]

        }), 200

    except Exception as e:

        print(
            "API MISSING ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to fetch missing reports."

        }), 500


# ============================================================
# GET ALL FOUND REPORTS
# ============================================================

@api.route(
    "/found",
    methods=["GET"]
)
@api_key_required
def get_found():

    try:

        reports = (
            FoundPerson.query
            .order_by(
                FoundPerson.created_at.desc()
            )
            .all()
        )

        return jsonify({

            "success": True,

            "count":
                len(reports),

            "reports": [

                serialize_found(
                    person,
                    include_private=False
                )

                for person in reports

            ]

        }), 200

    except Exception as e:

        print(
            "API FOUND ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to fetch found reports."

        }), 500


# ============================================================
# GET SINGLE REPORT
# ============================================================

@api.route(
    "/report/<report_id>",
    methods=["GET"]
)
@api_key_required
def get_report(report_id):

    report_id = normalize_report_id(
        report_id
    )

    missing = MissingPerson.query.filter_by(
        report_id=report_id
    ).first()

    if missing:

        return jsonify({

            "success": True,

            "type":
                "missing",

            "report":
                serialize_missing(
                    missing,
                    include_private=False
                )

        }), 200

    found = FoundPerson.query.filter_by(
        report_id=report_id
    ).first()

    if found:

        return jsonify({

            "success": True,

            "type":
                "found",

            "report":
                serialize_found(
                    found,
                    include_private=False
                )

        }), 200

    return jsonify({

        "success": False,

        "message":
            "Report not found."

    }), 404


# ============================================================
# TRACK REPORT
# ============================================================

@api.route(
    "/track/<report_id>",
    methods=["GET"]
)
def track_report_api(report_id):

    report_id = normalize_report_id(
        report_id
    )

    missing = MissingPerson.query.filter_by(
        report_id=report_id
    ).first()

    if missing:

        return jsonify({

            "success": True,

            "report_id":
                report_id,

            "type":
                "missing",

            "status":
                missing.status

        }), 200

    found = FoundPerson.query.filter_by(
        report_id=report_id
    ).first()

    if found:

        return jsonify({

            "success": True,

            "report_id":
                report_id,

            "type":
                "found",

            "status":
                found.status

        }), 200

    return jsonify({

        "success": False,

        "message":
            "No report found with this Report ID."

    }), 404


# ============================================================
# COUNTS
# ============================================================

@api.route(
    "/counts",
    methods=["GET"]
)
@api_key_required
def counts():

    try:

        missing_count = (
            MissingPerson.query.count()
        )

        found_count = (
            FoundPerson.query.count()
        )

        return jsonify({

            "success": True,

            "missing_count":
                missing_count,

            "found_count":
                found_count,

            "total_count":
                missing_count + found_count

        }), 200

    except Exception as e:

        print(
            "API COUNTS ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to fetch counts."

        }), 500


# ============================================================
# DASHBOARD
# ============================================================

@api.route(
    "/dashboard",
    methods=["GET"]
)
@api_key_required
def dashboard_api():

    try:

        missing_count = (
            MissingPerson.query.count()
        )

        found_count = (
            FoundPerson.query.count()
        )

        return jsonify({

            "success": True,

            "dashboard": {

                "missing_count":
                    missing_count,

                "found_count":
                    found_count,

                "total_count":
                    missing_count + found_count

            }

        }), 200

    except Exception as e:

        print(
            "API DASHBOARD ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to load dashboard."

        }), 500


# ============================================================
# NEW CASES
# ============================================================

@api.route(
    "/new-cases",
    methods=["GET"]
)
@api_key_required
def new_cases_api():

    try:

        limit = request.args.get(
            "limit",
            default=20,
            type=int
        )

        limit = max(
            1,
            min(limit, 100)
        )

        missing = (
            MissingPerson.query
            .order_by(
                MissingPerson.created_at.desc()
            )
            .limit(limit)
            .all()
        )

        found = (
            FoundPerson.query
            .order_by(
                FoundPerson.created_at.desc()
            )
            .limit(limit)
            .all()
        )

        cases = []

        for person in missing:

            cases.append({

                "type":
                    "missing",

                "report_id":
                    person.report_id,

                "name":
                    person.name,

                "location":
                    person.last_seen_location,

                "date":
                    safe_date(
                        person.last_seen_date
                    ),

                "status":
                    person.status,

                "created_at":
                    safe_datetime(
                        person.created_at
                    ),

                "person":
                    serialize_missing(person)

            })

        for person in found:

            cases.append({

                "type":
                    "found",

                "report_id":
                    person.report_id,

                "name":
                    "Unknown Person",

                "location":
                    person.found_location,

                "date":
                    safe_date(
                        person.found_date
                    ),

                "status":
                    person.status,

                "created_at":
                    safe_datetime(
                        person.created_at
                    ),

                "person":
                    serialize_found(person)

            })

        cases.sort(
            key=lambda x:
                x["created_at"] or "",
            reverse=True
        )

        cases = cases[:limit]

        return jsonify({

            "success": True,

            "count":
                len(cases),

            "missing_count":
                len([
                    x for x in cases
                    if x["type"] == "missing"
                ]),

            "found_count":
                len([
                    x for x in cases
                    if x["type"] == "found"
                ]),

            "cases":
                cases

        }), 200

    except Exception as e:

        print(
            "API NEW CASES ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to fetch new cases."

        }), 500


# ============================================================
# MISSING CASES
# ============================================================

@api.route(
    "/missing-cases",
    methods=["GET"]
)
@api_key_required
def missing_cases_api():

    reports = (
        MissingPerson.query
        .order_by(
            MissingPerson.created_at.desc()
        )
        .all()
    )

    return jsonify({

        "success": True,

        "count":
            len(reports),

        "reports": [

            serialize_missing(
                person
            )

            for person in reports

        ]

    }), 200


# ============================================================
# FOUND CASES
# ============================================================

@api.route(
    "/found-cases",
    methods=["GET"]
)
@api_key_required
def found_cases_api():

    reports = (
        FoundPerson.query
        .order_by(
            FoundPerson.created_at.desc()
        )
        .all()
    )

    return jsonify({

        "success": True,

        "count":
            len(reports),

        "reports": [

            serialize_found(
                person
            )

            for person in reports

        ]

    }), 200


# ============================================================
# CREATE MISSING REPORT
# ============================================================

@api.route(
    "/report/missing",
    methods=["POST"]
)
def create_missing_report_api():

    try:

        data = request.form.to_dict()

        if request.is_json:

            data = request.get_json(
                silent=True
            ) or {}

        # ------------------------------------------
        # REQUIRED FIELDS
        # ------------------------------------------

        email = str(
            data.get("email", "")
        ).strip()

        if not email:

            return jsonify({

                "success": False,

                "message":
                    "Email is required."

            }), 400

        name = str(
            data.get("name", "")
        ).strip()

        if not name:

            return jsonify({

                "success": False,

                "message":
                    "Name is required."

            }), 400

        # ------------------------------------------
        # DATE
        # ------------------------------------------

        last_seen_date = data.get(
            "last_seen_date"
        )

        if last_seen_date:

            try:

                parsed_date = datetime.strptime(
                    last_seen_date,
                    "%Y-%m-%d"
                ).date()

                if parsed_date >= date.today():

                    return jsonify({

                        "success": False,

                        "message":
                            "Last seen date must be before today's date."

                    }), 400

            except ValueError:

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid last seen date."

                }), 400

        # ------------------------------------------
        # LOCATION
        # ------------------------------------------

        valid, latitude, longitude, error = (
            validate_coordinates(
                data.get(
                    "last_seen_latitude"
                ),
                data.get(
                    "last_seen_longitude"
                )
            )
        )

        if not valid:

            return jsonify({

                "success": False,

                "message":
                    error

            }), 400

        # ------------------------------------------
        # PHOTO
        # ------------------------------------------

        photo = request.files.get(
            "photo"
        )

        if not photo:

            return jsonify({

                "success": False,

                "message":
                    "Photo is required."

            }), 400

        extension = os.path.splitext(
            photo.filename
        )[1].lower()

        allowed = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        }

        if extension not in allowed:

            return jsonify({

                "success": False,

                "message":
                    "Invalid image format."

            }), 400

        filename = (
            str(uuid.uuid4())
            + extension
        )

        upload_folder = current_app.config[
            "UPLOAD_FOLDER"
        ]

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        filepath = os.path.join(
            upload_folder,
            filename
        )

        photo.save(filepath)

        # ------------------------------------------
        # FACE EMBEDDING
        # ------------------------------------------

        success, embedding, message = (
            get_face_embedding(
                filepath
            )
        )

        if not success:

            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({

                "success": False,

                "message":
                    message

            }), 400

        embedding_json = json.dumps(
            embedding
        )

        # ------------------------------------------
        # SUPABASE
        # ------------------------------------------

        supabase = get_supabase()

        storage_path = filename

        try:

            with open(
                filepath,
                "rb"
            ) as image_file:

                supabase.storage.from_(
                    "missing-person-photos"
                ).upload(
                    storage_path,
                    image_file,
                    {
                        "content-type":
                            photo.content_type
                    }
                )

        finally:

            if os.path.exists(filepath):

                os.remove(filepath)

        # ------------------------------------------
        # OTP
        # ------------------------------------------

        generate_otp = (
            get_otp_generator()
        )

        otp = generate_otp()

        otp_hash = generate_password_hash(
            otp
        )

        pending_token = (
            secrets.token_urlsafe(32)
        )

        otp_expires_at = (
            datetime.utcnow()
            + timedelta(minutes=5)
        )

        # ------------------------------------------
        # REPORT DATA
        # ------------------------------------------

        report_data = {

            "name":
                name,

            "age":
                data.get("age"),

            "gender":
                data.get("gender"),

            "height":
                data.get("height"),

            "clothing":
                data.get("clothing"),

            "last_seen_location":
                data.get(
                    "last_seen_location"
                ),

            "last_seen_latitude":
                latitude,

            "last_seen_longitude":
                longitude,

            "last_seen_date":
                last_seen_date,

            "description":
                data.get("description"),

            "reporter_name":
                data.get("reporter_name"),

            "relationship":
                data.get("relationship"),

            "phone":
                data.get("phone"),

            "email":
                email

        }

        # ------------------------------------------
        # PENDING REPORT
        # ------------------------------------------

        pending = PendingReport(

            token=
                pending_token,

            report_type=
                "missing",

            report_data=
                json.dumps(report_data),

            photo_path=
                storage_path,

            embedding=
                embedding_json,

            email=
                email,

            otp_hash=
                otp_hash,

            otp_expires_at=
                otp_expires_at,

            otp_attempts=
                0

        )

        db.session.add(
            pending
        )

        db.session.commit()

        # ------------------------------------------
        # SEND OTP
        # ------------------------------------------

        send_email, send_otp_email = (
            get_email_functions()
        )

        email_sent = send_otp_email(

            to_email=
                email,

            to_name=
                data.get(
                    "reporter_name"
                ),

            otp=
                otp

        )

        if not email_sent:

            db.session.delete(
                pending
            )

            db.session.commit()

            try:

                supabase.storage.from_(
                    "missing-person-photos"
                ).remove([
                    storage_path
                ])

            except Exception:

                pass

            return jsonify({

                "success": False,

                "message":
                    "Unable to send verification OTP."

            }), 500

        return jsonify({

            "success": True,

            "message":
                "OTP sent successfully.",

            "pending_token":
                pending_token,

            "expires_in":
                300

        }), 201

    except Exception as e:

        db.session.rollback()

        print(
            "API CREATE MISSING ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to create missing report."

        }), 500


# ============================================================
# CREATE FOUND REPORT
# ============================================================

@api.route(
    "/report/found",
    methods=["POST"]
)
def create_found_report_api():

    try:

        data = request.form.to_dict()

        if request.is_json:

            data = request.get_json(
                silent=True
            ) or {}

        email = str(
            data.get("email", "")
        ).strip()

        if not email:

            return jsonify({

                "success": False,

                "message":
                    "Email is required."

            }), 400

        # ------------------------------------------
        # FOUND DATE
        # ------------------------------------------

        found_date = data.get(
            "found_date"
        )

        if not found_date:

            return jsonify({

                "success": False,

                "message":
                    "Found date is required."

            }), 400

        try:

            parsed_date = datetime.strptime(
                found_date,
                "%Y-%m-%d"
            ).date()

            if parsed_date >= date.today():

                return jsonify({

                    "success": False,

                    "message":
                        "Found date must be before today's date."

                }), 400

        except ValueError:

            return jsonify({

                "success": False,

                "message":
                    "Invalid found date."

            }), 400

        # ------------------------------------------
        # LOCATION
        # ------------------------------------------

        valid, latitude, longitude, error = (
            validate_coordinates(
                data.get(
                    "found_latitude"
                ),
                data.get(
                    "found_longitude"
                )
            )
        )

        if not valid:

            return jsonify({

                "success": False,

                "message":
                    error

            }), 400

        # ------------------------------------------
        # PHOTO
        # ------------------------------------------

        photo = request.files.get(
            "photo"
        )

        if not photo:

            return jsonify({

                "success": False,

                "message":
                    "Photo is required."

            }), 400

        extension = os.path.splitext(
            photo.filename
        )[1].lower()

        allowed = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        }

        if extension not in allowed:

            return jsonify({

                "success": False,

                "message":
                    "Invalid image format."

            }), 400

        filename = (
            str(uuid.uuid4())
            + extension
        )

        upload_folder = current_app.config[
            "UPLOAD_FOLDER"
        ]

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        filepath = os.path.join(
            upload_folder,
            filename
        )

        photo.save(filepath)

        # ------------------------------------------
        # AI
        # ------------------------------------------

        success, embedding, message = (
            get_face_embedding(
                filepath
            )
        )

        if not success:

            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({

                "success": False,

                "message":
                    message

            }), 400

        embedding_json = json.dumps(
            embedding
        )

        # ------------------------------------------
        # SUPABASE
        # ------------------------------------------

        supabase = get_supabase()

        storage_path = filename

        try:

            with open(
                filepath,
                "rb"
            ) as image_file:

                supabase.storage.from_(
                    "found-person-photos"
                ).upload(
                    storage_path,
                    image_file,
                    {
                        "content-type":
                            photo.content_type
                    }
                )

        finally:

            if os.path.exists(filepath):

                os.remove(filepath)

        # ------------------------------------------
        # OTP
        # ------------------------------------------

        generate_otp = (
            get_otp_generator()
        )

        otp = generate_otp()

        otp_hash = generate_password_hash(
            otp
        )

        pending_token = (
            secrets.token_urlsafe(32)
        )

        otp_expires_at = (
            datetime.utcnow()
            + timedelta(minutes=5)
        )

        # ------------------------------------------
        # REPORT DATA
        # ------------------------------------------

        report_data = {

            "estimated_age":
                data.get(
                    "estimated_age"
                ),

            "gender":
                data.get("gender"),

            "height":
                data.get("height"),

            "clothing":
                data.get("clothing"),

            "found_location":
                data.get(
                    "found_location"
                ),

            "found_latitude":
                latitude,

            "found_longitude":
                longitude,

            "found_date":
                found_date,

            "found_time":
                data.get("found_time"),

            "condition":
                data.get("condition"),

            "description":
                data.get("description"),

            "finder_name":
                data.get("finder_name"),

            "phone":
                data.get("phone"),

            "email":
                email,

            "organization":
                data.get("organization"),

            "police_station":
                data.get(
                    "police_station"
                )

        }

        # ------------------------------------------
        # PENDING REPORT
        # ------------------------------------------

        pending = PendingReport(

            token=
                pending_token,

            report_type=
                "found",

            report_data=
                json.dumps(report_data),

            photo_path=
                storage_path,

            embedding=
                embedding_json,

            email=
                email,

            otp_hash=
                otp_hash,

            otp_expires_at=
                otp_expires_at,

            otp_attempts=
                0

        )

        db.session.add(
            pending
        )

        db.session.commit()

        # ------------------------------------------
        # SEND OTP
        # ------------------------------------------

        send_email, send_otp_email = (
            get_email_functions()
        )

        email_sent = send_otp_email(

            to_email=
                email,

            to_name=
                data.get(
                    "finder_name"
                ),

            otp=
                otp

        )

        if not email_sent:

            db.session.delete(
                pending
            )

            db.session.commit()

            try:

                supabase.storage.from_(
                    "found-person-photos"
                ).remove([
                    storage_path
                ])

            except Exception:

                pass

            return jsonify({

                "success": False,

                "message":
                    "Unable to send verification OTP."

            }), 500

        return jsonify({

            "success": True,

            "message":
                "OTP sent successfully.",

            "pending_token":
                pending_token,

            "expires_in":
                300

        }), 201

    except Exception as e:

        db.session.rollback()

        print(
            "API CREATE FOUND ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to create found report."

        }), 500


# ============================================================
# VERIFY REPORT OTP
# ============================================================

@api.route(
    "/report/verify-otp",
    methods=["POST"]
)
def verify_report_otp_api():

    try:

        data = (
            request.get_json(
                silent=True
            )
            or
            request.form
        )

        token = str(
            data.get(
                "pending_token",
                ""
            )
        ).strip()

        otp = str(
            data.get(
                "otp",
                ""
            )
        ).strip()

        if not token:

            return jsonify({

                "success": False,

                "message":
                    "Pending token is required."

            }), 400

        if not otp:

            return jsonify({

                "success": False,

                "message":
                    "OTP is required."

            }), 400

        pending = PendingReport.query.filter_by(
            token=token
        ).first()

        if not pending:

            return jsonify({

                "success": False,

                "message":
                    "Pending report not found or expired."

            }), 404

        # ------------------------------------------
        # EXPIRY
        # ------------------------------------------

        if (
            pending.otp_expires_at
            and
            datetime.utcnow()
            > pending.otp_expires_at
        ):

            return jsonify({

                "success": False,

                "message":
                    "OTP has expired."

            }), 400

        # ------------------------------------------
        # ATTEMPTS
        # ------------------------------------------

        if pending.otp_attempts >= 5:

            return jsonify({

                "success": False,

                "message":
                    "Maximum OTP attempts exceeded."

            }), 429

        # ------------------------------------------
        # VERIFY
        # ------------------------------------------

        if not check_password_hash(
            pending.otp_hash,
            otp
        ):

            pending.otp_attempts += 1

            db.session.commit()

            return jsonify({

                "success": False,

                "message":
                    "Invalid OTP.",

                "attempts_remaining":
                    max(
                        0,
                        5 - pending.otp_attempts
                    )

            }), 400

        # ------------------------------------------
        # REPORT DATA
        # ------------------------------------------

        report_data = json.loads(
            pending.report_data
        )

        # ------------------------------------------
        # MISSING
        # ------------------------------------------

        if pending.report_type == "missing":

            report = MissingPerson(

                name=
                    report_data.get("name"),

                age=
                    report_data.get("age"),

                gender=
                    report_data.get("gender"),

                height=
                    report_data.get("height"),

                clothing=
                    report_data.get("clothing"),

                last_seen_location=
                    report_data.get(
                        "last_seen_location"
                    ),

                last_seen_latitude=
                    report_data.get(
                        "last_seen_latitude"
                    ),

                last_seen_longitude=
                    report_data.get(
                        "last_seen_longitude"
                    ),

                last_seen_date=
                    report_data.get(
                        "last_seen_date"
                    ),

                description=
                    report_data.get(
                        "description"
                    ),

                reporter_name=
                    report_data.get(
                        "reporter_name"
                    ),

                relationship=
                    report_data.get(
                        "relationship"
                    ),

                phone=
                    report_data.get(
                        "phone"
                    ),

                email=
                    report_data.get(
                        "email"
                    ),

                photo_path=
                    pending.photo_path,

                embedding=
                    pending.embedding,

                status=
                    "submitted"

            )

            db.session.add(
                report
            )

            db.session.flush()

            report.report_id = (
                f"ML-{str(uuid.uuid4())[:8].upper()}"
            )

            report_id = report.report_id

        # ------------------------------------------
        # FOUND
        # ------------------------------------------

        elif pending.report_type == "found":

            report = FoundPerson(

                estimated_age=
                    report_data.get(
                        "estimated_age"
                    ),

                gender=
                    report_data.get(
                        "gender"
                    ),

                height=
                    report_data.get(
                        "height"
                    ),

                clothing=
                    report_data.get(
                        "clothing"
                    ),

                found_location=
                    report_data.get(
                        "found_location"
                    ),

                found_latitude=
                    report_data.get(
                        "found_latitude"
                    ),

                found_longitude=
                    report_data.get(
                        "found_longitude"
                    ),

                found_date=
                    report_data.get(
                        "found_date"
                    ),

                found_time=
                    report_data.get(
                        "found_time"
                    ),

                condition=
                    report_data.get(
                        "condition"
                    ),

                description=
                    report_data.get(
                        "description"
                    ),

                finder_name=
                    report_data.get(
                        "finder_name"
                    ),

                phone=
                    report_data.get(
                        "phone"
                    ),

                email=
                    report_data.get(
                        "email"
                    ),

                organization=
                    report_data.get(
                        "organization"
                    ),

                police_station=
                    report_data.get(
                        "police_station"
                    ),

                photo_path=
                    pending.photo_path,

                embedding=
                    pending.embedding,

                status=
                    "submitted"

            )

            db.session.add(
                report
            )

            db.session.flush()

            report.report_id = (
                f"ML-F-{str(uuid.uuid4())[:8].upper()}"
            )

            report_id = report.report_id

        else:

            return jsonify({

                "success": False,

                "message":
                    "Invalid report type."

            }), 400

        # ------------------------------------------
        # DELETE PENDING REPORT
        # ------------------------------------------

        db.session.delete(
            pending
        )

        db.session.commit()

        return jsonify({

            "success": True,

            "message":
                "Report verified successfully.",

            "report_id":
                report_id,

            "type":
                pending.report_type,

            "status":
                report.status

        }), 201

    except Exception as e:

        db.session.rollback()

        print(
            "API VERIFY OTP ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to verify report."

        }), 500


# ============================================================
# UPDATE REPORT STATUS
# ============================================================

@api.route(
    "/report/status",
    methods=["POST"]
)
@api_key_required
def update_report_status_api():

    data = (
        request.get_json(
            silent=True
        )
        or
        request.form
    )

    report_id = normalize_report_id(
        str(
            data.get(
                "report_id",
                ""
            )
        )
    )

    new_status = str(
        data.get(
            "status",
            ""
        )
    ).strip().lower()

    report_type = str(
        data.get(
            "report_type",
            ""
        )
    ).strip().lower()

    allowed_statuses = {

        "submitted",

        "investigating",

        "potential_match",

        "found"

    }

    if not report_id:

        return jsonify({

            "success": False,

            "message":
                "Report ID is required."

        }), 400

    if new_status not in allowed_statuses:

        return jsonify({

            "success": False,

            "message":
                "Invalid report status."

        }), 400

    # ------------------------------------------
    # FIND REPORT
    # ------------------------------------------

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

        report = MissingPerson.query.filter_by(
            report_id=report_id
        ).first()

        if not report:

            report = FoundPerson.query.filter_by(
                report_id=report_id
            ).first()

    if not report:

        return jsonify({

            "success": False,

            "message":
                "Report not found."

        }), 404

    old_status = report.status

    if old_status == new_status:

        return jsonify({

            "success": True,

            "message":
                "Status is already set to this value.",

            "report_id":
                report_id,

            "status":
                new_status,

            "email_sent":
                False

        }), 200

    report.status = new_status

    try:

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "API STATUS ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to update report status."

        }), 500

    # ------------------------------------------
    # EMAIL
    # ------------------------------------------

    email_sent = False

    recipient_email = getattr(
        report,
        "email",
        None
    )

    if isinstance(
        report,
        MissingPerson
    ):

        recipient_name = getattr(
            report,
            "reporter_name",
            None
        )

        category = (
            "Missing Person Report"
        )

    else:

        recipient_name = getattr(
            report,
            "finder_name",
            None
        )

        category = (
            "Found Person Report"
        )

    if recipient_email:

        try:

            send_email, _ = (
                get_email_functions()
            )

            labels = {

                "submitted":
                    "Report Submitted",

                "investigating":
                    "Under Investigation",

                "potential_match":
                    "Potential Match Found",

                "found":
                    "Person Found"

            }

            email_sent = send_email(

                to_email=
                    recipient_email,

                to_name=
                    recipient_name
                    or
                    "User",

                subject=(
                    "MissingLink AI - "
                    "Report Status Updated "
                    f"({report_id})"
                ),

                html_content=f"""

                <div style="
                    font-family:Arial,sans-serif;
                    max-width:650px;
                    margin:auto;
                    padding:30px;
                ">

                    <h2>
                        MissingLink AI
                    </h2>

                    <p>
                        Hello
                        <strong>
                            {recipient_name or "User"}
                        </strong>,
                    </p>

                    <p>
                        Your
                        <strong>
                            {category}
                        </strong>
                        has been updated.
                    </p>

                    <p>
                        <strong>
                            Report ID:
                        </strong>
                        {report_id}
                    </p>

                    <p>
                        <strong>
                            Previous Status:
                        </strong>
                        {labels.get(
                            old_status,
                            old_status
                        )}
                    </p>

                    <p>
                        <strong>
                            Current Status:
                        </strong>
                        {labels.get(
                            new_status,
                            new_status
                        )}
                    </p>

                    <p>
                        Please use your Report ID
                        to track the case.
                    </p>

                    <p>
                        Regards,<br>
                        <strong>
                            MissingLink AI Team
                        </strong>
                    </p>

                </div>

                """

            )

        except Exception as e:

            print(
                "API STATUS EMAIL ERROR:",
                e
            )

    return jsonify({

        "success": True,

        "message":
            "Report status updated successfully.",

        "report_id":
            report_id,

        "old_status":
            old_status,

        "new_status":
            new_status,

        "email_sent":
            email_sent

    }), 200


# ============================================================
# DELETE REPORT
# ============================================================

@api.route(
    "/report/<report_type>/<int:report_id>",
    methods=["DELETE"]
)
@api_key_required
def delete_report_api(
    report_type,
    report_id
):

    if report_type not in {
        "missing",
        "found"
    }:

        return jsonify({

            "success": False,

            "message":
                "Invalid report type."

        }), 400

    if report_type == "missing":

        report = MissingPerson.query.get(
            report_id
        )

        bucket_name = (
            "missing-person-photos"
        )

    else:

        report = FoundPerson.query.get(
            report_id
        )

        bucket_name = (
            "found-person-photos"
        )

    if not report:

        return jsonify({

            "success": False,

            "message":
                "Report not found."

        }), 404

    photo_path = report.photo_path

    report_identifier = (
        report.report_id
    )

    # ------------------------------------------
    # DELETE PHOTO
    # ------------------------------------------

    if photo_path:

        try:

            supabase = get_supabase()

            clean_path = photo_path

            prefix = bucket_name + "/"

            if clean_path.startswith(prefix):

                clean_path = clean_path[
                    len(prefix):
                ]

            supabase.storage.from_(
                bucket_name
            ).remove([
                clean_path
            ])

        except Exception as e:

            print(
                "API SUPABASE DELETE ERROR:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Unable to remove report photo."

            }), 500

    # ------------------------------------------
    # DATABASE
    # ------------------------------------------

    try:

        db.session.delete(
            report
        )

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "API DELETE ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to delete report."

        }), 500

    return jsonify({

        "success": True,

        "message":
            "Report deleted successfully.",

        "report_id":
            report_identifier

    }), 200


# ============================================================
# AI MATCHING
# ============================================================

@api.route(
    "/ai/match/<int:found_id>",
    methods=["GET"]
)
@api_key_required
def ai_match_api(found_id):

    try:

        found_person = (
            FoundPerson.query.get(
                found_id
            )
        )

        if not found_person:

            return jsonify({

                "success": False,

                "message":
                    "Found report not found."

            }), 404

        missing_people = (
            MissingPerson.query.all()
        )

        matches = find_best_matches(

            found_person,

            missing_people

        )

        results = []

        for match in matches[:5]:

            person = match.get(
                "person"
            )

            result = {

                "report_id":
                    getattr(
                        person,
                        "report_id",
                        None
                    ),

                "name":
                    getattr(
                        person,
                        "name",
                        None
                    ),

                "age":
                    getattr(
                        person,
                        "age",
                        None
                    ),

                "gender":
                    getattr(
                        person,
                        "gender",
                        None
                    ),

                "location":
                    getattr(
                        person,
                        "last_seen_location",
                        None
                    ),

                "status":
                    getattr(
                        person,
                        "status",
                        None
                    ),

                "photo_url":
                    get_photo_url(
                        "missing-person-photos",
                        getattr(
                            person,
                            "photo_path",
                            None
                        )
                    )

            }

            # Preserve whatever score fields
            # your existing matcher returns.

            for key, value in match.items():

                if key != "person":

                    try:

                        json.dumps(value)

                        result[key] = value

                    except TypeError:

                        result[key] = str(
                            value
                        )

            results.append(
                result
            )

        return jsonify({

            "success": True,

            "found_report": {

                "id":
                    found_person.id,

                "report_id":
                    found_person.report_id,

                "photo_url":
                    get_photo_url(
                        "found-person-photos",
                        found_person.photo_path
                    )

            },

            "match_count":
                len(results),

            "matches":
                results

        }), 200

    except Exception as e:

        print(
            "API AI MATCH ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "AI matching failed."

        }), 500


# ============================================================
# ORGANIZATION LOGIN
# ============================================================

# ============================================================
# API ORGANIZATION REGISTRATION (FOR MOBILE APP)
# ============================================================
@api.route("/auth/register", methods=["POST"])
def organization_register_api():
    try:
        # 1. Get form data (using request.form because it's multipart with an image)
        organization = request.form.get("organization")
        role = request.form.get("role")
        full_name = request.form.get("full_name")
        government_id = request.form.get("government_id")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        
        # 2. Check for duplicate email
        existing_email = Organization.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({"success": False, "message": "Email already registered."}), 400
            
        # 3. Handle ID Card Upload to Supabase
        file = request.files.get("id_card")
        if not file:
            return jsonify({"success": False, "message": "ID card image is required."}), 400

        filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        temp_filepath = os.path.join(current_app.config["ID_CARD_FOLDER"], filename)
        file.save(temp_filepath)

        supabase = get_supabase()
        storage_path = f"organization-documents/{filename}"
        
        with open(temp_filepath, "rb") as id_file:
            supabase.storage.from_("organization-documents").upload(
                storage_path, id_file, {"content-type": file.content_type}
            )
        os.remove(temp_filepath)

        # 4. Save to Database as Unverified
        new_org = Organization(
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
        db.session.add(new_org)
        db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Organization registered successfully. Awaiting administrator approval."
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 500

@api.route(
    "/auth/login",
    methods=["POST"]
)
def organization_login_api():

    data = (
        request.get_json(
            silent=True
        )
        or
        request.form
    )

    email = str(
        data.get(
            "email",
            ""
        )
    ).strip()

    password = str(
        data.get(
            "password",
            ""
        )
    )

    if not email or not password:

        return jsonify({

            "success": False,

            "message":
                "Email and password are required."

        }), 400

    organization = (
        Organization.query
        .filter_by(
            email=email
        )
        .first()
    )

    if not organization:

        return jsonify({

            "success": False,

            "message":
                "Organization account not found."

        }), 401

    if not check_password_hash(
        organization.password,
        password
    ):

        return jsonify({

            "success": False,

            "message":
                "Incorrect password."

        }), 401

    if not organization.verified:

        return jsonify({

            "success": False,

            "message":
                "Organization is awaiting administrator approval."

        }), 403

    return jsonify({

        "success": True,

        "message":
            "Login successful.",

        "organization": {

            "id":
                organization.id,

            "organization":
                organization.organization,

            "role":
                organization.role,

            "full_name":
                organization.full_name,

            "email":
                organization.email

        }

    }), 200


# ============================================================
# ORGANIZATION PROFILE
# ============================================================

@api.route(
    "/auth/me/<int:organization_id>",
    methods=["GET"]
)
@api_key_required
def organization_profile(
    organization_id
):

    organization = (
        Organization.query.get(
            organization_id
        )
    )

    if not organization:

        return jsonify({

            "success": False,

            "message":
                "Organization not found."

        }), 404

    return jsonify({

        "success": True,

        "organization": {

            "id":
                organization.id,

            "organization":
                organization.organization,

            "role":
                organization.role,

            "full_name":
                organization.full_name,

            "email":
                organization.email,

            "phone":
                organization.phone,

            "verified":
                organization.verified,

            "email_verified":
                getattr(
                    organization,
                    "email_verified",
                    False
                )

        }

    }), 200


# ============================================================
# ADMIN: ORGANIZATIONS
# ============================================================

@api.route(
    "/admin/organizations",
    methods=["GET"]
)
@admin_api_key_required
def admin_organizations():

    pending = (
        Organization.query
        .filter_by(
            verified=False
        )
        .all()
    )

    verified = (
        Organization.query
        .filter_by(
            verified=True
        )
        .all()
    )

    def serialize_org(org):

        return {

            "id":
                org.id,

            "organization":
                org.organization,

            "role":
                org.role,

            "full_name":
                org.full_name,

            "email":
                org.email,

            "phone":
                org.phone,

            "verified":
                org.verified,

            "email_verified":
                getattr(
                    org,
                    "email_verified",
                    False
                )

        }

    return jsonify({

        "success": True,

        "pending_count":
            len(pending),

        "verified_count":
            len(verified),

        "pending":
            [
                serialize_org(x)
                for x in pending
            ],

        "verified":
            [
                serialize_org(x)
                for x in verified
            ]

    }), 200


# ============================================================
# ADMIN: APPROVE ORGANIZATION
# ============================================================

@api.route(
    "/admin/organizations/<int:organization_id>/approve",
    methods=["POST"]
)
@admin_api_key_required
def approve_organization_api(
    organization_id
):

    organization = (
        Organization.query.get(
            organization_id
        )
    )

    if not organization:

        return jsonify({

            "success": False,

            "message":
                "Organization not found."

        }), 404

    organization.verified = True

    try:

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
                "Unable to approve organization."

        }), 500

    email_sent = False

    try:

        send_email, _ = (
            get_email_functions()
        )

        email_sent = send_email(

            to_email=
                organization.email,

            to_name=
                organization.full_name,

            subject=
                "MissingLink AI - Organization Approved",

            html_content=f"""

            <h2>MissingLink AI</h2>

            <p>
                Hello {organization.full_name},
            </p>

            <p>
                Your organization registration
                has been approved.
            </p>

            <p>
                <strong>
                    Organization:
                </strong>
                {organization.organization}
            </p>

            <p>
                You can now access
                MissingLink AI.
            </p>

            """

        )

    except Exception as e:

        print(
            "APPROVAL EMAIL ERROR:",
            e
        )

    return jsonify({

        "success": True,

        "message":
            "Organization approved.",

        "organization_id":
            organization.id,

        "email_sent":
            email_sent

    }), 200


# ============================================================
# ADMIN: REJECT ORGANIZATION
# ============================================================

@api.route(
    "/admin/organizations/<int:organization_id>",
    methods=["DELETE"]
)
@admin_api_key_required
def reject_organization_api(
    organization_id
):

    organization = (
        Organization.query.get(
            organization_id
        )
    )

    if not organization:

        return jsonify({

            "success": False,

            "message":
                "Organization not found."

        }), 404

    email = organization.email
    full_name = organization.full_name
    organization_name = organization.organization

    try:

        db.session.delete(
            organization
        )

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
                "Unable to reject organization."

        }), 500

    email_sent = False

    try:

        send_email, _ = (
            get_email_functions()
        )

        email_sent = send_email(

            to_email=email,

            to_name=full_name,

            subject=(
                "MissingLink AI - "
                "Organization Registration Update"
            ),

            html_content=f"""

            <h2>MissingLink AI</h2>

            <p>
                Hello {full_name},
            </p>

            <p>
                Your organization registration
                could not be approved at this time.
            </p>

            <p>
                <strong>
                    Organization:
                </strong>
                {organization_name}
            </p>

            """

        )

    except Exception as e:

        print(
            "REJECTION EMAIL ERROR:",
            e
        )

    return jsonify({

        "success": True,

        "message":
            "Organization rejected.",

        "email_sent":
            email_sent

    }), 200


# ============================================================
# ADMIN: SYSTEM STATISTICS
# ============================================================

@api.route(
    "/admin/stats",
    methods=["GET"]
)
@admin_api_key_required
def admin_stats():

    return jsonify({

        "success": True,

        "statistics": {

            "missing_reports":
                MissingPerson.query.count(),

            "found_reports":
                FoundPerson.query.count(),

            "organizations":
                Organization.query.count(),

            "verified_organizations":
                Organization.query.filter_by(
                    verified=True
                ).count(),

            "pending_organizations":
                Organization.query.filter_by(
                    verified=False
                ).count(),

            "pending_reports":
                PendingReport.query.count()

        }

    }), 200


# ============================================================
# REGISTER BLUEPRINT
# ============================================================

def register_api(app):

    app.register_blueprint(
        api
    )

    