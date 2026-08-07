import cv2
import mediapipe as mp

from app.ai.emotion_detector import detect_emotion


mp_face = mp.solutions.face_detection

face_detector = mp_face.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.5
)


def detect_faces(video_path):

    cap = cv2.VideoCapture(video_path)

    emotions = []

    while True:

        success, frame = cap.read()

        if not success:
            break

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        results = face_detector.process(rgb)

        if results.detections:

            h, w, _ = frame.shape

            for detection in results.detections:

                bbox = detection.location_data.relative_bounding_box

                x = max(0, int(bbox.xmin * w))
                y = max(0, int(bbox.ymin * h))
                width = int(bbox.width * w)
                height = int(bbox.height * h)

                face = frame[
                    y:y + height,
                    x:x + width
                ]

                if face.size == 0:
                    continue

                if width < 60 or height < 60:
                    continue

                emotion = detect_emotion(face)

                emotions.append(emotion)

                print("Emotion:", emotion)

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + width, y + height),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    emotion,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

        cv2.imshow("Emotion Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    return emotions