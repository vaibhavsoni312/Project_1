import cv2
import time
import threading

from deepface import DeepFace

from app.ai.emotion import (
    reset_emotion_session,
    get_emotion_summary
)


# ============================================================
# CONFIG
# ============================================================

ANALYSIS_INTERVAL = 0.7

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

MODEL_INPUT_WIDTH = 640
MODEL_INPUT_HEIGHT = 360


# ============================================================
# SHARED STATE
# ============================================================

latest_frame = None

latest_result = {
    "emotion": "Detecting...",
    "confidence": 0.0,
    "stability": 0.0,
    "positive_score": 0.0,
    "negative_score": 0.0,
    "updated": False
}

frame_lock = threading.Lock()

result_lock = threading.Lock()

running = True


# ============================================================
# EMOTION WORKER
# ============================================================

def emotion_worker():

    global latest_frame
    global latest_result
    global running

    last_analysis = 0

    while running:

        # ----------------------------------------------------
        # Get latest frame
        # ----------------------------------------------------

        with frame_lock:

            if latest_frame is None:

                frame = None

            else:

                frame = latest_frame.copy()


        if frame is None:

            time.sleep(0.01)

            continue


        # ----------------------------------------------------
        # Don't analyze too frequently
        # ----------------------------------------------------

        now = time.time()

        if (
            now - last_analysis
            < ANALYSIS_INTERVAL
        ):

            time.sleep(0.01)

            continue


        last_analysis = now


        # ----------------------------------------------------
        # Resize for DeepFace
        # ----------------------------------------------------

        small_frame = cv2.resize(
            frame,
            (
                MODEL_INPUT_WIDTH,
                MODEL_INPUT_HEIGHT
            ),
            interpolation=cv2.INTER_AREA
        )


        # ----------------------------------------------------
        # DeepFace
        # ----------------------------------------------------

        try:

            result = DeepFace.analyze(

                img_path=small_frame,

                actions=["emotion"],

                detector_backend="opencv",

                enforce_detection=False,

                silent=True
            )


            if isinstance(
                result,
                list
            ):

                if len(result) == 0:

                    continue

                result = result[0]


            scores = result.get(
                "emotion",
                {}
            )


            if not scores:

                continue


            scores = {

                key.lower():
                float(value)

                for key, value
                in scores.items()
            }


            detected_emotion = max(
                scores,
                key=scores.get
            )


            confidence = scores.get(
                detected_emotion,
                0.0
            )


            # ------------------------------------------------
            # Update our emotion module state
            # ------------------------------------------------

            from app.ai import emotion as emotion_module


            emotion_module.emotion_history.append(
                detected_emotion
            )

            emotion_module.all_emotions.append(
                detected_emotion
            )

            emotion_module.all_confidences.append(
                confidence
            )

            emotion_module.last_scores = scores

            emotion_module.last_confidence = confidence


            smoothed = (
                emotion_module.get_smoothed_emotion(
                    emotion_module.emotion_history
                )
            )


            emotion_module.last_emotion = smoothed


            # ------------------------------------------------
            # Result
            # ------------------------------------------------

            new_result = {

                "emotion":
                    smoothed,

                "confidence":
                    confidence,

                "stability":
                    emotion_module.calculate_stability(
                        emotion_module.emotion_history
                    ),

                "positive_score":
                    emotion_module.get_positive_score(),

                "negative_score":
                    emotion_module.get_negative_score(),

                "updated":
                    True
            }


            with result_lock:

                latest_result = new_result


            # ------------------------------------------------
            # Terminal
            # ------------------------------------------------

            print(

                f"Emotion: "
                f"{smoothed.upper():10s}"
                f" | Confidence: "
                f"{confidence:5.1f}%"
                f" | Stability: "
                f"{new_result['stability']:5.1f}"
            )


        except Exception as e:

            # Don't kill camera thread
            pass


# ============================================================
# START
# ============================================================

reset_emotion_session()


cap = cv2.VideoCapture(0)


if not cap.isOpened():

    print(
        "ERROR: Camera could not be opened."
    )

    exit()


cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    FRAME_WIDTH
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    FRAME_HEIGHT
)


# ============================================================
# START WORKER THREAD
# ============================================================

worker = threading.Thread(
    target=emotion_worker,
    daemon=True
)

worker.start()


print()
print("=" * 60)
print("       PREP-CHECK - SMOOTH EMOTION V4")
print("=" * 60)
print()
print("Camera runs continuously.")
print("Emotion analysis runs in background.")
print("Try different facial expressions.")
print("Press Q to finish.")
print()


# ============================================================
# CAMERA LOOP
# ============================================================

while True:

    ret, frame = cap.read()


    if not ret:

        print(
            "ERROR: Could not read camera."
        )

        break


    # --------------------------------------------------------
    # Mirror
    # --------------------------------------------------------

    frame = cv2.flip(
        frame,
        1
    )


    # --------------------------------------------------------
    # Give latest frame to worker
    # --------------------------------------------------------

    with frame_lock:

        latest_frame = frame.copy()


    # --------------------------------------------------------
    # Get latest emotion result
    # --------------------------------------------------------

    with result_lock:

        result = latest_result.copy()


    emotion = result.get(
        "emotion",
        "Detecting..."
    )


    confidence = result.get(
        "confidence",
        0
    )


    stability = result.get(
        "stability",
        0
    )


    positive = result.get(
        "positive_score",
        0
    )


    negative = result.get(
        "negative_score",
        0
    )


    # ========================================================
    # UI
    # ========================================================

    cv2.putText(

        frame,

        f"Emotion: {emotion.upper()}",

        (30, 45),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.85,

        (0, 255, 0),

        2
    )


    cv2.putText(

        frame,

        f"Confidence: {confidence:.0f}%",

        (30, 82),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.7,

        (0, 255, 255),

        2
    )


    cv2.putText(

        frame,

        f"Stability: {stability:.0f}/100",

        (30, 117),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.7,

        (255, 255, 0),

        2
    )


    cv2.putText(

        frame,

        f"Positive: {positive:.0f}%",

        (30, 152),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (0, 255, 0),

        2
    )


    cv2.putText(

        frame,

        f"Negative: {negative:.0f}%",

        (30, 187),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (0, 0, 255),

        2
    )


    # --------------------------------------------------------
    # Processing indicator
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "Emotion AI: ACTIVE",

        (30, 225),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (255, 255, 255),

        2
    )


    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    cv2.imshow(

        "PREP-CHECK - Smooth Emotion V4",

        frame
    )


    # --------------------------------------------------------
    # Quit
    # --------------------------------------------------------

    if (
        cv2.waitKey(1) & 0xFF
        == ord("q")
    ):

        break


# ============================================================
# STOP
# ============================================================

running = False

cap.release()

cv2.destroyAllWindows()


# ============================================================
# FINAL REPORT
# ============================================================

summary = get_emotion_summary()


print()
print("=" * 60)
print("             EMOTION MODULE REPORT")
print("=" * 60)

print()

print(
    f"Predictions        : "
    f"{summary['predictions']}"
)

print(
    f"Dominant Emotion   : "
    f"{summary['dominant_emotion'].upper()}"
)

print(
    f"Average Confidence : "
    f"{summary['average_confidence']:.1f}%"
)

print(
    f"Stability          : "
    f"{summary['stability']:.1f}/100"
)

print(
    f"Positive           : "
    f"{summary['positive_percentage']:.1f}%"
)

print(
    f"Neutral            : "
    f"{summary['neutral_percentage']:.1f}%"
)

print(
    f"Negative           : "
    f"{summary['negative_percentage']:.1f}%"
)

print(
    f"Reactions          : "
    f"{summary['reaction_count']}"
)

print(
    f"Transitions        : "
    f"{summary['transition_count']}"
)

print()
print("=" * 60)
print("                 TEST FINISHED")
print("=" * 60)