import cv2
import time
from deepface import DeepFace

cap = cv2.VideoCapture(0)

last_emotion = "Detecting..."
last_prediction = 0

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # mirror camera
    frame = cv2.flip(frame, 1)

    # DeepFace ko sirf har 1 sec me chalao
    if time.time() - last_prediction > 1:

        try:

            result = DeepFace.analyze(
                img_path=frame,
                actions=["emotion"],
                detector_backend="skip",
                enforce_detection=False,
                silent=True
            )

            if isinstance(result, list):
                result = result[0]

            last_emotion = result["dominant_emotion"]

            print("Emotion:", last_emotion)

        except Exception:
            pass

        last_prediction = time.time()

    cv2.putText(
        frame,
        f"Emotion : {last_emotion}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0,255,0),
        2
    )

    cv2.imshow("Interview Analyzer", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()