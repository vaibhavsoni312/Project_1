from collections import Counter

from app.ai.face_detector import detect_faces

emotions = detect_faces("sample.mp4")

print(emotions)

if emotions:

    final_emotion = Counter(emotions).most_common(1)[0][0]

    print("\nFINAL EMOTION:", final_emotion)

else:

    print("No face detected.")