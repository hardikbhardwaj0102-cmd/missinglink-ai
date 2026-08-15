from ai.face_service import get_face_embedding

success, embedding, message = get_face_embedding("static/uploads/test.jpg")

print(success)
print(message)

if success:
    print(type(embedding))
    print(len(embedding))