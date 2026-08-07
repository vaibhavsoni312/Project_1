from deepface import DeepFace


def detect_emotion(face):

    try:

        result = DeepFace.analyze(
            img_path=face,
            actions=["emotion"],
            detector_backend="skip",
            enforce_detection=False,
            silent=True
        )

        if isinstance(result, list):
            result = result[0]

        return result["dominant_emotion"]

    except Exception as e:
        print("Emotion Error:", e)
        return "unknown"