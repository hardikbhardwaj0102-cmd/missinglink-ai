import json
import numpy as np


# ==========================================
# Cosine Similarity
# ==========================================

def cosine_similarity(embedding1, embedding2):

    embedding1 = np.array(embedding1, dtype=np.float32)
    embedding2 = np.array(embedding2, dtype=np.float32)

    denominator = (
        np.linalg.norm(embedding1) *
        np.linalg.norm(embedding2)
    )

    if denominator == 0:
        return 0.0

    similarity = np.dot(
        embedding1,
        embedding2
    ) / denominator

    return float(similarity)


# ==========================================
# Calibrated Match Score
# ==========================================

def calibrated_score(similarity):

    # Very low similarity
    if similarity < 0.20:
        return 0.0

    # 0.20 → 0%
    # 0.35 → 50%
    elif similarity < 0.35:
        score = (
            (similarity - 0.20)
            / 0.15
        ) * 50

    # 0.35 → 50%
    # 0.50 → 80%
    elif similarity < 0.50:
        score = (
            50
            + ((similarity - 0.35) / 0.15) * 30
        )

    # 0.50 → 80%
    # 0.60 → 100%
    else:
        score = (
            80
            + ((similarity - 0.50) / 0.10) * 20
        )

    return round(
        max(0.0, min(score, 100.0)),
        2
    )


# ==========================================
# Find Best Matches
# ==========================================

def find_best_matches(found_person, missing_people):

    # ==========================================
    # Found Person Embedding
    # ==========================================

    if not found_person.embedding:
        return []

    found_embedding = json.loads(
        found_person.embedding
    )

    matches = []

    # ==========================================
    # Compare With Missing People
    # ==========================================

    for person in missing_people:

        if not person.embedding:
            continue

        try:

            missing_embedding = json.loads(
                person.embedding
            )

            # Raw cosine similarity
            similarity = cosine_similarity(
                found_embedding,
                missing_embedding
            )

            # Calibrated score for UI
            match_score = calibrated_score(
                similarity
            )

            print(
                f"{person.name} | "
                f"Cosine: {similarity:.4f} | "
                f"Match Score: {match_score:.2f}%"
            )

            matches.append({

                "person": person,

                # Raw AI similarity
                "cosine_similarity": round(
                    similarity,
                    4
                ),

                # Calibrated UI score
                "similarity": match_score

            })

        except Exception as e:

            print(
                f"Error comparing with "
                f"{person.name}: {e}"
            )

            continue

    # ==========================================
    # Sort Highest Match First
    # ==========================================

    matches.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return matches