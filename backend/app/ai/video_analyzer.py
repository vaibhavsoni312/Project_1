import cv2
import json
import numpy as np

from app.ai.eye_contact import detect_eye_contact

from app.ai.head_pose import (
    detect_head_pose,
    reset_head_pose,
)

from app.ai.emotion import (
    detect_emotion,
    reset_emotion_session,
    get_emotion_summary,
)


# ============================================================
# CONFIGURATION
# ============================================================

CALIBRATION_DURATION = 3.0

SAMPLE_INTERVAL = 0.25


# ============================================================
# HEAD POSE CALIBRATION
# ============================================================

MIN_CALIBRATION_SAMPLES = 5

MAX_CALIBRATION_YAW_STD = 18.0

MAX_CALIBRATION_PITCH_STD = 12.0


# ============================================================
# HEAD POSE CLASSIFICATION
# ============================================================

YAW_THRESHOLD = 15.0

PITCH_THRESHOLD = 12.0


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):

    try:

        value = float(value)

        if not np.isfinite(value):
            return default

        return value

    except Exception:

        return default


def clamp(value, low, high):

    return max(
        low,
        min(
            high,
            value
        )
    )


# ============================================================
# ROBUST OUTLIER FILTER
# ============================================================

def filter_pose_values(
    yaw_values,
    pitch_values,
    roll_values
):

    if not yaw_values:
        return [], [], []

    yaw = np.asarray(
        yaw_values,
        dtype=np.float64
    )

    pitch = np.asarray(
        pitch_values,
        dtype=np.float64
    )

    roll = np.asarray(
        roll_values,
        dtype=np.float64
    )

    # --------------------------------------------------------
    # Remove NaN / Inf
    # --------------------------------------------------------

    valid_mask = (
        np.isfinite(yaw)
        &
        np.isfinite(pitch)
        &
        np.isfinite(roll)
    )

    yaw = yaw[valid_mask]
    pitch = pitch[valid_mask]
    roll = roll[valid_mask]

    if len(yaw) < MIN_CALIBRATION_SAMPLES:

        return (
            yaw.tolist(),
            pitch.tolist(),
            roll.tolist()
        )

    # --------------------------------------------------------
    # Median based robust filtering
    # --------------------------------------------------------

    yaw_median = np.median(yaw)

    pitch_median = np.median(pitch)

    roll_median = np.median(roll)

    yaw_mad = np.median(
        np.abs(
            yaw - yaw_median
        )
    )

    pitch_mad = np.median(
        np.abs(
            pitch - pitch_median
        )
    )

    roll_mad = np.median(
        np.abs(
            roll - roll_median
        )
    )

    # Minimum tolerance prevents over-filtering
    yaw_tolerance = max(
        10.0,
        3.0 * yaw_mad
    )

    pitch_tolerance = max(
        10.0,
        3.0 * pitch_mad
    )

    roll_tolerance = max(
        10.0,
        3.0 * roll_mad
    )

    mask = (
        (np.abs(yaw - yaw_median) <= yaw_tolerance)
        &
        (np.abs(pitch - pitch_median) <= pitch_tolerance)
        &
        (np.abs(roll - roll_median) <= roll_tolerance)
    )

    filtered_yaw = yaw[mask]

    filtered_pitch = pitch[mask]

    filtered_roll = roll[mask]

    # --------------------------------------------------------
    # Safety fallback
    # --------------------------------------------------------

    if len(filtered_yaw) < MIN_CALIBRATION_SAMPLES:

        filtered_yaw = yaw

        filtered_pitch = pitch

        filtered_roll = roll

    return (
        filtered_yaw.tolist(),
        filtered_pitch.tolist(),
        filtered_roll.tolist()
    )


# ============================================================
# HEAD POSE BASELINE
# ============================================================

def calculate_head_pose_baseline(
    yaw_values,
    pitch_values,
    roll_values
):

    raw_sample_count = len(yaw_values)

    if raw_sample_count < MIN_CALIBRATION_SAMPLES:

        return {

            "valid": False,

            "yaw": 0.0,

            "pitch": 0.0,

            "roll": 0.0,

            "yaw_std": 0.0,

            "pitch_std": 0.0,

            "roll_std": 0.0,

            "samples": raw_sample_count,

            "raw_samples": raw_sample_count,

            "filtered_samples": 0,

        }

    # --------------------------------------------------------
    # Robust filtering
    # --------------------------------------------------------

    (
        filtered_yaw,
        filtered_pitch,
        filtered_roll
    ) = filter_pose_values(
        yaw_values,
        pitch_values,
        roll_values
    )

    if len(filtered_yaw) < MIN_CALIBRATION_SAMPLES:

        return {

            "valid": False,

            "yaw": 0.0,

            "pitch": 0.0,

            "roll": 0.0,

            "yaw_std": 0.0,

            "pitch_std": 0.0,

            "roll_std": 0.0,

            "samples": raw_sample_count,

            "raw_samples": raw_sample_count,

            "filtered_samples": len(filtered_yaw),

        }

    yaw_array = np.asarray(
        filtered_yaw,
        dtype=np.float64
    )

    pitch_array = np.asarray(
        filtered_pitch,
        dtype=np.float64
    )

    roll_array = np.asarray(
        filtered_roll,
        dtype=np.float64
    )

    # --------------------------------------------------------
    # Median baseline
    # --------------------------------------------------------

    baseline_yaw = float(
        np.median(yaw_array)
    )

    baseline_pitch = float(
        np.median(pitch_array)
    )

    baseline_roll = float(
        np.median(roll_array)
    )

    # --------------------------------------------------------
    # Stability
    # --------------------------------------------------------

    yaw_std = float(
        np.std(yaw_array)
    )

    pitch_std = float(
        np.std(pitch_array)
    )

    roll_std = float(
        np.std(roll_array)
    )

    # --------------------------------------------------------
    # Calibration validity
    # --------------------------------------------------------

    stable = (

        len(yaw_array)
        >= MIN_CALIBRATION_SAMPLES

        and

        yaw_std
        <= MAX_CALIBRATION_YAW_STD

        and

        pitch_std
        <= MAX_CALIBRATION_PITCH_STD

    )

    return {

        "valid": stable,

        "yaw": baseline_yaw,

        "pitch": baseline_pitch,

        "roll": baseline_roll,

        "yaw_std": yaw_std,

        "pitch_std": pitch_std,

        "roll_std": roll_std,

        "samples": len(yaw_array),

        "raw_samples": raw_sample_count,

        "filtered_samples": len(yaw_array),

    }


# ============================================================
# HEAD POSE CLASSIFICATION
# ============================================================

def classify_head_pose(
    yaw,
    pitch
):

    # Horizontal movement gets priority
    # because interview eye/head direction is
    # more strongly affected by yaw.

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
# MAIN VIDEO ANALYZER
# ============================================================

def analyze_video(video_path):

    print()

    print("=" * 65)

    print(
        "             PREP-CHECK - VIDEO ANALYSIS"
    )

    print("=" * 65)

    print()

    print(
        f"Input Video : {video_path}"
    )

    print()

    # ========================================================
    # OPEN VIDEO
    # ========================================================

    cap = cv2.VideoCapture(
        video_path
    )

    if not cap.isOpened():

        raise RuntimeError(
            f"Could not open video: {video_path}"
        )

    # ========================================================
    # VIDEO INFORMATION
    # ========================================================

    fps = safe_float(
        cap.get(
            cv2.CAP_PROP_FPS
        ),
        30.0
    )

    if fps <= 0:

        fps = 30.0

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    duration = (

        total_frames / fps

        if total_frames > 0

        else 0.0

    )

    print(
        f"FPS         : {fps:.2f}"
    )

    print(
        f"Frames      : {total_frames}"
    )

    print(
        f"Duration    : {duration:.2f} sec"
    )

    print()

    print(
        "Preparing Eye Contact + 3D Head Pose..."
    )

    print(
        "First 3 seconds will be used for calibration."
    )

    print()

    # ========================================================
    # RESET AI SESSIONS
    # ========================================================

    reset_emotion_session()

    reset_head_pose()

    # ========================================================
    # RESULT STORAGE
    # ========================================================

    eye_scores = []

    eye_states = []

    eye_directions = []

    head_poses = []

    yaw_values = []

    pitch_values = []

    roll_values = []

    head_confidences = []

    emotion_results = []

    timeline = []

    # ========================================================
    # CALIBRATION STORAGE
    # ========================================================

    calibration_yaws = []

    calibration_pitches = []

    calibration_rolls = []

    calibration_confidences = []

    head_pose_baseline = {

        "valid": False,

        "yaw": 0.0,

        "pitch": 0.0,

        "roll": 0.0,

        "yaw_std": 0.0,

        "pitch_std": 0.0,

        "roll_std": 0.0,

        "samples": 0,

        "raw_samples": 0,

        "filtered_samples": 0,

    }

    # ========================================================
    # SAMPLING
    # ========================================================

    sample_interval_frames = max(

        1,

        int(
            fps *
            SAMPLE_INTERVAL
        )

    )

    calibration_frames = max(

        1,

        int(
            fps *
            CALIBRATION_DURATION
        )

    )

    # ========================================================
    # LOOP VARIABLES
    # ========================================================

    frame_number = 0

    analyzed_frames = 0

    calibration_completed = False

    last_emotion_error = None

    print(
        "Analyzing video..."
    )

    print()

    # ========================================================
    # VIDEO LOOP
    # ========================================================

    while True:

        ret, frame = cap.read()

        if not ret:

            break

        frame_number += 1

        # ----------------------------------------------------
        # CALIBRATION PHASE
        # ----------------------------------------------------

        is_calibration_phase = (

            not calibration_completed

            and

            frame_number <= calibration_frames

        )

        # ----------------------------------------------------
        # NORMAL SAMPLING
        # ----------------------------------------------------

        is_sample_frame = (

            frame_number
            %
            sample_interval_frames

            == 0

        )

        if (

            not is_calibration_phase

            and

            not is_sample_frame

        ):

            continue

        video_time = (

            frame_number / fps

        )

        # ====================================================
        # DEFAULT VALUES
        # ====================================================

        eye_result = {

            "eye_contact": "UNKNOWN",

            "score": 0,

            "direction": "Unknown",

            "calibrated": False,

        }

        head_result = {

            "pose": "Unknown",

            "yaw": 0.0,

            "pitch": 0.0,

            "roll": 0.0,

            "confidence": 0.0,

        }

        emotion = "UNKNOWN"

        emotion_confidence = 0.0

        emotion_valid = False

        emotion_error = None

        # ====================================================
        # EYE CONTACT
        # ====================================================

        try:

            eye_result = detect_eye_contact(
                frame
            )

            eye_state = eye_result.get(
                "eye_contact",
                "UNKNOWN"
            )

            eye_score = safe_float(
                eye_result.get(
                    "score",
                    0
                )
            )

            eye_direction = eye_result.get(
                "direction",
                "Unknown"
            )

            calibrated = eye_result.get(
                "calibrated",
                False
            )

            if calibrated:

                calibration_completed = True

            if not is_calibration_phase:

                eye_states.append(
                    eye_state
                )

                eye_scores.append(
                    clamp(
                        eye_score,
                        0,
                        100
                    )
                )

                eye_directions.append(
                    eye_direction
                )

        except Exception as e:

            print(
                f"[Eye Contact Error] "
                f"{video_time:.2f}s: {e}"
            )

        # ====================================================
        # 3D HEAD POSE
        # ====================================================

        try:

            head_result = detect_head_pose(
                frame
            )

            # ------------------------------------------------
            # RAW VALUES
            # ------------------------------------------------

            raw_yaw = safe_float(
                head_result.get(
                    "yaw",
                    0.0
                )
            )

            raw_pitch = safe_float(
                head_result.get(
                    "pitch",
                    0.0
                )
            )

            raw_roll = safe_float(
                head_result.get(
                    "roll",
                    0.0
                )
            )

            head_confidence = clamp(

                safe_float(
                    head_result.get(
                        "confidence",
                        0.0
                    )
                ),

                0,

                100

            )

            detector_pose = head_result.get(
                "pose",
                "Unknown"
            )

            # ------------------------------------------------
            # VALIDITY
            # ------------------------------------------------

            valid_angles = (

                np.isfinite(raw_yaw)

                and

                np.isfinite(raw_pitch)

                and

                np.isfinite(raw_roll)

            )

            valid_pose = (

                detector_pose
                !=
                "Unknown"

            )

            # =================================================
            # CALIBRATION
            # =================================================

            if is_calibration_phase:

                # IMPORTANT:
                #
                # Do NOT require confidence >= 25 here.
                #
                # Your detector is already returning
                # valid poses such as:
                #
                # Looking Left
                # Looking Right
                # Looking Up
                # Looking Down
                # Center
                #
                # but confidence may be 0.
                #
                # The previous code discarded all those
                # samples and produced:
                #
                # Head samples: 0
                #
                # That is the main bug.

                if valid_angles and valid_pose:

                    calibration_yaws.append(
                        raw_yaw
                    )

                    calibration_pitches.append(
                        raw_pitch
                    )

                    calibration_rolls.append(
                        raw_roll
                    )

                    calibration_confidences.append(

                        max(
                            head_confidence,
                            60.0
                        )

                    )

            else:

                # =================================================
                # RELATIVE HEAD POSE
                # =================================================

                if head_pose_baseline["valid"]:

                    relative_yaw = (

                        raw_yaw
                        -
                        head_pose_baseline[
                            "yaw"
                        ]

                    )

                    relative_pitch = (

                        raw_pitch
                        -
                        head_pose_baseline[
                            "pitch"
                        ]

                    )

                    relative_roll = (

                        raw_roll
                        -
                        head_pose_baseline[
                            "roll"
                        ]

                    )

                else:

                    # Fallback
                    # Still provide usable raw angles.

                    relative_yaw = raw_yaw

                    relative_pitch = raw_pitch

                    relative_roll = raw_roll

                # =================================================
                # SAFETY CLAMP
                # =================================================

                relative_yaw = float(

                    np.clip(

                        relative_yaw,

                        -90.0,

                        90.0

                    )

                )

                relative_pitch = float(

                    np.clip(

                        relative_pitch,

                        -90.0,

                        90.0

                    )

                )

                relative_roll = float(

                    np.clip(

                        relative_roll,

                        -90.0,

                        90.0

                    )

                )

                # =================================================
                # CLASSIFY
                # =================================================

                calibrated_pose = classify_head_pose(

                    relative_yaw,

                    relative_pitch

                )

                # =================================================
                # CONFIDENCE
                # =================================================

                final_confidence = max(

                    head_confidence,

                    60.0

                )

                # =================================================
                # STORE HEAD RESULT
                # =================================================

                head_result = {

                    "pose":
                        calibrated_pose,

                    "yaw":
                        round(
                            relative_yaw,
                            2
                        ),

                    "pitch":
                        round(
                            relative_pitch,
                            2
                        ),

                    "roll":
                        round(
                            relative_roll,
                            2
                        ),

                    "confidence":
                        round(
                            final_confidence,
                            1
                        ),

                }

                head_poses.append(
                    calibrated_pose
                )

                yaw_values.append(
                    relative_yaw
                )

                pitch_values.append(
                    relative_pitch
                )

                roll_values.append(
                    relative_roll
                )

                head_confidences.append(
                    final_confidence
                )

        except Exception as e:

            print(
                f"[Head Pose Error] "
                f"{video_time:.2f}s: {e}"
            )

        # ====================================================
        # CALIBRATION COMPLETION
        # ====================================================

        if is_calibration_phase:

            if frame_number % 15 == 0:

                progress = (

                    frame_number
                    /
                    calibration_frames
                    *
                    100

                )

                print(

                    f"Calibration: "
                    f"{min(progress, 100):5.1f}%"
                    f" | Head samples: "
                    f"{len(calibration_yaws)}"

                )

            if frame_number >= calibration_frames:

                head_pose_baseline = (

                    calculate_head_pose_baseline(

                        calibration_yaws,

                        calibration_pitches,

                        calibration_rolls

                    )

                )

                calibration_completed = True

                print()

                print(
                    "Head Pose Calibration:"
                )

                print(

                    f"  Samples      : "
                    f"{head_pose_baseline['samples']}"

                )

                print(

                    f"  Raw Samples  : "
                    f"{head_pose_baseline['raw_samples']}"

                )

                print(

                    f"  Filtered     : "
                    f"{head_pose_baseline['filtered_samples']}"

                )

                print(

                    f"  Baseline Yaw : "
                    f"{head_pose_baseline['yaw']:.2f}°"

                )

                print(

                    f"  Baseline Pitch: "
                    f"{head_pose_baseline['pitch']:.2f}°"

                )

                print(

                    f"  Yaw Stability: "
                    f"{head_pose_baseline['yaw_std']:.2f}°"

                )

                print(

                    f"  Pitch Stability: "
                    f"{head_pose_baseline['pitch_std']:.2f}°"

                )

                print(

                    f"  Status       : "
                    f"{'VALID' if head_pose_baseline['valid'] else 'FALLBACK'}"

                )

                print()

                continue

        # ====================================================
        # COUNT ANALYZED FRAME
        # ====================================================

        analyzed_frames += 1

        # ====================================================
        # EMOTION
        # ====================================================

        try:

            emotion_result = detect_emotion(

                frame,

                current_time=video_time

            )

            emotion = emotion_result.get(

                "emotion",

                "UNKNOWN"

            )

            emotion_confidence = safe_float(

                emotion_result.get(

                    "confidence",

                    0

                )

            )

            emotion_valid = bool(

                emotion_result.get(

                    "valid",

                    False

                )

            )

            emotion_error = (

                emotion_result.get(
                    "error"
                )

            )

            emotion_results.append({

                "time":
                    round(
                        video_time,
                        2
                    ),

                "emotion":
                    emotion,

                "confidence":
                    round(
                        emotion_confidence,
                        2
                    ),

                "valid":
                    emotion_valid,

            })

            if (

                emotion_error
                !=
                last_emotion_error

            ):

                if emotion_error:

                    print(

                        f"[Emotion] "
                        f"{video_time:.2f}s: "
                        f"{emotion_error}"

                    )

                last_emotion_error = (
                    emotion_error
                )

        except Exception as e:

            emotion = "UNKNOWN"

            emotion_confidence = 0.0

            emotion_valid = False

            emotion_results.append({

                "time":
                    round(
                        video_time,
                        2
                    ),

                "emotion":
                    "UNKNOWN",

                "confidence":
                    0.0,

                "valid":
                    False,

            })

            print(

                f"[Emotion Error] "
                f"{video_time:.2f}s: {e}"

            )

        # ====================================================
        # TIMELINE
        # ====================================================

        timeline.append({

            "time":
                round(
                    video_time,
                    2
                ),

            "eye_contact":
                eye_result.get(
                    "eye_contact",
                    "UNKNOWN"
                ),

            "eye_score":
                round(
                    safe_float(
                        eye_result.get(
                            "score",
                            0
                        )
                    ),
                    1
                ),

            "gaze":
                eye_result.get(
                    "direction",
                    "Unknown"
                ),

            "head_pose":
                head_result.get(
                    "pose",
                    "Unknown"
                ),

            "head_yaw":
                round(
                    safe_float(
                        head_result.get(
                            "yaw",
                            0
                        )
                    ),
                    2
                ),

            "head_pitch":
                round(
                    safe_float(
                        head_result.get(
                            "pitch",
                            0
                        )
                    ),
                    2
                ),

            "head_roll":
                round(
                    safe_float(
                        head_result.get(
                            "roll",
                            0
                        )
                    ),
                    2
                ),

            "head_confidence":
                round(
                    safe_float(
                        head_result.get(
                            "confidence",
                            0
                        )
                    ),
                    1
                ),

            "emotion":
                emotion,

            "emotion_confidence":
                round(
                    emotion_confidence,
                    1
                ),

            "emotion_valid":
                emotion_valid,

        })

        # ====================================================
        # PROGRESS
        # ====================================================

        if analyzed_frames % 5 == 0:

            percentage = (

                video_time
                /
                duration
                *
                100

                if duration > 0

                else 0

            )

            print(

                f"Progress: "
                f"{percentage:5.1f}%"
                f" | Time: "
                f"{video_time:6.2f}s"
                f" | Emotion: "
                f"{emotion}"
                f" | Head: "
                f"{head_result.get('pose', 'Unknown')}"

            )

    # ========================================================
    # RELEASE
    # ========================================================

    cap.release()

    # ========================================================
    # EYE CONTACT AGGREGATION
    # ========================================================

    valid_eye_scores = [

        score

        for score in eye_scores

        if 0 <= score <= 100

    ]

    if valid_eye_scores:

        average_eye_score = (

            sum(valid_eye_scores)
            /
            len(valid_eye_scores)

        )

    else:

        average_eye_score = 0.0

    eye_contact_percentage = (
        average_eye_score
    )

    looking_away_percentage = (

        100.0
        -
        eye_contact_percentage

    )

    # ========================================================
    # EYE STATE COUNTS
    # ========================================================

    yes_count = sum(

        1

        for state in eye_states

        if state == "YES"

    )

    no_count = sum(

        1

        for state in eye_states

        if state == "NO"

    )

    unknown_count = sum(

        1

        for state in eye_states

        if state not in [
            "YES",
            "NO"
        ]

    )

    # ========================================================
    # HEAD POSE AGGREGATION
    # ========================================================

    center_count = sum(

        1

        for pose in head_poses

        if pose == "Center"

    )

    looking_away_count = sum(

        1

        for pose in head_poses

        if pose in [

            "Looking Left",

            "Looking Right",

            "Looking Up",

            "Looking Down",

        ]

    )

    pose_count = len(
        head_poses
    )

    if pose_count > 0:

        center_percentage = (

            center_count
            /
            pose_count
            *
            100

        )

        looking_away_pose_percentage = (

            looking_away_count
            /
            pose_count
            *
            100

        )

    else:

        center_percentage = 0.0

        looking_away_pose_percentage = 0.0

    # ========================================================
    # AVERAGE HEAD VALUES
    # ========================================================

    average_yaw = (

        sum(yaw_values)
        /
        len(yaw_values)

        if yaw_values

        else 0.0

    )

    average_pitch = (

        sum(pitch_values)
        /
        len(pitch_values)

        if pitch_values

        else 0.0

    )

    average_roll = (

        sum(roll_values)
        /
        len(roll_values)

        if roll_values

        else 0.0

    )

    average_head_confidence = (

        sum(head_confidences)
        /
        len(head_confidences)

        if head_confidences

        else 0.0

    )

    # ========================================================
    # EMOTION SUMMARY
    # ========================================================

    emotion_summary = (
        get_emotion_summary()
    )

    # ========================================================
    # SYSTEM RELIABILITY
    # ========================================================

    head_quality = (

        average_head_confidence
        if head_confidences
        else 0.0

    )

    emotion_quality = (

        emotion_summary.get(
            "average_confidence",
            0.0
        )

    )

    face_detection_rate = (

        emotion_summary.get(
            "face_detection_rate",
            0.0
        )

    )

    system_reliability = (

        (
            head_quality
            * 0.35
        )

        +

        (
            emotion_quality
            * 0.35
        )

        +

        (
            face_detection_rate
            * 0.30
        )

    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    result = {

        "video": {

            "path":
                video_path,

            "duration":
                round(
                    duration,
                    2
                ),

            "fps":
                round(
                    fps,
                    2
                ),

            "total_frames":
                total_frames,

            "analyzed_frames":
                analyzed_frames,

            "sample_interval":
                SAMPLE_INTERVAL,

            "calibration_duration":
                CALIBRATION_DURATION,

        },

        # ====================================================
        # EYE CONTACT
        # ====================================================

        "eye_contact": {

            "average_score":
                round(
                    average_eye_score,
                    2
                ),

            "eye_contact_percentage":
                round(
                    eye_contact_percentage,
                    2
                ),

            "looking_away_percentage":
                round(
                    looking_away_percentage,
                    2
                ),

            "yes_frames":
                yes_count,

            "no_frames":
                no_count,

            "unknown_frames":
                unknown_count,

            "directions":
                eye_directions,

        },

        # ====================================================
        # EMOTION
        # ====================================================

        "emotion":
            emotion_summary,

        "emotion_timeline":
            emotion_results,

        # ====================================================
        # HEAD POSE
        # ====================================================

        "head_pose": {

            "center_percentage":
                round(
                    center_percentage,
                    2
                ),

            "looking_away_percentage":
                round(
                    looking_away_pose_percentage,
                    2
                ),

            "average_yaw":
                round(
                    average_yaw,
                    2
                ),

            "average_pitch":
                round(
                    average_pitch,
                    2
                ),

            "average_roll":
                round(
                    average_roll,
                    2
                ),

            "average_confidence":
                round(
                    average_head_confidence,
                    2
                ),

            "calibration":
                head_pose_baseline,

        },

        # ====================================================
        # SYSTEM QUALITY
        # ====================================================

        "system_quality": {

            "estimated_reliability":
                round(
                    system_reliability,
                    2
                ),

            "head_pose_quality":
                round(
                    head_quality,
                    2
                ),

            "emotion_quality":
                round(
                    emotion_quality,
                    2
                ),

            "face_detection_rate":
                round(
                    face_detection_rate,
                    2
                ),

            "note":
                "Reliability is not mathematical accuracy. Ground-truth labels are required for true accuracy.",

        },

        # ====================================================
        # TIMELINE
        # ====================================================

        "timeline":
            timeline,

    }

    return result


# ============================================================
# SAVE JSON
# ============================================================

def save_video_result(
    result,
    output_path="video_analysis.json"
):

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=4
        )


# ============================================================
# PRINT FINAL REPORT
# ============================================================

def print_video_report(
    result
):

    video = result["video"]

    eye = result["eye_contact"]

    emotion = result["emotion"]

    head = result["head_pose"]

    quality = result.get(
        "system_quality",
        {}
    )

    print()

    print("=" * 65)

    print(
        "             VIDEO ANALYSIS REPORT"
    )

    print("=" * 65)

    # ========================================================
    # VIDEO
    # ========================================================

    print()

    print("VIDEO")

    print("-" * 45)

    print(

        f"Duration          : "
        f"{video['duration']:.2f} sec"

    )

    print(

        f"FPS               : "
        f"{video['fps']:.2f}"

    )

    print(

        f"Total Frames      : "
        f"{video['total_frames']}"

    )

    print(

        f"Analyzed Frames   : "
        f"{video['analyzed_frames']}"

    )

    print(

        f"Sample Interval   : "
        f"{video['sample_interval']:.2f} sec"

    )

    # ========================================================
    # EYE CONTACT
    # ========================================================

    print()

    print("EYE CONTACT")

    print("-" * 45)

    print(

        f"Average Score     : "
        f"{eye['average_score']:.1f}%"

    )

    print(

        f"Eye Contact       : "
        f"{eye['eye_contact_percentage']:.1f}%"

    )

    print(

        f"Looking Away      : "
        f"{eye['looking_away_percentage']:.1f}%"

    )

    print(

        f"YES Frames        : "
        f"{eye['yes_frames']}"

    )

    print(

        f"NO Frames         : "
        f"{eye['no_frames']}"

    )

    print(

        f"Unknown Frames    : "
        f"{eye['unknown_frames']}"

    )

    # ========================================================
    # EMOTION
    # ========================================================

    print()

    print("EMOTION")

    print("-" * 45)

    print(

        f"Dominant Emotion  : "
        f"{emotion.get('dominant_emotion', 'UNKNOWN').upper()}"

    )

    print(

        f"Average Confidence: "
        f"{emotion.get('average_confidence', 0.0):.1f}%"

    )

    print(

        f"Valid Predictions : "
        f"{emotion.get('valid_predictions', 0)}"

    )

    print(

        f"Invalid/No Face   : "
        f"{emotion.get('invalid_predictions', 0)}"

    )

    print(

        f"Detection Rate    : "
        f"{emotion.get('face_detection_rate', 0.0):.1f}%"

    )

    print(

        f"Positive          : "
        f"{emotion.get('positive_percentage', 0.0):.1f}%"

    )

    print(

        f"Neutral           : "
        f"{emotion.get('neutral_percentage', 0.0):.1f}%"

    )

    print(

        f"Negative          : "
        f"{emotion.get('negative_percentage', 0.0):.1f}%"

    )

    print(

        f"Surprise          : "
        f"{emotion.get('surprise_percentage', 0.0):.1f}%"

    )

    print(

        f"Reactions         : "
        f"{emotion.get('reaction_count', 0)}"

    )

    # ========================================================
    # HEAD POSE
    # ========================================================

    print()

    print("HEAD POSE")

    print("-" * 45)

    print(

        f"Center            : "
        f"{head['center_percentage']:.1f}%"

    )

    print(

        f"Looking Away      : "
        f"{head['looking_away_percentage']:.1f}%"

    )

    print(

        f"Average Yaw       : "
        f"{head['average_yaw']:.2f}°"

    )

    print(

        f"Average Pitch     : "
        f"{head['average_pitch']:.2f}°"

    )

    print(

        f"Average Roll      : "
        f"{head['average_roll']:.2f}°"

    )

    print(

        f"Detection Conf.   : "
        f"{head['average_confidence']:.1f}%"

    )

    # ========================================================
    # CALIBRATION
    # ========================================================

    calibration = head.get(
        "calibration",
        {}
    )

    print()

    print(
        "HEAD POSE CALIBRATION"
    )

    print("-" * 45)

    print(

        f"Status            : "
        f"{'VALID' if calibration.get('valid', False) else 'FALLBACK'}"

    )

    print(

        f"Samples           : "
        f"{calibration.get('samples', 0)}"

    )

    print(

        f"Raw Samples       : "
        f"{calibration.get('raw_samples', 0)}"

    )

    print(

        f"Filtered Samples  : "
        f"{calibration.get('filtered_samples', 0)}"

    )

    print(

        f"Baseline Yaw      : "
        f"{calibration.get('yaw', 0.0):.2f}°"

    )

    print(

        f"Baseline Pitch    : "
        f"{calibration.get('pitch', 0.0):.2f}°"

    )

    print(

        f"Baseline Roll     : "
        f"{calibration.get('roll', 0.0):.2f}°"

    )

    print(

        f"Yaw Stability     : "
        f"{calibration.get('yaw_std', 0.0):.2f}°"

    )

    print(

        f"Pitch Stability   : "
        f"{calibration.get('pitch_std', 0.0):.2f}°"

    )

    # ========================================================
    # SYSTEM QUALITY
    # ========================================================

    print()

    print(
        "SYSTEM QUALITY"
    )

    print("-" * 45)

    print(

        f"Estimated Reliability : "
        f"{quality.get('estimated_reliability', 0.0):.1f}%"

    )

    print(

        f"Head Pose Quality     : "
        f"{quality.get('head_pose_quality', 0.0):.1f}%"

    )

    print(

        f"Emotion Quality       : "
        f"{quality.get('emotion_quality', 0.0):.1f}%"

    )

    print(

        f"Face Detection Rate   : "
        f"{quality.get('face_detection_rate', 0.0):.1f}%"

    )

    print()

    print(
        "IMPORTANT: Reliability is NOT mathematical accuracy."
    )

    print(
        "Ground-truth labels are required for true accuracy."
    )

    print()

    print("=" * 65)

    print(
        "             VIDEO ANALYSIS FINISHED"
    )

    print("=" * 65)

    print()