import cv2
from insightface.app import FaceAnalysis

# Load the model only once
face_app = FaceAnalysis(name="buffalo_l")
face_app.prepare(ctx_id=-1)


def get_face_embedding(image_path):
    """
    Detects exactly one face and generates its face embedding.

    Returns:
        success (bool)
        embedding (list or None)
        message (str)
    """

    image = cv2.imread(image_path)

    # Image could not be read
    if image is None:
        return (
            False,
            None,
            "Unable to read the uploaded image. Please try another image."
        )

    # Detect faces
    faces = face_app.get(image)

    # No face detected
    if len(faces) == 0:
        return (
            False,
            None,
            "No face detected. Please upload a clear image containing the person's face."
        )

    # More than one face detected
    if len(faces) > 1:
        return (
            False,
            None,
            "Multiple faces detected. Please upload an image containing only one person's face."
        )

    # Exactly one face detected
    embedding = faces[0].embedding.tolist()

    return (
        True,
        embedding,
        "Face detected successfully."
    )