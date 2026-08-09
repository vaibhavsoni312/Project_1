import cv2
import mediapipe as mp

from pathlib import Path
from collections import deque


# =========================================================
# MODEL PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = BASE_DIR / "models" / "face_landmarker.task"


if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Face landmark model not found:\n{MODEL_PATH}"
    )


# =========================================================
# MEDIAPIPE TASKS
# =========================================================

BaseOptions = mp.tasks.BaseOptions

FaceLandmarker = (
    mp.tasks.vision.FaceLandmarker
)

FaceLandmarkerOptions = (
    mp.tasks.vision.FaceLandmarkerOptions
)

RunningMode = (
    mp.tasks.vision.RunningMode
)


options = FaceLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path=str(MODEL_PATH)
    ),

    running_mode=RunningMode.IMAGE,

    num_faces=1,

    min_face_detection_confidence=0.5,

    min_face_presence_confidence=0.5,

    min_tracking_confidence=0.5
)


landmarker = FaceLandmarker.create_from_options(
    options
)


# =========================================================
# EYE LANDMARKS
# =========================================================

LEFT_OUTER = 33
LEFT_INNER = 133

RIGHT_INNER = 362
RIGHT_OUTER = 263

LEFT_TOP = 159
LEFT_BOTTOM = 145

RIGHT_TOP = 386
RIGHT_BOTTOM = 374


LEFT_IRIS = [
    468,
    469,
    470,
    471,
    472
]


RIGHT_IRIS = [
    473,
    474,
    475,
    476,
    477
]


# =========================================================
# CALIBRATION
# =========================================================
#
# 90 frames at 30 FPS ~= 3 seconds.
#
# This matches video_analyzer.py which uses the
# first 3 seconds for calibration.
# =========================================================

CALIBRATION_FRAMES = 90

calibration_samples = []

calibrated = False

baseline_x = 0.5
baseline_y = 0.5


# =========================================================
# SMOOTHING
# =========================================================

gaze_history = deque(
    maxlen=7
)

state_history = deque(
    maxlen=7
)


# =========================================================
# CURRENT STATE
# =========================================================

current_state = "CALIBRATING"

current_direction = "Look at camera"

current_score = 0.0


# =========================================================
# AVERAGE LANDMARK POINT
# =========================================================

def average_point(
    landmarks,
    indices
):

    x = 0.0
    y = 0.0
    z = 0.0

    for index in indices:

        point = landmarks[index]

        x += point.x
        y += point.y
        z += point.z

    count = len(indices)

    return (
        x / count,
        y / count,
        z / count
    )


# =========================================================
# GET EYE POSITION
# =========================================================

def get_eye_position(
    landmarks,
    outer_index,
    inner_index,
    top_index,
    bottom_index,
    iris_indices
):

    outer = landmarks[outer_index]
    inner = landmarks[inner_index]

    top = landmarks[top_index]
    bottom = landmarks[bottom_index]


    iris_x, iris_y, _ = average_point(
        landmarks,
        iris_indices
    )


    left = min(
        outer.x,
        inner.x
    )

    right = max(
        outer.x,
        inner.x
    )


    top_y = min(
        top.y,
        bottom.y
    )

    bottom_y = max(
        top.y,
        bottom.y
    )


    width = right - left

    height = bottom_y - top_y


    if width < 0.001:
        return None

    if height < 0.001:
        return None


    normalized_x = (
        iris_x - left
    ) / width


    normalized_y = (
        iris_y - top_y
    ) / height


    return (
        normalized_x,
        normalized_y
    )


# =========================================================
# CALCULATE GAZE
# =========================================================

def calculate_gaze(
    landmarks
):

    left_eye = get_eye_position(
        landmarks,

        LEFT_OUTER,
        LEFT_INNER,

        LEFT_TOP,
        LEFT_BOTTOM,

        LEFT_IRIS
    )


    right_eye = get_eye_position(
        landmarks,

        RIGHT_INNER,
        RIGHT_OUTER,

        RIGHT_TOP,
        RIGHT_BOTTOM,

        RIGHT_IRIS
    )


    if left_eye is None:
        return None

    if right_eye is None:
        return None


    x = (
        left_eye[0]
        +
        right_eye[0]
    ) / 2.0


    y = (
        left_eye[1]
        +
        right_eye[1]
    ) / 2.0


    return (
        x,
        y
    )


# =========================================================
# SMOOTH GAZE
# =========================================================

def smooth_gaze(
    x,
    y
):

    gaze_history.append(
        (x, y)
    )


    smooth_x = sum(
        point[0]
        for point in gaze_history
    ) / len(gaze_history)


    smooth_y = sum(
        point[1]
        for point in gaze_history
    ) / len(gaze_history)


    return (
        smooth_x,
        smooth_y
    )


# =========================================================
# STABLE STATE
# =========================================================

def get_stable_state(
    new_state
):

    global current_state

    state_history.append(
        new_state
    )


    yes_count = state_history.count(
        "YES"
    )

    no_count = state_history.count(
        "NO"
    )


    # Strong YES majority
    if yes_count >= 4:

        return "YES"


    # Strong NO majority
    if no_count >= 4:

        return "NO"


    # During the first few frames after
    # calibration, don't return CALIBRATING.
    if current_state not in (
        "YES",
        "NO"
    ):

        return new_state


    # Otherwise maintain previous stable state.
    return current_state


# =========================================================
# FULL FACE VISIBILITY
# =========================================================

def check_face_visibility(
    landmarks
):

    xs = [
        point.x
        for point in landmarks
    ]


    ys = [
        point.y
        for point in landmarks
    ]


    min_x = min(xs)
    max_x = max(xs)

    min_y = min(ys)
    max_y = max(ys)


    # Small margin around frame.
    margin = 0.025


    cropped = (
        min_x < margin
        or
        max_x > (1.0 - margin)
        or
        min_y < margin
        or
        max_y > (1.0 - margin)
    )


    return (
        not cropped,
        min_x,
        max_x,
        min_y,
        max_y
    )


# =========================================================
# RESET SESSION
# =========================================================

def reset_eye_contact_session():

    global calibrated
    global baseline_x
    global baseline_y

    global current_state
    global current_direction
    global current_score


    calibration_samples.clear()

    gaze_history.clear()

    state_history.clear()


    calibrated = False

    baseline_x = 0.5
    baseline_y = 0.5


    current_state = "CALIBRATING"

    current_direction = "Look at camera"

    current_score = 0.0


# =========================================================
# MAIN FUNCTION
# =========================================================

def detect_eye_contact(
    frame
):

    global calibrated

    global baseline_x
    global baseline_y

    global current_state
    global current_direction
    global current_score


    if frame is None:

        return {
            "eye_contact": "UNKNOWN",
            "score": 0.0,
            "direction": "No frame",
            "calibrated": calibrated
        }


    # =====================================================
    # BGR -> RGB
    # =====================================================

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )


    # =====================================================
    # FACE LANDMARK DETECTION
    # =====================================================

    result = landmarker.detect(
        image
    )


    # =====================================================
    # NO FACE
    # =====================================================

    if not result.face_landmarks:

        current_state = "UNKNOWN"

        current_direction = "No face"

        current_score = 0.0


        return {
            "eye_contact": "UNKNOWN",
            "score": 0.0,
            "direction": "No face",
            "calibrated": calibrated
        }


    landmarks = result.face_landmarks[0]


    # =====================================================
    # FACE VISIBILITY
    # =====================================================

    (
        face_visible,
        face_x1,
        face_x2,
        face_y1,
        face_y2
    ) = check_face_visibility(
        landmarks
    )


    if not face_visible:

        current_state = "UNKNOWN"

        current_direction = "Face cropped"

        current_score = 0.0


        return {
            "eye_contact": "UNKNOWN",
            "score": 0.0,
            "direction": "Face cropped",
            "calibrated": calibrated
        }


    # =====================================================
    # GAZE
    # =====================================================

    gaze = calculate_gaze(
        landmarks
    )


    if gaze is None:

        current_state = "UNKNOWN"

        current_direction = "Eyes unavailable"

        current_score = 0.0


        return {
            "eye_contact": "UNKNOWN",
            "score": 0.0,
            "direction": "Eyes unavailable",
            "calibrated": calibrated
        }


    gaze_x, gaze_y = gaze


    # =====================================================
    # SMOOTH
    # =====================================================

    smooth_x, smooth_y = smooth_gaze(
        gaze_x,
        gaze_y
    )


    # =====================================================
    # CALIBRATION
    # =====================================================

    if not calibrated:

        calibration_samples.append(
            (
                smooth_x,
                smooth_y
            )
        )


        progress = int(
            (
                len(calibration_samples)
                /
                CALIBRATION_FRAMES
            )
            * 100
        )


        # -------------------------------------------------
        # CALIBRATION COMPLETE
        # -------------------------------------------------

        if len(calibration_samples) >= CALIBRATION_FRAMES:

            baseline_x = sum(
                x
                for x, y
                in calibration_samples
            ) / len(
                calibration_samples
            )


            baseline_y = sum(
                y
                for x, y
                in calibration_samples
            ) / len(
                calibration_samples
            )


            calibrated = True


            print()
            print(
                "=============================================="
            )
            print(
                "        EYE CONTACT V7 CALIBRATION DONE"
            )
            print(
                "=============================================="
            )

            print(
                f"Baseline X : {baseline_x:.4f}"
            )

            print(
                f"Baseline Y : {baseline_y:.4f}"
            )

            print()


        current_state = "CALIBRATING"

        current_direction = "Look at camera"

        current_score = 0.0


        return {
            "eye_contact": "CALIBRATING",

            "score": 0.0,

            "direction": "Look at camera",

            "calibrated": False,

            "calibration_progress": min(
                progress,
                100
            )
        }


    # =====================================================
    # DISTANCE FROM CALIBRATION BASELINE
    # =====================================================

    dx = (
        smooth_x
        -
        baseline_x
    )


    dy = (
        smooth_y
        -
        baseline_y
    )


    abs_dx = abs(dx)

    abs_dy = abs(dy)


    # =====================================================
    # THRESHOLDS
    # =====================================================
    #
    # Slightly relaxed so normal eye movement
    # isn't immediately treated as looking away.
    #

    HORIZONTAL_THRESHOLD = 0.15

    VERTICAL_THRESHOLD = 0.20


    # =====================================================
    # GAZE CLASSIFICATION
    # =====================================================

    if (
        abs_dx <= HORIZONTAL_THRESHOLD
        and
        abs_dy <= VERTICAL_THRESHOLD
    ):

        raw_state = "YES"

        direction = "Camera"


    else:

        raw_state = "NO"


        # -----------------------------------------------
        # LEFT / RIGHT
        # -----------------------------------------------

        if abs_dx > abs_dy:

            if dx < 0:

                direction = "Right"

            else:

                direction = "Left"


        # -----------------------------------------------
        # UP / DOWN
        # -----------------------------------------------

        else:

            if dy < 0:

                direction = "Down"

            else:

                direction = "Up"


    # =====================================================
    # STABILITY FILTER
    # =====================================================

    final_state = get_stable_state(
        raw_state
    )


    # =====================================================
    # V7 SCORE
    # =====================================================

    horizontal_error = (
        abs_dx
        /
        HORIZONTAL_THRESHOLD
    )


    vertical_error = (
        abs_dy
        /
        VERTICAL_THRESHOLD
    )


    # Weighted error.
    #
    # Horizontal gaze movement is more important
    # than small vertical movement.
    #

    error = (
        0.65 * horizontal_error
        +
        0.35 * vertical_error
    )


    error = min(
        error,
        1.0
    )


    score = (
        100.0
        *
        (
            1.0
            -
            error
        )
    )


    # =====================================================
    # NATURAL EYE MOVEMENT BOOST
    # =====================================================

    if (
        abs_dx <= 0.05
        and
        abs_dy <= 0.07
    ):

        score = max(
            score,
            92.0
        )


    elif (
        abs_dx <= 0.08
        and
        abs_dy <= 0.10
    ):

        score = max(
            score,
            82.0
        )


    elif (
        abs_dx <= 0.11
        and
        abs_dy <= 0.14
    ):

        score = max(
            score,
            70.0
        )


    # =====================================================
    # STATE BASED SCORE
    # =====================================================

    if final_state == "YES":

        if (
            abs_dx <= 0.05
            and
            abs_dy <= 0.07
        ):

            score = max(
                score,
                92.0
            )


        elif (
            abs_dx <= 0.08
            and
            abs_dy <= 0.10
        ):

            score = max(
                score,
                82.0
            )


        else:

            score = max(
                score,
                70.0
            )


    elif final_state == "NO":

        score = min(
            score,
            55.0
        )


    else:

        score = min(
            score,
            60.0
        )


    score = max(
        0.0,
        min(
            100.0,
            score
        )
    )


    # =====================================================
    # FACE BOX
    # =====================================================

    h, w, _ = frame.shape


    x1 = max(
        0,
        int(face_x1 * w)
    )


    x2 = min(
        w - 1,
        int(face_x2 * w)
    )


    y1 = max(
        0,
        int(face_y1 * h)
    )


    y2 = min(
        h - 1,
        int(face_y2 * h)
    )


    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )


    # =====================================================
    # IRIS POINTS
    # =====================================================

    for index in (
        LEFT_IRIS
        +
        RIGHT_IRIS
    ):

        point = landmarks[index]


        px = int(
            point.x * w
        )


        py = int(
            point.y * h
        )


        cv2.circle(
            frame,
            (px, py),
            2,
            (255, 0, 0),
            -1
        )


    # =====================================================
    # DISPLAY COLOR
    # =====================================================

    if final_state == "YES":

        display_color = (
            0,
            255,
            0
        )


    elif final_state == "NO":

        display_color = (
            0,
            0,
            255
        )


    else:

        display_color = (
            0,
            255,
            255
        )


    # =====================================================
    # DISPLAY
    # =====================================================

    cv2.putText(
        frame,

        f"Eye Contact: {int(score)}%",

        (30, 45),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.8,

        display_color,

        2
    )


    cv2.putText(
        frame,

        f"Gaze: {direction}",

        (30, 80),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.75,

        (0, 255, 255),

        2
    )


    cv2.putText(
        frame,

        "Calibration: READY",

        (30, 115),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.7,

        (255, 255, 0),

        2
    )


    # =====================================================
    # SAVE STATE
    # =====================================================

    current_state = final_state

    current_direction = direction

    current_score = score


    # =====================================================
    # RETURN RESULT
    # =====================================================

    return {

        "eye_contact": final_state,

        "score": round(
            score,
            1
        ),

        "direction": direction,

        "calibrated": True,

        "gaze_x": round(
            smooth_x,
            4
        ),

        "gaze_y": round(
            smooth_y,
            4
        ),

        "baseline_x": round(
            baseline_x,
            4
        ),

        "baseline_y": round(
            baseline_y,
            4
        )
    }