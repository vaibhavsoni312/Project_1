import cv2
import mediapipe as mp

from pathlib import Path
from collections import deque
from statistics import median


# ============================================================
# MODEL
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "face_landmarker.task"

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Face landmark model not found: {MODEL_PATH}"
    )


# ============================================================
# MEDIAPIPE
# ============================================================

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode


options = FaceLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path=str(MODEL_PATH)
    ),
    running_mode=RunningMode.IMAGE,
    num_faces=1,
    min_face_detection_confidence=0.55,
    min_face_presence_confidence=0.55,
    min_tracking_confidence=0.55,
)

landmarker = FaceLandmarker.create_from_options(options)


# ============================================================
# LANDMARKS
# ============================================================

LEFT_OUTER = 33
LEFT_INNER = 133
LEFT_TOP = 159
LEFT_BOTTOM = 145

RIGHT_INNER = 362
RIGHT_OUTER = 263
RIGHT_TOP = 386
RIGHT_BOTTOM = 374

LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]


# ============================================================
# SESSION
# ============================================================

CALIBRATION_FRAMES = 90

calibration_samples = []

calibrated = False

baseline_x = 0.5
baseline_y = 0.5

gaze_history = deque(maxlen=7)
state_history = deque(maxlen=7)

current_state = "CALIBRATING"


# ============================================================
# HELPERS
# ============================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def avg_point(landmarks, indices):

    points = []

    for i in indices:
        if i < len(landmarks):
            p = landmarks[i]
            points.append((p.x, p.y, p.z))

    if not points:
        return None

    return (
        sum(p[0] for p in points) / len(points),
        sum(p[1] for p in points) / len(points),
        sum(p[2] for p in points) / len(points),
    )


def eye_position(
    landmarks,
    outer,
    inner,
    top,
    bottom,
    iris
):

    try:
        p_outer = landmarks[outer]
        p_inner = landmarks[inner]
        p_top = landmarks[top]
        p_bottom = landmarks[bottom]
    except IndexError:
        return None

    iris_point = avg_point(
        landmarks,
        iris
    )

    if iris_point is None:
        return None

    left = min(
        p_outer.x,
        p_inner.x
    )

    right = max(
        p_outer.x,
        p_inner.x
    )

    top_y = min(
        p_top.y,
        p_bottom.y
    )

    bottom_y = max(
        p_top.y,
        p_bottom.y
    )

    width = right - left
    height = bottom_y - top_y

    if width < 0.003:
        return None

    if height < 0.003:
        return None

    x = (
        iris_point[0] - left
    ) / width

    y = (
        iris_point[1] - top_y
    ) / height

    return x, y


def calculate_gaze(landmarks):

    left = eye_position(
        landmarks,
        LEFT_OUTER,
        LEFT_INNER,
        LEFT_TOP,
        LEFT_BOTTOM,
        LEFT_IRIS
    )

    right = eye_position(
        landmarks,
        RIGHT_INNER,
        RIGHT_OUTER,
        RIGHT_TOP,
        RIGHT_BOTTOM,
        RIGHT_IRIS
    )

    if left is None or right is None:
        return None

    return (
        (left[0] + right[0]) / 2,
        (left[1] + right[1]) / 2
    )


def smooth_gaze(x, y):

    gaze_history.append(
        (x, y)
    )

    xs = [
        p[0]
        for p in gaze_history
    ]

    ys = [
        p[1]
        for p in gaze_history
    ]

    return (
        median(xs),
        median(ys)
    )


def robust_baseline(samples):

    if len(samples) < 15:
        return None

    xs = [
        p[0]
        for p in samples
    ]

    ys = [
        p[1]
        for p in samples
    ]

    mx = median(xs)
    my = median(ys)

    filtered = []

    for x, y in samples:

        distance = (
            abs(x - mx)
            +
            abs(y - my)
        )

        if distance <= 0.22:
            filtered.append(
                (x, y)
            )

    if len(filtered) < 15:
        filtered = samples

    return (
        median(
            [p[0] for p in filtered]
        ),
        median(
            [p[1] for p in filtered]
        )
    )


def stable_state(state):

    global current_state

    state_history.append(state)

    yes = state_history.count("YES")
    no = state_history.count("NO")
    unknown = state_history.count("UNKNOWN")

    if unknown >= 5:
        current_state = "UNKNOWN"
        return current_state

    if yes >= 4:
        current_state = "YES"
        return current_state

    if no >= 4:
        current_state = "NO"
        return current_state

    if current_state in (
        "YES",
        "NO"
    ):
        return current_state

    return state


# ============================================================
# RESET
# ============================================================

def reset_eye_contact_session():

    global calibrated
    global baseline_x
    global baseline_y
    global current_state

    calibration_samples.clear()
    gaze_history.clear()
    state_history.clear()

    calibrated = False

    baseline_x = 0.5
    baseline_y = 0.5

    current_state = "CALIBRATING"


# ============================================================
# MAIN
# ============================================================

def detect_eye_contact(
    frame,
    head_result=None
):

    global calibrated
    global baseline_x
    global baseline_y

    # ========================================================
    # INVALID FRAME
    # ========================================================

    if frame is None:

        return {
            "eye_contact": "UNKNOWN",
            "score": 0.0,
            "direction": "No frame",
            "calibrated": calibrated,
            "fusion": False
        }

    # ========================================================
    # RGB
    # ========================================================

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    result = landmarker.detect(image)

    # ========================================================
    # NO FACE
    # ========================================================

    if not result.face_landmarks:

        return {
            "eye_contact": "UNKNOWN",
            "score": 0.0,
            "direction": "No face",
            "calibrated": calibrated,
            "fusion": False
        }

    landmarks = result.face_landmarks[0]

    # ========================================================
    # GAZE
    # ========================================================

    gaze = calculate_gaze(
        landmarks
    )

    if gaze is None:

        return {
            "eye_contact": "UNKNOWN",
            "score": 0.0,
            "direction": "Eyes unavailable",
            "calibrated": calibrated,
            "fusion": False
        }

    gx, gy = smooth_gaze(
        gaze[0],
        gaze[1]
    )

    # ========================================================
    # CALIBRATION
    # ========================================================

    if not calibrated:

        calibration_samples.append(
            (gx, gy)
        )

        if len(calibration_samples) >= CALIBRATION_FRAMES:

            baseline = robust_baseline(
                calibration_samples
            )

            if baseline is not None:

                baseline_x = baseline[0]
                baseline_y = baseline[1]

                calibrated = True

                print()
                print(
                    "Eye Contact V9 Calibration:"
                )
                print(
                    f"Baseline X : {baseline_x:.4f}"
                )
                print(
                    f"Baseline Y : {baseline_y:.4f}"
                )
                print(
                    f"Samples    : {len(calibration_samples)}"
                )
                print()

        return {
            "eye_contact": "CALIBRATING",
            "score": 0.0,
            "direction": "Calibrating",
            "calibrated": calibrated,
            "fusion": False
        }

    # ========================================================
    # IRIS ERROR
    # ========================================================

    iris_dx = gx - baseline_x
    iris_dy = gy - baseline_y

    iris_x_error = abs(iris_dx)
    iris_y_error = abs(iris_dy)

    # ========================================================
    # IRIS SCORE
    # ========================================================

    iris_horizontal = clamp(
        iris_x_error / 0.19,
        0.0,
        1.0
    )

    iris_vertical = clamp(
        iris_y_error / 0.23,
        0.0,
        1.0
    )

    iris_error = (
        0.70 * iris_horizontal
        +
        0.30 * iris_vertical
    )

    iris_score = (
        100.0
        *
        (1.0 - iris_error)
    )

    # ========================================================
    # HEAD POSE FUSION
    # ========================================================

    head_available = (
        isinstance(
            head_result,
            dict
        )
    )

    if head_available:

        try:

            head_yaw = float(
                head_result.get(
                    "yaw",
                    0.0
                )
            )

            head_pitch = float(
                head_result.get(
                    "pitch",
                    0.0
                )
            )

            head_confidence = float(
                head_result.get(
                    "confidence",
                    0.0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            head_available = False

    # ========================================================
    # HEAD SCORE
    # ========================================================

    if head_available:

        yaw_error = clamp(
            abs(head_yaw) / 25.0,
            0.0,
            1.0
        )

        pitch_error = clamp(
            abs(head_pitch) / 20.0,
            0.0,
            1.0
        )

        head_error = (
            0.70 * yaw_error
            +
            0.30 * pitch_error
        )

        head_score = (
            100.0
            *
            (1.0 - head_error)
        )

    else:

        head_score = 50.0
        head_confidence = 0.0

    # ========================================================
    # FUSION
    # ========================================================

    if head_available and head_confidence >= 40:

        # Iris remains primary.
        #
        # Head pose prevents iris-only false positives.
        final_score = (
            0.60 * iris_score
            +
            0.40 * head_score
        )

    elif head_available:

        final_score = (
            0.75 * iris_score
            +
            0.25 * head_score
        )

    else:

        final_score = iris_score

    final_score = clamp(
        final_score,
        0.0,
        100.0
    )

    # ========================================================
    # CLASSIFICATION
    # ========================================================

    # Strong head-away signal.
    head_away = False

    if head_available:

        head_away = (
            abs(head_yaw) >= 25.0
            or
            abs(head_pitch) >= 20.0
        )

    # Strong iris-away signal.
    iris_away = (
        iris_x_error >= 0.19
        or
        iris_y_error >= 0.23
    )

    # Camera.
    if (
        final_score >= 68
        and
        not head_away
    ):

        raw_state = "YES"
        direction = "Camera"

    # Definitely away.
    elif (
        final_score < 42
        and
        (
            iris_away
            or
            head_away
        )
    ):

        raw_state = "NO"

        if head_available and abs(head_yaw) >= 25:

            if head_yaw > 0:
                direction = "Left"
            else:
                direction = "Right"

        elif abs(iris_dx) > abs(iris_dy):

            if iris_dx > 0:
                direction = "Left"
            else:
                direction = "Right"

        else:

            if iris_dy > 0:
                direction = "Down"
            else:
                direction = "Up"

    else:

        # Borderline movement is not immediately
        # classified as looking away.
        raw_state = "YES"
        direction = "Slight movement"

    final_state = stable_state(
        raw_state
    )

    # ========================================================
    # FINAL SCORE SAFETY
    # ========================================================

    if final_state == "YES":

        final_score = max(
            final_score,
            65.0
        )

    elif final_state == "NO":

        final_score = min(
            final_score,
            55.0
        )

    elif final_state == "UNKNOWN":

        final_score = 0.0

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "eye_contact": final_state,

        "score": round(
            final_score,
            1
        ),

        "direction": direction,

        "calibrated": True,

        "gaze_x": round(
            gx,
            4
        ),

        "gaze_y": round(
            gy,
            4
        ),

        "baseline_x": round(
            baseline_x,
            4
        ),

        "baseline_y": round(
            baseline_y,
            4
        ),

        "iris_score": round(
            iris_score,
            1
        ),

        "head_score": round(
            head_score,
            1
        ),

        "head_confidence": round(
            head_confidence,
            1
        ),

        "fusion": head_available
    }