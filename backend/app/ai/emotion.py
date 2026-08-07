from deepface import DeepFace

def detect_emotion(frame):
    try:
        result = DeepFace.analyze(
            img_path=frame,
            actions=["emotion"],
            enforce_detection=False,
            silent=True
        )

        if isinstance(result, list):
            result = result[0]

        return {
            "emotion": result["dominant_emotion"],
            "score": result["emotion"]
        }

    except Exception as e:
        print("DEEPFACE ERROR:", e)   # <-- IMPORTANT
        return {
            "emotion": "unknown",
            "score": {},
            "error": str(e)
        }