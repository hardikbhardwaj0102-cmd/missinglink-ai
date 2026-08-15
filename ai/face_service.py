import cv2
from insightface.app import FaceAnalysis


# ==========================================
# Load InsightFace Model
# ==========================================

face_app = FaceAnalysis(
    name="buffalo_s",
    providers=["CPUExecutionProvider"]
)

face_app.prepare(
    ctx_id=-1,
    det_size=(640, 640)
)


def get_face_embedding(image_path):
    """
    Detects exactly one face and generates its face embedding.

    Returns:
        success (bool)
        embedding (list or None)
        message (str)
    """

    image = cv2.imread(image_path)

    # ==========================================
    # Image could not be read
    # ==========================================

    if image is None:
        return (
            False,
            None,
            "Unable to read the uploaded image. Please try another image."
        )

    # ==========================================
    # Detect faces
    # ==========================================

    faces = face_app.get(image)

    # ==========================================
    # No face
    # ==========================================

    if len(faces) == 0:
        return (
            False,
            None,
            "No face detected. Please upload a clear image containing the person's face."
        )

    # ==========================================
    # Multiple faces
    # ==========================================

    if len(faces) > 1:
        return (
            False,
            None,
            "Multiple faces detected. Please upload an image containing only one person's face."
        )

    # ==========================================
    # Exactly one face
    # ==========================================

    embedding = faces[0].embedding.tolist()

    return (
        True,
        embedding,
        "Face detected successfully."
    )