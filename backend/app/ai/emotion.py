import os
import time

from collections import Counter, deque

import cv2
import numpy as np
import mediapipe as mp

from deepface import DeepFace


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "app",
    "models",
    "face_landmarker.task"
)


if not os.path.isfile(MODEL_PATH):
    raise FileNotFoundError(
        f"Face landmark model not found:\n{MODEL_PATH}"
    )


# Analyze one emotion sample every 0.25 sec
ANALYSIS_INTERVAL = 0.25


# Temporal emotion smoothing
SMOOTHING_WINDOW = 5


# Number of consecutive observations needed
# before accepting an emotion transition.
REACTION_CONFIRMATION = 2


# Minimum dominant probability to accept
# a DeepFace prediction.
MIN_EMOTION_CONFIDENCE = 30.0


# Minimum acceptable face size
MIN_FACE_WIDTH = 60
MIN_FACE_HEIGHT = 60


# Maximum time for which a previous face box
# can be used as a recovery candidate.
MAX_RECOVERY_AGE = 0.75


# ============================================================
# EMOTION LABELS
# ============================================================

EMOTIONS = [
    "angry",
    "disgust",
    "fear",
    "happy",
    "sad",
    "surprise",
    "neutral",
]


POSITIVE_EMOTIONS = {
    "happy",
}


NEGATIVE_EMOTIONS = {
    "angry",
    "disgust",
    "fear",
    "sad",
}


# ============================================================
# MEDIAPIPE FACE LANDMARKER
# ============================================================

BaseOptions = mp.tasks.BaseOptions

VisionRunningMode = (
    mp.tasks.vision.RunningMode
)

FaceLandmarker = (
    mp.tasks.vision.FaceLandmarker
)

FaceLandmarkerOptions = (
    mp.tasks.vision.FaceLandmarkerOptions
)


face_options = FaceLandmarkerOptions(

    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),

    running_mode=VisionRunningMode.IMAGE,

    num_faces=1,

    min_face_detection_confidence=0.30,

    min_face_presence_confidence=0.30,

    min_tracking_confidence=0.30,

    output_face_blendshapes=False,

    output_facial_transformation_matrixes=False,
)


face_landmarker = (
    FaceLandmarker.create_from_options(
        face_options
    )
)


# ============================================================
# SESSION STATE
# ============================================================

last_prediction_time = -999.0

last_emotion = "UNKNOWN"

last_confidence = 0.0

last_scores = {}

last_error = None


emotion_history = deque(
    maxlen=SMOOTHING_WINDOW
)


all_emotions = []

all_confidences = []

all_scores = []


timeline = []


valid_prediction_count = 0

invalid_prediction_count = 0


reaction_count = 0

transition_count = 0


previous_emotion = None

candidate_emotion = None

candidate_count = 0


# ------------------------------------------------------------
# Previous valid face box
#
# x1, y1, x2, y2
# ------------------------------------------------------------

previous_face_box = None

previous_face_time = -999.0


# ============================================================
# RESET
# ============================================================

def reset_emotion_session():

    global last_prediction_time
    global last_emotion
    global last_confidence
    global last_scores
    global last_error

    global valid_prediction_count
    global invalid_prediction_count

    global reaction_count
    global transition_count

    global previous_emotion
    global candidate_emotion
    global candidate_count

    global previous_face_box
    global previous_face_time


    last_prediction_time = -999.0

    last_emotion = "UNKNOWN"

    last_confidence = 0.0

    last_scores = {}

    last_error = None


    emotion_history.clear()

    all_emotions.clear()

    all_confidences.clear()

    all_scores.clear()

    timeline.clear()


    valid_prediction_count = 0

    invalid_prediction_count = 0


    reaction_count = 0

    transition_count = 0


    previous_emotion = None

    candidate_emotion = None

    candidate_count = 0


    previous_face_box = None

    previous_face_time = -999.0


# ============================================================
# FRAME VALIDATION
# ============================================================

def is_valid_frame(frame):

    if frame is None:
        return False

    if not isinstance(
        frame,
        np.ndarray
    ):
        return False

    if frame.size == 0:
        return False

    if len(frame.shape) != 3:
        return False

    h, w = frame.shape[:2]

    if h < 40 or w < 40:
        return False

    return True


# ============================================================
# MEDIAPIPE LANDMARKS
# ============================================================

def get_face_landmarks(frame):

    if not is_valid_frame(frame):
        return None


    h, w = frame.shape[:2]


    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )


    result = face_landmarker.detect(
        mp_image
    )


    if not result.face_landmarks:
        return None


    return result.face_landmarks[0]


# ============================================================
# LANDMARK BOUNDING BOX
# ============================================================

def landmarks_to_box(
    landmarks,
    width,
    height
):

    xs = []
    ys = []


    for landmark in landmarks:

        try:

            x = (
                float(landmark.x)
                * width
            )

            y = (
                float(landmark.y)
                * height
            )

        except Exception:

            continue


        if not np.isfinite(x):
            continue

        if not np.isfinite(y):
            continue


        xs.append(x)
        ys.append(y)


    if len(xs) < 20:
        return None


    x_min = int(
        np.floor(min(xs))
    )

    y_min = int(
        np.floor(min(ys))
    )

    x_max = int(
        np.ceil(max(xs))
    )

    y_max = int(
        np.ceil(max(ys))
    )


    x_min = max(
        0,
        min(
            x_min,
            width - 1
        )
    )

    y_min = max(
        0,
        min(
            y_min,
            height - 1
        )
    )

    x_max = max(
        1,
        min(
            x_max,
            width
        )
    )

    y_max = max(
        1,
        min(
            y_max,
            height
        )
    )


    if (
        x_max - x_min
        <
        MIN_FACE_WIDTH
    ):
        return None


    if (
        y_max - y_min
        <
        MIN_FACE_HEIGHT
    ):
        return None


    return (
        x_min,
        y_min,
        x_max,
        y_max
    )


# ============================================================
# PAD FACE BOX
# ============================================================

def pad_face_box(
    box,
    width,
    height
):

    x1, y1, x2, y2 = box


    face_w = x2 - x1

    face_h = y2 - y1


    # More space around face.
    pad_x = int(
        face_w * 0.25
    )

    pad_y = int(
        face_h * 0.30
    )


    x1 = max(
        0,
        x1 - pad_x
    )

    y1 = max(
        0,
        y1 - pad_y
    )

    x2 = min(
        width,
        x2 + pad_x
    )

    y2 = min(
        height,
        y2 + pad_y
    )


    return (
        x1,
        y1,
        x2,
        y2
    )


# ============================================================
# BOX VALIDATION
# ============================================================

def valid_box(
    box,
    width,
    height
):

    if box is None:
        return False


    x1, y1, x2, y2 = box


    if x2 <= x1:
        return False

    if y2 <= y1:
        return False


    if x1 < 0:
        return False

    if y1 < 0:
        return False

    if x2 > width:
        return False

    if y2 > height:
        return False


    if x2 - x1 < MIN_FACE_WIDTH:
        return False

    if y2 - y1 < MIN_FACE_HEIGHT:
        return False


    return True


# ============================================================
# FACE BOX RECOVERY
# ============================================================

def recover_previous_face(
    frame,
    current_time
):

    global previous_face_box
    global previous_face_time


    if previous_face_box is None:
        return None


    age = (
        current_time
        -
        previous_face_time
    )


    if age > MAX_RECOVERY_AGE:
        return None


    h, w = frame.shape[:2]


    x1, y1, x2, y2 = (
        previous_face_box
    )


    # Slightly expand previous region
    # to tolerate head movement.
    bw = x2 - x1
    bh = y2 - y1


    expand_x = int(
        bw * 0.15
    )

    expand_y = int(
        bh * 0.15
    )


    x1 = max(
        0,
        x1 - expand_x
    )

    y1 = max(
        0,
        y1 - expand_y
    )

    x2 = min(
        w,
        x2 + expand_x
    )

    y2 = min(
        h,
        y2 + expand_y
    )


    if not valid_box(
        (
            x1,
            y1,
            x2,
            y2
        ),
        w,
        h
    ):
        return None


    crop = frame[
        y1:y2,
        x1:x2
    ]


    if crop.size == 0:
        return None


    return crop


# ============================================================
# FACE CROP
# ============================================================

def detect_face_crop(
    frame,
    current_time
):

    global previous_face_box
    global previous_face_time


    h, w = frame.shape[:2]


    landmarks = get_face_landmarks(
        frame
    )


    # --------------------------------------------------------
    # NORMAL DETECTION
    # --------------------------------------------------------

    if landmarks is not None:

        box = landmarks_to_box(
            landmarks,
            w,
            h
        )


        if box is not None:

            padded = pad_face_box(
                box,
                w,
                h
            )


            if valid_box(
                padded,
                w,
                h
            ):

                x1, y1, x2, y2 = (
                    padded
                )


                crop = frame[
                    y1:y2,
                    x1:x2
                ]


                if (
                    crop.size > 0
                    and
                    crop.shape[1]
                    >= MIN_FACE_WIDTH
                    and
                    crop.shape[0]
                    >= MIN_FACE_HEIGHT
                ):

                    previous_face_box = (
                        x1,
                        y1,
                        x2,
                        y2
                    )

                    previous_face_time = (
                        current_time
                    )


                    return crop


    # --------------------------------------------------------
    # RECOVERY
    # --------------------------------------------------------

    recovered = recover_previous_face(
        frame,
        current_time
    )


    if recovered is not None:
        return recovered


    return None


# ============================================================
# FACE QUALITY
# ============================================================

def face_quality(
    face_crop
):

    if face_crop is None:
        return 0.0


    h, w = face_crop.shape[:2]


    if (
        w < MIN_FACE_WIDTH
        or
        h < MIN_FACE_HEIGHT
    ):
        return 0.0


    gray = cv2.cvtColor(
        face_crop,
        cv2.COLOR_BGR2GRAY
    )


    # --------------------------------------------------------
    # Blur quality
    # --------------------------------------------------------

    sharpness = (
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )


    # --------------------------------------------------------
    # Brightness
    # --------------------------------------------------------

    brightness = float(
        np.mean(gray)
    )


    # --------------------------------------------------------
    # Convert quality into a conservative score
    # --------------------------------------------------------

    sharp_score = np.clip(
        sharpness / 120.0,
        0.0,
        1.0
    )


    brightness_score = 1.0


    if brightness < 35:
        brightness_score = 0.4

    elif brightness < 50:
        brightness_score = 0.7

    elif brightness > 235:
        brightness_score = 0.5

    elif brightness > 220:
        brightness_score = 0.75


    quality = (
        0.75 * sharp_score
        +
        0.25 * brightness_score
    )


    return float(
        np.clip(
            quality * 100.0,
            0.0,
            100.0
        )
    )


# ============================================================
# NORMALIZE DEEPFACE SCORES
# ============================================================

def normalize_scores(
    raw_scores
):

    if not isinstance(
        raw_scores,
        dict
    ):
        return {}


    scores = {}


    for emotion in EMOTIONS:

        try:

            value = float(
                raw_scores.get(
                    emotion,
                    0.0
                )
            )

        except Exception:

            value = 0.0


        if not np.isfinite(
            value
        ):
            value = 0.0


        scores[emotion] = max(
            0.0,
            value
        )


    total = sum(
        scores.values()
    )


    if total <= 0:
        return {}


    return {

        emotion:
        (
            value / total
        ) * 100.0

        for emotion, value
        in scores.items()

    }


# ============================================================
# EXTRACT DEEPFACE RESULT
# ============================================================

def extract_deepface_result(
    result
):

    if isinstance(
        result,
        list
    ):

        if not result:
            return None

        result = result[0]


    if not isinstance(
        result,
        dict
    ):
        return None


    raw_scores = result.get(
        "emotion"
    )


    if not raw_scores:
        return None


    scores = normalize_scores(
        raw_scores
    )


    if not scores:
        return None


    dominant = max(
        scores,
        key=scores.get
    )


    confidence = float(
        scores[dominant]
    )


    return (
        dominant,
        confidence,
        scores
    )


# ============================================================
# TEMPORAL SMOOTHING
# ============================================================

def smoothed_emotion():

    if not emotion_history:
        return "UNKNOWN"


    counts = Counter(
        emotion_history
    )


    return (
        counts
        .most_common(1)[0][0]
    )


# ============================================================
# EMOTION STABILITY
# ============================================================

def emotion_stability():

    if not emotion_history:
        return 0.0


    counts = Counter(
        emotion_history
    )


    dominant_count = (
        counts
        .most_common(1)[0][1]
    )


    return (
        dominant_count
        /
        len(emotion_history)
    ) * 100.0


# ============================================================
# REACTION TRACKING
# ============================================================

def update_reaction_state(
    emotion,
    current_time
):

    global previous_emotion
    global candidate_emotion
    global candidate_count
    global reaction_count
    global transition_count


    if previous_emotion is None:

        previous_emotion = emotion

        candidate_emotion = emotion

        candidate_count = 1

        return


    if candidate_emotion == emotion:

        candidate_count += 1

    else:

        candidate_emotion = emotion

        candidate_count = 1


    if (
        candidate_count
        <
        REACTION_CONFIRMATION
    ):
        return


    if (
        candidate_emotion
        !=
        previous_emotion
    ):

        transition_count += 1

        reaction_count += 1


        timeline.append({

            "time":
            round(
                float(
                    current_time
                ),
                3
            ),

            "from":
            previous_emotion,

            "to":
            candidate_emotion,

        })


        previous_emotion = (
            candidate_emotion
        )


# ============================================================
# RESULT
# ============================================================

def make_result(
    emotion="UNKNOWN",
    confidence=0.0,
    scores=None,
    valid=False,
    updated=False,
    error=None,
    quality=0.0
):

    if scores is None:
        scores = {}


    positive = sum(
        scores.get(
            e,
            0.0
        )
        for e
        in POSITIVE_EMOTIONS
    )


    negative = sum(
        scores.get(
            e,
            0.0
        )
        for e
        in NEGATIVE_EMOTIONS
    )


    return {

        "emotion":
        emotion,

        "dominant_emotion":
        emotion,

        "confidence":
        round(
            float(confidence),
            2
        ),

        "emotion_confidence":
        round(
            float(confidence),
            2
        ),

        "scores":
        scores,

        "face_quality":
        round(
            float(quality),
            2
        ),

        "stability":
        round(
            emotion_stability(),
            2
        ),

        "positive_score":
        round(
            positive,
            2
        ),

        "negative_score":
        round(
            negative,
            2
        ),

        "reaction_count":
        reaction_count,

        "transition_count":
        transition_count,

        "valid":
        valid,

        "updated":
        updated,

        "error":
        error,

    }


# ============================================================
# MAIN EMOTION DETECTOR
# ============================================================

def detect_emotion(
    frame,
    current_time=None
):

    global last_prediction_time

    global last_emotion
    global last_confidence
    global last_scores
    global last_error

    global valid_prediction_count
    global invalid_prediction_count


    if current_time is None:
        current_time = time.time()


    # ========================================================
    # THROTTLE
    # ========================================================

    if (
        current_time
        -
        last_prediction_time
        <
        ANALYSIS_INTERVAL
    ):

        return make_result(

            emotion=last_emotion,

            confidence=last_confidence,

            scores=last_scores.copy(),

            valid=bool(
                last_scores
            ),

            updated=False,

            error=last_error,

        )


    last_prediction_time = (
        current_time
    )


    # ========================================================
    # FRAME
    # ========================================================

    if not is_valid_frame(
        frame
    ):

        invalid_prediction_count += 1

        last_error = (
            "Invalid frame"
        )

        return make_result(
            error=last_error
        )


    # ========================================================
    # FACE DETECTION + RECOVERY
    # ========================================================

    try:

        face_crop = (
            detect_face_crop(
                frame,
                current_time
            )
        )

    except Exception as e:

        invalid_prediction_count += 1

        last_error = (
            f"Face detection error: "
            f"{type(e).__name__}: {e}"
        )

        return make_result(
            error=last_error
        )


    if face_crop is None:

        invalid_prediction_count += 1

        last_error = (
            "Face not detected"
        )

        return make_result(
            error=last_error
        )


    # ========================================================
    # FACE QUALITY
    # ========================================================

    quality = face_quality(
        face_crop
    )


    if quality < 20.0:

        invalid_prediction_count += 1

        last_error = (
            "Face quality too low"
        )

        return make_result(

            error=last_error,

            quality=quality

        )


    # ========================================================
    # DEEPFACE
    # ========================================================

    try:

        result = DeepFace.analyze(

            img_path=face_crop,

            actions=[
                "emotion"
            ],

            detector_backend="skip",

            enforce_detection=False,

            align=True,

            silent=True,

        )

    except Exception as e:

        invalid_prediction_count += 1

        last_error = (
            f"DeepFace error: "
            f"{type(e).__name__}: {e}"
        )

        return make_result(

            error=last_error,

            quality=quality

        )


    # ========================================================
    # PARSE
    # ========================================================

    extracted = (
        extract_deepface_result(
            result
        )
    )


    if extracted is None:

        invalid_prediction_count += 1

        last_error = (
            "No valid emotion probabilities"
        )

        return make_result(

            error=last_error,

            quality=quality

        )


    (
        detected_emotion,
        confidence,
        scores
    ) = extracted


    # ========================================================
    # LOW CONFIDENCE
    # ========================================================

    if (
        confidence
        <
        MIN_EMOTION_CONFIDENCE
    ):

        invalid_prediction_count += 1

        last_error = (
            "Low-confidence emotion prediction"
        )

        return make_result(

            emotion="UNKNOWN",

            confidence=confidence,

            scores=scores,

            valid=False,

            updated=False,

            error=last_error,

            quality=quality

        )


    # ========================================================
    # VALID
    # ========================================================

    valid_prediction_count += 1

    last_error = None


    emotion_history.append(
        detected_emotion
    )


    all_emotions.append(
        detected_emotion
    )


    all_confidences.append(
        confidence
    )


    all_scores.append(
        scores.copy()
    )


    final_emotion = (
        smoothed_emotion()
    )


    update_reaction_state(
        final_emotion,
        current_time
    )


    last_emotion = final_emotion

    last_confidence = confidence

    last_scores = scores.copy()


    return make_result(

        emotion=final_emotion,

        confidence=confidence,

        scores=scores,

        valid=True,

        updated=True,

        error=None,

        quality=quality

    )


# ============================================================
# SUMMARY
# ============================================================

def get_emotion_summary():

    total_valid = len(
        all_emotions
    )


    total_attempts = (
        valid_prediction_count
        +
        invalid_prediction_count
    )


    # --------------------------------------------------------
    # Nothing valid
    # --------------------------------------------------------

    if total_valid == 0:

        return {

            "predictions": 0,

            "valid_predictions":
            valid_prediction_count,

            "invalid_predictions":
            invalid_prediction_count,

            "face_detection_rate":
            0.0,

            "dominant_emotion":
            "unknown",

            "average_confidence":
            0.0,

            "stability":
            0.0,

            "positive_percentage":
            0.0,

            "neutral_percentage":
            0.0,

            "negative_percentage":
            0.0,

            "surprise_percentage":
            0.0,

            "reaction_count":
            reaction_count,

            "transition_count":
            transition_count,

            "timeline":
            timeline.copy(),

            "valid":
            False,

            "error":
            last_error,

        }


    # --------------------------------------------------------
    # Dominant
    # --------------------------------------------------------

    counts = Counter(
        all_emotions
    )


    dominant = (
        counts
        .most_common(1)[0][0]
    )


    # --------------------------------------------------------
    # Average confidence
    # --------------------------------------------------------

    average_confidence = (

        sum(
            all_confidences
        )
        /
        len(
            all_confidences
        )

    )


    # --------------------------------------------------------
    # Percentages
    # --------------------------------------------------------

    positive_count = sum(

        counts.get(
            e,
            0
        )

        for e
        in POSITIVE_EMOTIONS

    )


    negative_count = sum(

        counts.get(
            e,
            0
        )

        for e
        in NEGATIVE_EMOTIONS

    )


    neutral_count = counts.get(
        "neutral",
        0
    )


    surprise_count = counts.get(
        "surprise",
        0
    )


    detection_rate = (

        valid_prediction_count
        /
        total_attempts
        *
        100.0

        if total_attempts > 0
        else 0.0

    )


    # --------------------------------------------------------
    # Average score distribution
    # --------------------------------------------------------

    avg_scores = {}


    for emotion in EMOTIONS:

        values = [

            scores.get(
                emotion,
                0.0
            )

            for scores
            in all_scores

        ]


        avg_scores[emotion] = (

            sum(values)
            /
            len(values)

            if values
            else 0.0

        )


    return {

        "predictions":
        total_valid,

        "valid_predictions":
        valid_prediction_count,

        "invalid_predictions":
        invalid_prediction_count,

        "face_detection_rate":
        round(
            detection_rate,
            2
        ),

        "dominant_emotion":
        dominant,

        "average_confidence":
        round(
            average_confidence,
            2
        ),

        "stability":
        round(
            emotion_stability(),
            2
        ),

        "positive_percentage":
        round(
            positive_count
            /
            total_valid
            *
            100.0,
            2
        ),

        "neutral_percentage":
        round(
            neutral_count
            /
            total_valid
            *
            100.0,
            2
        ),

        "negative_percentage":
        round(
            negative_count
            /
            total_valid
            *
            100.0,
            2
        ),

        "surprise_percentage":
        round(
            surprise_count
            /
            total_valid
            *
            100.0,
            2
        ),

        "emotion_scores":
        {
            k:
            round(v, 2)
            for k, v
            in avg_scores.items()
        },

        "reaction_count":
        reaction_count,

        "transition_count":
        transition_count,

        "timeline":
        timeline.copy(),

        "valid":
        True,

        "error":
        last_error,

    }