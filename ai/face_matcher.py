import json
import numpy as np


def cosine_similarity(embedding1, embedding2):

    embedding1 = np.array(embedding1)
    embedding2 = np.array(embedding2)

    similarity = np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) *
        np.linalg.norm(embedding2)
    )

    return float(similarity)


def find_best_matches(found_person, missing_people):

    found_embedding = json.loads(found_person.embedding)

    matches = []

    for person in missing_people:
         
        if not person.embedding:
            continue

        missing_embedding = json.loads(person.embedding)

        similarity = cosine_similarity(
            found_embedding,
            missing_embedding
        )

        matches.append({

            "person": person,

            "similarity": round(similarity * 100, 2)

        })

    matches.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return matches