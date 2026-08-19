import json
import math
import numpy as np


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(embedding1, embedding2):

    embedding1 = np.array(
        embedding1,
        dtype=np.float32
    )

    embedding2 = np.array(
        embedding2,
        dtype=np.float32
    )

    denominator = (
        np.linalg.norm(embedding1)
        *
        np.linalg.norm(embedding2)
    )

    if denominator == 0:
        return 0.0

    similarity = np.dot(
        embedding1,
        embedding2
    ) / denominator

    return float(similarity)


# ============================================================
# FACE SCORE
# ============================================================
# Converts cosine similarity into a UI-friendly score.
#
# NOTE:
# This is NOT a probability.
# It is a normalized AI similarity score.
# ============================================================

def calibrated_score(similarity):

    if similarity < 0.20:

        return 0.0

    elif similarity < 0.35:

        score = (
            (similarity - 0.20)
            / 0.15
        ) * 50

    elif similarity < 0.50:

        score = (
            50
            +
            ((similarity - 0.35) / 0.15)
            * 30
        )

    else:

        score = (
            80
            +
            ((similarity - 0.50) / 0.10)
            * 20
        )

    return round(
        max(
            0.0,
            min(score, 100.0)
        ),
        2
    )


# ============================================================
# AGE SIMILARITY
# ============================================================

def calculate_age_score(
    found_age,
    missing_age
):

    if found_age is None or missing_age is None:
        return None

    try:

        found_age = float(found_age)
        missing_age = float(missing_age)

    except (ValueError, TypeError):

        return None

    difference = abs(
        found_age - missing_age
    )

    # Same / almost same age
    if difference <= 2:
        return 100.0

    # 3 years difference
    elif difference <= 4:
        return 90.0

    # 5 years difference
    elif difference <= 7:
        return 75.0

    # 8 years difference
    elif difference <= 10:
        return 55.0

    # 11-15 years
    elif difference <= 15:
        return 30.0

    # Very different
    else:
        return 10.0


# ============================================================
# GENDER SIMILARITY
# ============================================================

def calculate_gender_score(
    found_gender,
    missing_gender
):

    if not found_gender or not missing_gender:
        return None

    found_gender = str(
        found_gender
    ).strip().lower()

    missing_gender = str(
        missing_gender
    ).strip().lower()

    # Normalize common variations

    male_values = {
        "male",
        "m",
        "man",
        "boy"
    }

    female_values = {
        "female",
        "f",
        "woman",
        "girl"
    }

    if (
        found_gender in male_values
        and missing_gender in male_values
    ):
        return 100.0

    if (
        found_gender in female_values
        and missing_gender in female_values
    ):
        return 100.0

    # Unknown / other values
    if found_gender == missing_gender:
        return 100.0

    return 0.0


# ============================================================
# HEIGHT PARSER
# ============================================================

def parse_height(height):

    if height is None:
        return None

    value = str(
        height
    ).strip().lower()

    if not value:
        return None

    # Remove common text

    value = value.replace(
        "cm",
        ""
    ).strip()

    try:

        # Direct numeric value
        if value.replace(
            ".",
            "",
            1
        ).isdigit():

            return float(value)

        # Feet + inches
        #
        # Examples:
        # 5'8
        # 5' 8"
        # 5 ft 8 in

        if "ft" in value:

            parts = value.split("ft")

            feet = float(
                parts[0].strip()
            )

            inches = 0.0

            if len(parts) > 1:

                inch_part = (
                    parts[1]
                    .replace("in", "")
                    .replace('"', "")
                    .strip()
                )

                if inch_part:
                    inches = float(
                        inch_part
                    )

            return (
                feet * 30.48
                +
                inches * 2.54
            )

        # Feet/inches notation

        if "'" in value:

            parts = value.split("'")

            feet = float(
                parts[0].strip()
            )

            inches = 0.0

            if len(parts) > 1:

                inch_part = (
                    parts[1]
                    .replace('"', "")
                    .strip()
                )

                if inch_part:
                    inches = float(
                        inch_part
                    )

            return (
                feet * 30.48
                +
                inches * 2.54
            )

    except (
        ValueError,
        TypeError
    ):

        return None

    return None


# ============================================================
# HEIGHT SIMILARITY
# ============================================================

def calculate_height_score(
    found_height,
    missing_height
):

    found_cm = parse_height(
        found_height
    )

    missing_cm = parse_height(
        missing_height
    )

    if (
        found_cm is None
        or missing_cm is None
    ):
        return None

    difference = abs(
        found_cm - missing_cm
    )

    if difference <= 2:
        return 100.0

    elif difference <= 5:
        return 90.0

    elif difference <= 8:
        return 75.0

    elif difference <= 12:
        return 55.0

    elif difference <= 18:
        return 30.0

    else:
        return 10.0


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):

    if (
        lat1 is None
        or lon1 is None
        or lat2 is None
        or lon2 is None
    ):
        return None

    try:

        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)

    except (
        ValueError,
        TypeError
    ):

        return None

    earth_radius = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    delta_lat = math.radians(
        lat2 - lat1
    )

    delta_lon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1_rad)
        *
        math.cos(lat2_rad)
        *
        math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# ============================================================
# LOCATION SIMILARITY
# ============================================================

def calculate_location_score(
    found_latitude,
    found_longitude,
    missing_latitude,
    missing_longitude
):

    distance = calculate_distance_km(
        found_latitude,
        found_longitude,
        missing_latitude,
        missing_longitude
    )

    if distance is None:
        return None

    # Very close
    if distance <= 2:
        score = 100.0

    elif distance <= 5:
        score = 95.0

    elif distance <= 10:
        score = 85.0

    elif distance <= 25:
        score = 70.0

    elif distance <= 50:
        score = 55.0

    elif distance <= 100:
        score = 40.0

    elif distance <= 250:
        score = 25.0

    elif distance <= 500:
        score = 15.0

    else:
        score = 5.0

    return round(
        score,
        2
    )


# ============================================================
# FINAL AI SCORE
# ============================================================

def calculate_final_score(
    face_score,
    age_score=None,
    gender_score=None,
    height_score=None,
    location_score=None
):

    # ========================================================
    # BASE WEIGHTS
    # ========================================================

    weights = {

        "face": 0.75,

        "age": 0.10,

        "gender": 0.05,

        "height": 0.05,

        "location": 0.05

    }

    scores = {

        "face": face_score,

        "age": age_score,

        "gender": gender_score,

        "height": height_score,

        "location": location_score

    }

    # ========================================================
    # ONLY USE AVAILABLE SIGNALS
    # ========================================================

    weighted_total = 0.0
    available_weight = 0.0

    for key, weight in weights.items():

        score = scores.get(key)

        if score is None:
            continue

        weighted_total += (
            score * weight
        )

        available_weight += weight

    # ========================================================
    # SAFETY
    # ========================================================

    if available_weight == 0:

        return 0.0

    # Re-normalize weights when some
    # information is unavailable.

    final_score = (
        weighted_total
        /
        available_weight
    )

    return round(
        max(
            0.0,
            min(
                final_score,
                100.0
            )
        ),
        2
    )


# ============================================================
# MATCH CONFIDENCE
# ============================================================

def get_match_confidence(
    final_score,
    face_score
):

    # ========================================================
    # IMPORTANT:
    # Final score alone should not create
    # a high-confidence face match.
    # ========================================================

    if (
        face_score >= 80
        and final_score >= 85
    ):

        return (
            "HIGH CONFIDENCE",
            "Potential Match"
        )

    if (
        face_score >= 65
        and final_score >= 70
    ):

        return (
            "MODERATE CONFIDENCE",
            "Potential Match"
        )

    if (
        face_score >= 50
        and final_score >= 55
    ):

        return (
            "LOW CONFIDENCE",
            "Possible Match"
        )

    return (
        "VERY LOW CONFIDENCE",
        "Unlikely Match"
    )


# ============================================================
# FIND BEST MATCHES
# ============================================================

def find_best_matches(
    found_person,
    missing_people
):

    # ========================================================
    # FOUND EMBEDDING
    # ========================================================

    if not found_person.embedding:
        return []

    try:

        found_embedding = json.loads(
            found_person.embedding
        )

    except Exception as e:

        print(
            "FOUND EMBEDDING ERROR:",
            e
        )

        return []

    matches = []

    # ========================================================
    # COMPARE EACH MISSING PERSON
    # ========================================================

    for person in missing_people:

        if not person.embedding:
            continue

        try:

            missing_embedding = json.loads(
                person.embedding
            )

            # ==================================================
            # FACE SIMILARITY
            # ==================================================

            raw_similarity = cosine_similarity(
                found_embedding,
                missing_embedding
            )

            face_score = calibrated_score(
                raw_similarity
            )

            # ==================================================
            # AGE
            # ==================================================

            age_score = calculate_age_score(
                found_person.estimated_age,
                person.age
            )

            # ==================================================
            # GENDER
            # ==================================================

            gender_score = calculate_gender_score(
                found_person.gender,
                person.gender
            )

            # ==================================================
            # HEIGHT
            # ==================================================

            height_score = calculate_height_score(
                found_person.height,
                person.height
            )

            # ==================================================
            # LOCATION
            # ==================================================

            location_score = calculate_location_score(
                found_person.found_latitude,
                found_person.found_longitude,
                person.last_seen_latitude,
                person.last_seen_longitude
            )

            # ==================================================
            # FINAL AI SCORE
            # ==================================================

            final_score = calculate_final_score(

                face_score=face_score,

                age_score=age_score,

                gender_score=gender_score,

                height_score=height_score,

                location_score=location_score
            )

            # ==================================================
            # CONFIDENCE
            # ==================================================

            confidence, decision = (
                get_match_confidence(
                    final_score,
                    face_score
                )
            )

            # ==================================================
            # DISTANCE
            # ==================================================

            distance_km = calculate_distance_km(

                found_person.found_latitude,

                found_person.found_longitude,

                person.last_seen_latitude,

                person.last_seen_longitude
            )

            if distance_km is not None:

                distance_km = round(
                    distance_km,
                    2
                )

            # ==================================================
            # DEBUG
            # ==================================================

            print(
                "\n"
                "====================================\n"
                f"Candidate: {person.name}\n"
                f"Cosine Similarity: {raw_similarity:.4f}\n"
                f"Face Score: {face_score:.2f}%\n"
                f"Age Score: {age_score}\n"
                f"Gender Score: {gender_score}\n"
                f"Height Score: {height_score}\n"
                f"Location Score: {location_score}\n"
                f"Distance: {distance_km} km\n"
                f"FINAL AI SCORE: {final_score:.2f}%\n"
                f"CONFIDENCE: {confidence}\n"
                f"DECISION: {decision}\n"
                "===================================="
            )

            # ==================================================
            # STORE RESULT
            # ==================================================

            matches.append({

                "person": person,

                # Raw face similarity
                "cosine_similarity": round(
                    raw_similarity,
                    4
                ),

                # Individual AI signals
                "face_score": face_score,

                "age_score": age_score,

                "gender_score": gender_score,

                "height_score": height_score,

                "location_score": location_score,

                "distance_km": distance_km,

                # Final calculation
                "similarity": final_score,

                "final_score": final_score,

                "confidence": confidence,

                "decision": decision

            })

        except Exception as e:

            print(
                f"ERROR comparing "
                f"{person.name}: {e}"
            )

            continue

    # ========================================================
    # SORT BY FINAL AI SCORE
    # ========================================================

    matches.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return matches