from app import app
from models import db, MissingPerson, FoundPerson

from ai.face_matcher import find_best_matches


with app.app_context():

    found_person = FoundPerson.query.first()

    missing_people = MissingPerson.query.all()

    matches = find_best_matches(
        found_person,
        missing_people
    )

    print("\n========== AI MATCHES ==========\n")

    for match in matches:

        person = match["person"]

        print(
            person.name,
            " -> ",
            match["similarity"],
            "%"
        )