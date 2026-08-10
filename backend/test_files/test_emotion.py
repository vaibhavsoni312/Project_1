import cv2
import time
from collections import deque, Counter
from deepface import DeepFace


# ============================================================
# CONFIG
# ============================================================

CAMERA_ID = 0

# DeepFace ko roughly 4 times/sec run karenge
ANALYSIS_INTERVAL = 0.25

# Temporal smoothing
SMOOTHING_WINDOW = 7

# Reaction ko genuine maan-ne ke liye minimum
# consecutive predictions
REACTION_CONFIRMATION = 2


# ============================================================
# CAMERA
# ============================================================

cap = cv2.VideoCapture(CAMERA_ID)

if not cap.isOpened():
    raise RuntimeError("Could not open webcam.")


cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


# ============================================================
# EMOTIONS
# ============================================================

EMOTIONS = [
    "angry",
    "disgust",
    "fear",
    "happy",
    "sad",
    "surprise",
    "neutral"
]


POSITIVE_EMOTIONS = {
    "happy"
}


NEGATIVE_EMOTIONS = {
    "angry",
    "disgust",
    "fear",
    "sad"
}


# ============================================================
# SESSION STATE
# ============================================================

start_time = time.time()

last_prediction_time = 0

last_emotion = "Detecting..."

last_confidence = 0.0

last_scores = {}

emotion_history = deque(
    maxlen=SMOOTHING_WINDOW
)

all_emotions = []

all_confidences = []

timeline = []

transition_count = 0

reaction_count = 0

previous_emotion = None

candidate_emotion = None

candidate_count = 0

reaction_start_time = None


# ============================================================
# EMOTION SMOOTHING
# ============================================================

def get_smoothed_emotion(history):

    if not history:
        return "Detecting..."

    counts = Counter(history)

    return counts.most_common(1)[0][0]


# ============================================================
# STABILITY
# ============================================================

def calculate_stability(history):

    if len(history) < 2:
        return 100.0

    counts = Counter(history)

    dominant_count = counts.most_common(1)[0][1]

    return (
        dominant_count /
        len(history)
    ) * 100


# ============================================================
# MAIN
# ============================================================

print()
print("=" * 65)
print("          PREP-CHECK - FACIAL EMOTION V3")
print("=" * 65)
print()
print("Temporal facial-expression analysis")
print("Press Q to finish.")
print()


while True:

    ret, frame = cap.read()

    if not ret:
        print("Could not read camera frame.")
        break


    # ========================================================
    # MIRROR CAMERA
    # ========================================================

    frame = cv2.flip(
        frame,
        1
    )


    current_time = time.time()


    # ========================================================
    # DEEPFACE ANALYSIS
    # ========================================================

    if (
        current_time -
        last_prediction_time
        >= ANALYSIS_INTERVAL
    ):

        try:

            result = DeepFace.analyze(
                img_path=frame,
                actions=["emotion"],
                detector_backend="skip",
                enforce_detection=False,
                silent=True
            )


            # ------------------------------------------------
            # DeepFace response
            # ------------------------------------------------

            if isinstance(result, list):

                result = result[0]


            # ------------------------------------------------
            # Emotion probabilities
            # ------------------------------------------------

            scores = result.get(
                "emotion",
                {}
            )


            if not scores:

                raise ValueError(
                    "No emotion probabilities returned."
                )


            # Convert values to float
            scores = {
                emotion.lower(): float(value)
                for emotion, value
                in scores.items()
            }


            last_scores = scores


            # ------------------------------------------------
            # Dominant emotion
            # ------------------------------------------------

            detected_emotion = max(
                scores,
                key=scores.get
            )


            confidence = scores.get(
                detected_emotion,
                0.0
            )


            last_confidence = confidence


            # =================================================
            # TEMPORAL HISTORY
            # =================================================

            emotion_history.append(
                detected_emotion
            )

            all_emotions.append(
                detected_emotion
            )

            all_confidences.append(
                confidence
            )


            # =================================================
            # SMOOTHED EMOTION
            # =================================================

            smoothed_emotion = (
                get_smoothed_emotion(
                    emotion_history
                )
            )


            # =================================================
            # REACTION CANDIDATE
            # =================================================

            if (
                candidate_emotion
                != detected_emotion
            ):

                candidate_emotion = (
                    detected_emotion
                )

                candidate_count = 1

            else:

                candidate_count += 1


            # =================================================
            # CONFIRMED REACTION
            # =================================================

            if candidate_count >= REACTION_CONFIRMATION:

                if (
                    previous_emotion
                    is not None
                    and
                    candidate_emotion
                    != previous_emotion
                ):

                    transition_count += 1

                    reaction_count += 1

                    reaction_start_time = (
                        current_time
                    )


                    timeline.append({
                        "time": (
                            current_time -
                            start_time
                        ),
                        "from": previous_emotion,
                        "to": candidate_emotion
                    })


                previous_emotion = (
                    candidate_emotion
                )


            # =================================================
            # CURRENT EMOTION
            # =================================================

            last_emotion = (
                smoothed_emotion
            )


            # =================================================
            # TERMINAL OUTPUT
            # =================================================

            print(
                f"Emotion: "
                f"{detected_emotion.upper():9s}"
                f" | "
                f"Confidence: "
                f"{confidence:5.1f}%"
                f" | "
                f"Smoothed: "
                f"{smoothed_emotion.upper():9s}"
            )


        except Exception as e:

            print(
                "Emotion analysis error:",
                e
            )


        last_prediction_time = (
            current_time
        )


    # ========================================================
    # LIVE STABILITY
    # ========================================================

    stability = calculate_stability(
        emotion_history
    )


    # ========================================================
    # POSITIVE / NEGATIVE
    # ========================================================

    if last_scores:

        positive_score = sum(
            last_scores.get(
                emotion,
                0
            )
            for emotion
            in POSITIVE_EMOTIONS
        )


        negative_score = sum(
            last_scores.get(
                emotion,
                0
            )
            for emotion
            in NEGATIVE_EMOTIONS
        )

    else:

        positive_score = 0

        negative_score = 0


    # ========================================================
    # UI
    # ========================================================

    cv2.putText(
        frame,
        f"Emotion: {last_emotion.upper()}",
        (30, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 0),
        2
    )


    cv2.putText(
        frame,
        f"Confidence: {last_confidence:.0f}%",
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
        f"Reactions: {reaction_count}",
        (30, 152),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    # ========================================================
    # DISPLAY
    # ========================================================

    cv2.imshow(
        "PREP-CHECK - Facial Emotion V3",
        frame
    )


    # ========================================================
    # QUIT
    # ========================================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()


# ============================================================
# FINAL SESSION
# ============================================================

duration = (
    time.time()
    -
    start_time
)


print()
print("=" * 65)
print("             FACIAL EMOTION V3 REPORT")
print("=" * 65)

print(
    f"Duration              : "
    f"{duration:.1f} sec"
)

print(
    f"Predictions           : "
    f"{len(all_emotions)}"
)


# ============================================================
# EMOTION DISTRIBUTION
# ============================================================

if all_emotions:

    counts = Counter(
        all_emotions
    )

    total = len(
        all_emotions
    )


    print()
    print("EMOTION DISTRIBUTION")
    print("-" * 35)


    for emotion in EMOTIONS:

        count = counts.get(
            emotion,
            0
        )

        percentage = (
            count /
            total
        ) * 100


        print(
            f"{emotion.capitalize():12s}"
            f": {percentage:6.1f}%"
        )


    # ========================================================
    # DOMINANT
    # ========================================================

    dominant_emotion = (
        counts.most_common(1)[0][0]
    )


    # ========================================================
    # AVERAGE CONFIDENCE
    # ========================================================

    if all_confidences:

        average_confidence = (
            sum(all_confidences)
            /
            len(all_confidences)
        )

    else:

        average_confidence = 0


    # ========================================================
    # POSITIVE / NEGATIVE DISTRIBUTION
    # ========================================================

    positive_count = sum(
        counts.get(
            emotion,
            0
        )
        for emotion
        in POSITIVE_EMOTIONS
    )


    negative_count = sum(
        counts.get(
            emotion,
            0
        )
        for emotion
        in NEGATIVE_EMOTIONS
    )


    neutral_count = counts.get(
        "neutral",
        0
    )


    positive_percentage = (
        positive_count /
        total
    ) * 100


    negative_percentage = (
        negative_count /
        total
    ) * 100


    neutral_percentage = (
        neutral_count /
        total
    ) * 100


    # ========================================================
    # FINAL STABILITY
    # ========================================================

    final_stability = (
        calculate_stability(
            emotion_history
        )
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("-" * 35)

    print(
        f"Dominant Emotion       : "
        f"{dominant_emotion.upper()}"
    )

    print(
        f"Average Confidence     : "
        f"{average_confidence:.1f}%"
    )

    print(
        f"Expression Stability   : "
        f"{final_stability:.1f}/100"
    )

    print(
        f"Emotion Transitions    : "
        f"{transition_count}"
    )

    print(
        f"Detected Reactions     : "
        f"{reaction_count}"
    )

    print(
        f"Positive Expression    : "
        f"{positive_percentage:.1f}%"
    )

    print(
        f"Neutral Expression     : "
        f"{neutral_percentage:.1f}%"
    )

    print(
        f"Negative Expression    : "
        f"{negative_percentage:.1f}%"
    )


    # ========================================================
    # TIMELINE
    # ========================================================

    print()
    print("EMOTION TIMELINE")
    print("-" * 35)


    if timeline:

        for event in timeline:

            timestamp = event["time"]

            old_emotion = (
                event["from"].upper()
            )

            new_emotion = (
                event["to"].upper()
            )


            print(
                f"{timestamp:6.1f}s : "
                f"{old_emotion} → "
                f"{new_emotion}"
            )

    else:

        print(
            "No significant emotion transitions detected."
        )


    # ========================================================
    # OBSERVATION
    # ========================================================

    print()
    print("OBSERVATION")
    print("-" * 35)


    if final_stability >= 80:

        print(
            "Facial expression remained relatively stable."
        )

    elif final_stability >= 60:

        print(
            "Facial expression showed moderate variation."
        )

    else:

        print(
            "Facial expression showed frequent variation."
        )


    if positive_percentage > negative_percentage:

        print(
            "Positive expressions were more prominent "
            "than negative expressions."
        )

    elif negative_percentage > positive_percentage:

        print(
            "Negative expressions were more prominent "
            "than positive expressions."
        )

    else:

        print(
            "Positive and negative expressions were "
            "relatively balanced."
        )


else:

    print()
    print(
        "No emotion predictions were collected."
    )


# ============================================================
# END
# ============================================================

print()
print("=" * 65)
print("                 SESSION FINISHED")
print("=" * 65)