import os
from collections import deque

import cv2
import mediapipe as mp
import numpy as np


# ============================================================
# MODEL
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
    "models",
    "face_landmarker.task",
)

if not os.path.isfile(MODEL_PATH):
    raise FileNotFoundError(
        f"Face landmark model not found:\n{MODEL_PATH}"
    )


# ============================================================
# MEDIAPIPE
# ============================================================

BaseOptions = mp.tasks.BaseOptions
RunningMode = mp.tasks.vision.RunningMode
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions

options = FaceLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),
    running_mode=RunningMode.IMAGE,
    num_faces=1,
    min_face_detection_confidence=0.40,
    min_face_presence_confidence=0.40,
    min_tracking_confidence=0.40,
    output_face_blendshapes=False,
    output_facial_transformation_matrixes=True,
)

face_landmarker = FaceLandmarker.create_from_options(options)


# ============================================================
# SMOOTHING
# ============================================================

YAW_HISTORY = deque(maxlen=5)
PITCH_HISTORY = deque(maxlen=5)
ROLL_HISTORY = deque(maxlen=5)
POSE_HISTORY = deque(maxlen=5)


# ============================================================
# LIMITS / THRESHOLDS
# ============================================================

MAX_YAW = 70.0
MAX_PITCH = 50.0
MAX_ROLL = 50.0

YAW_THRESHOLD = 15.0
PITCH_UP_THRESHOLD = -15.0
PITCH_DOWN_THRESHOLD = 15.0


# ============================================================
# RESET
# ============================================================

def reset_head_pose():
    YAW_HISTORY.clear()
    PITCH_HISTORY.clear()
    ROLL_HISTORY.clear()
    POSE_HISTORY.clear()


# ============================================================
# SAFE HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    try:
        value = float(value)

        if np.isfinite(value):
            return value

    except Exception:
        pass

    return default


def _smooth(history, value):
    history.append(
        _safe_float(value)
    )

    return float(
        np.median(
            np.asarray(
                history,
                dtype=np.float64
            )
        )
    )


def _stable_pose(pose):
    POSE_HISTORY.append(pose)

    counts = {}

    for item in POSE_HISTORY:
        counts[item] = (
            counts.get(item, 0) + 1
        )

    return max(
        counts,
        key=counts.get
    )


# ============================================================
# FACE QUALITY
# ============================================================

def _face_quality(landmarks):

    xs = np.asarray(
        [
            float(p.x)
            for p in landmarks
        ],
        dtype=np.float64
    )

    ys = np.asarray(
        [
            float(p.y)
            for p in landmarks
        ],
        dtype=np.float64
    )

    if xs.size == 0 or ys.size == 0:
        return 0.0

    min_x = float(np.min(xs))
    max_x = float(np.max(xs))

    min_y = float(np.min(ys))
    max_y = float(np.max(ys))

    width = max_x - min_x
    height = max_y - min_y

    area = width * height

    if area < 0.015:
        score = 35.0

    elif area < 0.03:
        score = 55.0

    elif area < 0.06:
        score = 75.0

    elif area < 0.10:
        score = 90.0

    else:
        score = 96.0

    margin = 0.02

    penalty = 0.0

    if min_x < margin:
        penalty += 8.0

    if max_x > 1.0 - margin:
        penalty += 8.0

    if min_y < margin:
        penalty += 8.0

    if max_y > 1.0 - margin:
        penalty += 8.0

    return float(
        np.clip(
            score - penalty,
            0.0,
            100.0
        )
    )


# ============================================================
# TRANSFORMATION MATRIX -> EULER
# ============================================================

def _extract_euler_angles(matrix):

    matrix = np.asarray(
        matrix,
        dtype=np.float64
    )

    if matrix.shape == (4, 4):

        rotation = matrix[:3, :3]

    elif matrix.shape == (3, 3):

        rotation = matrix

    else:

        raise ValueError(
            "Unexpected transformation "
            f"matrix shape: {matrix.shape}"
        )

    if not np.all(
        np.isfinite(rotation)
    ):
        raise ValueError(
            "Transformation matrix "
            "contains non-finite values"
        )

    # Small numerical correction.
    u, _, vt = np.linalg.svd(
        rotation
    )

    rotation = u @ vt

    if np.linalg.det(rotation) < 0:

        u[:, -1] *= -1.0

        rotation = u @ vt

    euler = cv2.RQDecomp3x3(
        rotation
    )[0]

    pitch = _safe_float(
        euler[0]
    )

    yaw = _safe_float(
        euler[1]
    )

    roll = _safe_float(
        euler[2]
    )

    return (
        pitch,
        yaw,
        roll
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def _classify(
    yaw,
    pitch
):

    if yaw < -YAW_THRESHOLD:
        return "Looking Left"

    if yaw > YAW_THRESHOLD:
        return "Looking Right"

    if pitch < PITCH_UP_THRESHOLD:
        return "Looking Up"

    if pitch > PITCH_DOWN_THRESHOLD:
        return "Looking Down"

    return "Center"


# ============================================================
# MAIN HEAD POSE FUNCTION
# ============================================================

def detect_head_pose(frame):

    try:

        if (
            frame is None
            or not isinstance(
                frame,
                np.ndarray
            )
        ):

            return {
                "pose": "Unknown",
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0,
                "confidence": 0.0,
                "detected": False,
            }

        if (
            frame.ndim != 3
            or frame.shape[0] < 40
            or frame.shape[1] < 40
        ):

            return {
                "pose": "Unknown",
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0,
                "confidence": 0.0,
                "detected": False,
            }

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=(
                mp.ImageFormat.SRGB
            ),
            data=rgb
        )

        result = face_landmarker.detect(
            mp_image
        )

        if not result.face_landmarks:

            return {
                "pose": "No face",
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0,
                "confidence": 0.0,
                "detected": False,
            }

        matrices = getattr(
            result,
            "facial_transformation_matrixes",
            None
        )

        if (
            matrices is None
            or len(matrices) == 0
        ):

            return {
                "pose": "Unknown",
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0,
                "confidence": 0.0,
                "detected": False,
            }

        landmarks = (
            result.face_landmarks[0]
        )

        pitch, yaw, roll = (
            _extract_euler_angles(
                matrices[0]
            )
        )

        # Reject impossible values.
        if (
            not np.isfinite(yaw)
            or not np.isfinite(pitch)
            or not np.isfinite(roll)
            or abs(yaw) > MAX_YAW
            or abs(pitch) > MAX_PITCH
            or abs(roll) > MAX_ROLL
        ):

            return {
                "pose": "Unknown",
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0,
                "confidence": 0.0,
                "detected": False,
            }

        smooth_yaw = _smooth(
            YAW_HISTORY,
            yaw
        )

        smooth_pitch = _smooth(
            PITCH_HISTORY,
            pitch
        )

        smooth_roll = _smooth(
            ROLL_HISTORY,
            roll
        )

        pose = _stable_pose(
            _classify(
                smooth_yaw,
                smooth_pitch
            )
        )

        quality = _face_quality(
            landmarks
        )

        # Extreme angles reduce reliability.
        if abs(smooth_yaw) > 45:
            quality -= 12.0

        if abs(smooth_pitch) > 35:
            quality -= 10.0

        if abs(smooth_roll) > 35:
            quality -= 5.0

        quality = float(
            np.clip(
                quality,
                0.0,
                100.0
            )
        )

        return {
            "pose": pose,

            "yaw": round(
                smooth_yaw,
                2
            ),

            "pitch": round(
                smooth_pitch,
                2
            ),

            "roll": round(
                smooth_roll,
                2
            ),

            "confidence": round(
                quality,
                1
            ),

            "detected": True,
        }

    except Exception as e:

        print(
            "[Head Pose Error] "
            f"{type(e).__name__}: {e}"
        )

        return {
            "pose": "Unknown",
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "confidence": 0.0,
            "detected": False,
        }