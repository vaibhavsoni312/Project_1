import cv2
import math
import numpy as np
import mediapipe as mp

from pathlib import Path
from collections import deque


# ============================================================
# MODEL PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "face_landmarker.task"
)

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Face landmark model not found:\n{MODEL_PATH}"
    )


# ============================================================
# MEDIAPIPE
# ============================================================

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
        model_asset_path=str(
            MODEL_PATH
        )
    ),

    running_mode=RunningMode.IMAGE,

    num_faces=1,

    min_face_detection_confidence=0.50,

    min_face_presence_confidence=0.50,

    min_tracking_confidence=0.50,

    output_face_blendshapes=False,

    output_facial_transformation_matrixes=True,
)


landmarker = (
    FaceLandmarker.create_from_options(
        options
    )
)


# ============================================================
# SMOOTHING
# ============================================================

SMOOTHING_WINDOW = 5

yaw_history = deque(
    maxlen=SMOOTHING_WINDOW
)

pitch_history = deque(
    maxlen=SMOOTHING_WINDOW
)

roll_history = deque(
    maxlen=SMOOTHING_WINDOW
)


# ============================================================
# RESET
# ============================================================

def reset_head_pose():

    yaw_history.clear()

    pitch_history.clear()

    roll_history.clear()


# ============================================================
# HELPERS
# ============================================================

def clamp(
    value,
    minimum,
    maximum
):

    return max(
        minimum,
        min(
            maximum,
            value
        )
    )


def safe_float(
    value,
    default=0.0
):

    try:

        value = float(value)

        if not np.isfinite(value):

            return default

        return value

    except Exception:

        return default


# ============================================================
# MATRIX → NUMPY
# ============================================================

def matrix_to_numpy(
    matrix
):

    """
    MediaPipe transformation matrix
    ko safely 4x4 numpy matrix mein convert karta hai.
    """

    try:

        # --------------------------------------------
        # MediaPipe matrix object
        # --------------------------------------------

        if hasattr(
            matrix,
            "data"
        ):

            data = np.asarray(
                matrix.data,
                dtype=np.float64
            )

            if data.size == 16:

                return data.reshape(
                    4,
                    4
                )


        # --------------------------------------------
        # List / numpy array
        # --------------------------------------------

        data = np.asarray(
            matrix,
            dtype=np.float64
        )

        if data.size == 16:

            return data.reshape(
                4,
                4
            )

    except Exception:

        return None

    return None


# ============================================================
# ROTATION MATRIX → EULER
# ============================================================

def rotation_matrix_to_euler(
    rotation
):

    """
    Returns:

        yaw
        pitch
        roll

    in degrees.
    """

    try:

        r00 = float(
            rotation[0, 0]
        )

        r01 = float(
            rotation[0, 1]
        )

        r02 = float(
            rotation[0, 2]
        )

        r10 = float(
            rotation[1, 0]
        )

        r11 = float(
            rotation[1, 1]
        )

        r12 = float(
            rotation[1, 2]
        )

        r20 = float(
            rotation[2, 0]
        )

        r21 = float(
            rotation[2, 1]
        )

        r22 = float(
            rotation[2, 2]
        )


        # --------------------------------------------
        # Numerical stability
        # --------------------------------------------

        sy = math.sqrt(
            r00 * r00
            +
            r10 * r10
        )

        singular = (
            sy < 1e-6
        )


        # --------------------------------------------
        # Normal case
        # --------------------------------------------

        if not singular:

            x = math.atan2(
                r21,
                r22
            )

            y = math.atan2(
                -r20,
                sy
            )

            z = math.atan2(
                r10,
                r00
            )


        # --------------------------------------------
        # Gimbal lock
        # --------------------------------------------

        else:

            x = math.atan2(
                -r12,
                r11
            )

            y = math.atan2(
                -r20,
                sy
            )

            z = 0.0


        roll = math.degrees(
            x
        )

        pitch = math.degrees(
            y
        )

        yaw = math.degrees(
            z
        )


        return (
            yaw,
            pitch,
            roll
        )

    except Exception:

        return (
            0.0,
            0.0,
            0.0
        )


# ============================================================
# ANGLE NORMALIZATION
# ============================================================

def normalize_angle(
    angle
):

    angle = safe_float(
        angle
    )

    while angle > 180.0:

        angle -= 360.0

    while angle < -180.0:

        angle += 360.0

    return angle


# ============================================================
# SMOOTHING
# ============================================================

def smooth_angles(
    yaw,
    pitch,
    roll
):

    yaw_history.append(
        yaw
    )

    pitch_history.append(
        pitch
    )

    roll_history.append(
        roll
    )


    # Median is resistant to
    # occasional noisy frames.

    smooth_yaw = float(
        np.median(
            list(
                yaw_history
            )
        )
    )

    smooth_pitch = float(
        np.median(
            list(
                pitch_history
            )
        )
    )

    smooth_roll = float(
        np.median(
            list(
                roll_history
            )
        )
    )


    return (
        smooth_yaw,
        smooth_pitch,
        smooth_roll
    )


# ============================================================
# MATRIX QUALITY
# ============================================================

def matrix_quality(
    matrix
):

    """
    Checks whether the 3x3 part behaves
    reasonably like a rotation matrix.

    This is QUALITY, not model accuracy.
    """

    try:

        rotation = matrix[
            :3,
            :3
        ]


        if not np.all(
            np.isfinite(
                rotation
            )
        ):

            return 0.0


        determinant = abs(
            np.linalg.det(
                rotation
            )
        )


        orthogonality_error = np.linalg.norm(
            (
                rotation.T
                @
                rotation
            )
            -
            np.eye(3)
        )


        # --------------------------------------------
        # Score
        # --------------------------------------------

        score = 100.0


        if determinant < 0.5:

            score -= 20.0

        elif determinant > 2.0:

            score -= 15.0


        if orthogonality_error > 1.0:

            score -= 20.0

        elif orthogonality_error > 0.5:

            score -= 10.0


        return clamp(
            score,
            0.0,
            100.0
        )

    except Exception:

        return 0.0


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(
    matrix,
    yaw,
    pitch,
    roll
):

    """
    IMPORTANT:

    Analyzer accepts calibration samples when
    confidence >= 25.

    Previous implementation could produce
    artificially low confidence even when
    MediaPipe successfully returned a valid
    transformation matrix.

    This version therefore treats a valid
    transformation matrix + finite angles as
    a strong detection.

    This number is RELIABILITY/QUALITY,
    NOT mathematical accuracy.
    """

    if matrix is None:

        return 0.0


    try:

        if not np.all(
            np.isfinite(
                matrix
            )
        ):

            return 0.0


        if not all(
            np.isfinite(
                value
            )
            for value in (
                yaw,
                pitch,
                roll
            )
        ):

            return 0.0


        quality = matrix_quality(
            matrix
        )


        # ------------------------------------------------
        # Valid MediaPipe matrix itself is strong evidence
        # ------------------------------------------------

        confidence = (
            70.0
            +
            (
                quality
                *
                0.25
            )
        )


        # ------------------------------------------------
        # Extreme angles are still valid detections,
        # but slightly reduce confidence.
        # ------------------------------------------------

        if abs(yaw) > 80.0:

            confidence -= 8.0

        if abs(pitch) > 75.0:

            confidence -= 8.0

        if abs(roll) > 75.0:

            confidence -= 5.0


        confidence = clamp(
            confidence,
            40.0,
            98.0
        )


        return confidence

    except Exception:

        return 0.0


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_head_pose(
    yaw,
    pitch
):

    """
    Raw head pose.

    NOTE:
    video_analyzer.py later converts this into
    relative head pose using calibration baseline.
    """

    YAW_THRESHOLD = 15.0

    PITCH_THRESHOLD = 12.0


    # Horizontal priority.

    if yaw < -YAW_THRESHOLD:

        return "Looking Left"


    if yaw > YAW_THRESHOLD:

        return "Looking Right"


    if pitch < -PITCH_THRESHOLD:

        return "Looking Up"


    if pitch > PITCH_THRESHOLD:

        return "Looking Down"


    return "Center"


# ============================================================
# MAIN
# ============================================================

def detect_head_pose(
    frame
):

    """
    Detect 3D head pose using MediaPipe
    facial transformation matrix.

    Returns:

    {
        "pose": str,
        "yaw": float,
        "pitch": float,
        "roll": float,
        "confidence": float
    }
    """


    # ========================================================
    # INVALID FRAME
    # ========================================================

    if frame is None:

        return {
            "pose": "Unknown",
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "confidence": 0.0
        }


    # ========================================================
    # BGR → RGB
    # ========================================================

    try:

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

    except Exception:

        return {
            "pose": "Unknown",
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "confidence": 0.0
        }


    # ========================================================
    # MEDIAPIPE IMAGE
    # ========================================================

    try:

        image = mp.Image(
            image_format=(
                mp.ImageFormat.SRGB
            ),
            data=rgb
        )

    except Exception:

        return {
            "pose": "Unknown",
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "confidence": 0.0
        }


    # ========================================================
    # DETECTION
    # ========================================================

    try:

        result = landmarker.detect(
            image
        )

    except Exception as e:

        print(
            f"[Head Pose Detection Error] {e}"
        )

        return {
            "pose": "Unknown",
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "confidence": 0.0
        }


    # ========================================================
    # NO FACE
    # ========================================================

    if (
        result is None
        or
        not result.face_landmarks
    ):

        return {
            "pose": "Unknown",
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "confidence": 0.0
        }


    # ========================================================
    # TRANSFORMATION MATRICES
    # ========================================================

    matrices = getattr(
        result,
        "facial_transformation_matrixes",
        None
    )


    if matrices is None:

        return {
            "pose": "Unknown",
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "confidence": 0.0
        }


    try:

        if len(matrices) == 0:

            return {
                "pose": "Unknown",
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0,
                "confidence": 0.0
            }

    except Exception:

        return {
            "pose": "Unknown",
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "confidence": 0.0
        }


    # ========================================================
    # MATRIX
    # ========================================================

    matrix = matrix_to_numpy(
        matrices[0]
    )


    if matrix is None:

        return {
            "pose": "Unknown",
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "confidence": 0.0
        }


    # ========================================================
    # ROTATION
    # ========================================================

    rotation = matrix[
        :3,
        :3
    ]


    # ========================================================
    # EULER ANGLES
    # ========================================================

    (
        yaw,
        pitch,
        roll
    ) = rotation_matrix_to_euler(
        rotation
    )


    # ========================================================
    # NORMALIZE
    # ========================================================

    yaw = normalize_angle(
        yaw
    )

    pitch = normalize_angle(
        pitch
    )

    roll = normalize_angle(
        roll
    )


    # ========================================================
    # CLAMP
    # ========================================================

    yaw = clamp(
        yaw,
        -90.0,
        90.0
    )

    pitch = clamp(
        pitch,
        -90.0,
        90.0
    )

    roll = clamp(
        roll,
        -90.0,
        90.0
    )


    # ========================================================
    # SMOOTH
    # ========================================================

    (
        smooth_yaw,
        smooth_pitch,
        smooth_roll
    ) = smooth_angles(
        yaw,
        pitch,
        roll
    )


    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = calculate_confidence(
        matrix,
        smooth_yaw,
        smooth_pitch,
        smooth_roll
    )


    # ========================================================
    # POSE
    # ========================================================

    pose = classify_head_pose(
        smooth_yaw,
        smooth_pitch
    )


    # ========================================================
    # RETURN
    # ========================================================

    return {

        "pose":
            pose,

        "yaw":
            round(
                smooth_yaw,
                2
            ),

        "pitch":
            round(
                smooth_pitch,
                2
            ),

        "roll":
            round(
                smooth_roll,
                2
            ),

        "confidence":
            round(
                confidence,
                1
            )
    }