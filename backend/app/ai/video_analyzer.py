import cv2
import json
import sys
import numpy as np

from app.ai.eye_contact import (
    detect_eye_contact
)

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
# CONFIG
# ============================================================

CALIBRATION_DURATION = 3.0
SAMPLE_INTERVAL = 0.25

MIN_CALIBRATION_SAMPLES = 20

MAD_SCALE = 3.5

MAX_CALIBRATION_YAW_STD = 15.0
MAX_CALIBRATION_PITCH_STD = 12.0
MAX_CALIBRATION_ROLL_STD = 10.0


# ============================================================
# HELPERS
# ============================================================

def safe_float(
    value,
    default=0.0
):

    try:

        value = float(value)

        if np.isfinite(value):
            return value

    except Exception:
        pass

    return default


def clamp(
    value,
    low,
    high
):

    return max(
        low,
        min(high, value)
    )


def robust_filter(values):

    arr = np.asarray(
        values,
        dtype=np.float64
    )

    if arr.size == 0:
        return arr

    median = np.median(arr)

    deviation = np.abs(
        arr - median
    )

    mad = np.median(
        deviation
    )

    if mad < 1e-6:
        return arr

    robust_sigma = (
        1.4826 * mad
    )

    limit = (
        MAD_SCALE
        * robust_sigma
    )

    filtered = arr[
        np.abs(
            arr - median
        ) <= limit
    ]

    if (
        filtered.size
        < max(
            5,
            int(arr.size * 0.50)
        )
    ):
        return arr

    return filtered


# ============================================================
# HEAD CALIBRATION
# ============================================================

def calculate_head_pose_baseline(
    yaw_values,
    pitch_values,
    roll_values,
    confidence_values
):

    raw_count = len(
        yaw_values
    )

    if (
        raw_count
        < MIN_CALIBRATION_SAMPLES
    ):

        return {
            "valid": False,
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "yaw_std": 0.0,
            "pitch_std": 0.0,
            "roll_std": 0.0,
            "samples": 0,
            "raw_samples": raw_count,
            "filtered_samples": 0,
            "average_confidence": 0.0,
        }

    yaw = robust_filter(
        yaw_values
    )

    pitch = robust_filter(
        pitch_values
    )

    roll = robust_filter(
        roll_values
    )

    n = min(
        len(yaw),
        len(pitch),
        len(roll)
    )

    if (
        n
        < MIN_CALIBRATION_SAMPLES
    ):

        return {
            "valid": False,
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "yaw_std": 0.0,
            "pitch_std": 0.0,
            "roll_std": 0.0,
            "samples": 0,
            "raw_samples": raw_count,
            "filtered_samples": n,
            "average_confidence": 0.0,
        }

    yaw = yaw[:n]
    pitch = pitch[:n]
    roll = roll[:n]

    baseline_yaw = float(
        np.median(yaw)
    )

    baseline_pitch = float(
        np.median(pitch)
    )

    baseline_roll = float(
        np.median(roll)
    )

    yaw_std = float(
        np.std(yaw)
    )

    pitch_std = float(
        np.std(pitch)
    )

    roll_std = float(
        np.std(roll)
    )

    conf = np.asarray(
        confidence_values,
        dtype=np.float64
    )

    average_confidence = (
        float(np.mean(conf))
        if conf.size
        else 0.0
    )

    stable = (
        yaw_std
        <= MAX_CALIBRATION_YAW_STD
        and pitch_std
        <= MAX_CALIBRATION_PITCH_STD
        and roll_std
        <= MAX_CALIBRATION_ROLL_STD
    )

    return {
        "valid": bool(stable),
        "yaw": baseline_yaw,
        "pitch": baseline_pitch,
        "roll": baseline_roll,
        "yaw_std": yaw_std,
        "pitch_std": pitch_std,
        "roll_std": roll_std,
        "samples": n,
        "raw_samples": raw_count,
        "filtered_samples": n,
        "average_confidence": average_confidence,
    }


# ============================================================
# MAIN ANALYZER
# ============================================================

def analyze_video(
    video_path
):

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

    cap = cv2.VideoCapture(
        video_path
    )

    if not cap.isOpened():

        raise RuntimeError(
            "Could not open video: "
            f"{video_path}"
        )

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

    reset_emotion_session()
    reset_head_pose()

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
        "average_confidence": 0.0,
    }

    sample_interval_frames = max(
        1,
        int(
            fps
            * SAMPLE_INTERVAL
        )
    )

    calibration_frames = max(
        1,
        int(
            fps
            * CALIBRATION_DURATION
        )
    )

    frame_number = 0
    analyzed_frames = 0

    head_calibration_completed = False

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
        # HEAD CALIBRATION IS INDEPENDENT
        # ----------------------------------------------------

        is_head_calibration = (
            not head_calibration_completed
            and
            frame_number <= calibration_frames
        )

        is_sample_frame = (
            frame_number
            % sample_interval_frames
            == 0
        )

        if (
            not is_head_calibration
            and
            not is_sample_frame
        ):
            continue

        video_time = (
            frame_number / fps
        )

        eye_result = {
            "eye_contact": "UNKNOWN",
            "score": 0.0,
            "direction": "Unknown",
            "calibrated": False,
        }

        head_result = {
            "pose": "Unknown",
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "confidence": 0.0,
            "detected": False,
        }

        emotion = "UNKNOWN"
        emotion_confidence = 0.0
        emotion_valid = False

        # ====================================================
        # EYE CONTACT
        # ====================================================

        try:

            eye_result = (
                detect_eye_contact(
                    frame
                )
            )

            eye_state = (
                eye_result.get(
                    "eye_contact",
                    "UNKNOWN"
                )
            )

            eye_score = clamp(
                safe_float(
                    eye_result.get(
                        "score",
                        0.0
                    )
                ),
                0.0,
                100.0
            )

            eye_direction = (
                eye_result.get(
                    "direction",
                    "Unknown"
                )
            )

            if not is_head_calibration:

                eye_states.append(
                    eye_state
                )

                eye_scores.append(
                    eye_score
                )

                eye_directions.append(
                    eye_direction
                )

        except Exception as e:

            print(
                "[Eye Contact Error] "
                f"{video_time:.2f}s: "
                f"{type(e).__name__}: {e}"
            )

        # ====================================================
        # HEAD POSE
        # ====================================================

        try:

            head_result = (
                detect_head_pose(
                    frame
                )
            )

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
                0.0,
                100.0
            )

            detected = bool(
                head_result.get(
                    "detected",
                    False
                )
            )

            # ------------------------------------------------
            # CALIBRATION
            # ------------------------------------------------

            if is_head_calibration:

                valid_sample = (
                    detected
                    and
                    np.isfinite(raw_yaw)
                    and
                    np.isfinite(raw_pitch)
                    and
                    np.isfinite(raw_roll)
                    and
                    abs(raw_yaw) <= 70.0
                    and
                    abs(raw_pitch) <= 50.0
                    and
                    abs(raw_roll) <= 50.0
                )

                if valid_sample:

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
                        head_confidence
                    )

            else:

                # --------------------------------------------
                # RELATIVE HEAD POSE
                # --------------------------------------------

                if head_pose_baseline[
                    "valid"
                ]:

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

                    relative_yaw = raw_yaw
                    relative_pitch = raw_pitch
                    relative_roll = raw_roll

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

                if (
                    relative_yaw
                    < -15.0
                ):

                    calibrated_pose = (
                        "Looking Left"
                    )

                elif (
                    relative_yaw
                    > 15.0
                ):

                    calibrated_pose = (
                        "Looking Right"
                    )

                elif (
                    relative_pitch
                    < -15.0
                ):

                    calibrated_pose = (
                        "Looking Up"
                    )

                elif (
                    relative_pitch
                    > 15.0
                ):

                    calibrated_pose = (
                        "Looking Down"
                    )

                else:

                    calibrated_pose = (
                        "Center"
                    )

                head_result = {
                    "pose": calibrated_pose,

                    "yaw": round(
                        relative_yaw,
                        2
                    ),

                    "pitch": round(
                        relative_pitch,
                        2
                    ),

                    "roll": round(
                        relative_roll,
                        2
                    ),

                    "confidence": round(
                        head_confidence,
                        1
                    ),

                    "detected": detected,
                }

                if detected:

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
                        head_confidence
                    )

        except Exception as e:

            print(
                "[Head Pose Error] "
                f"{video_time:.2f}s: "
                f"{type(e).__name__}: {e}"
            )

        # ====================================================
        # COMPLETE CALIBRATION
        # ====================================================

        if is_head_calibration:

            if frame_number % 15 == 0:

                progress = (
                    frame_number
                    /
                    calibration_frames
                    *
                    100.0
                )

                print(
                    f"Calibration: "
                    f"{min(progress, 100.0):5.1f}%"
                    f" | Head samples: "
                    f"{len(calibration_yaws)}"
                )

            if (
                frame_number
                >= calibration_frames
            ):

                head_pose_baseline = (
                    calculate_head_pose_baseline(
                        calibration_yaws,
                        calibration_pitches,
                        calibration_rolls,
                        calibration_confidences
                    )
                )

                head_calibration_completed = True

                print()

                print(
                    "Head Pose Calibration:"
                )

                print(
                    "Samples      : "
                    f"{head_pose_baseline['samples']}"
                )

                print(
                    "Raw Samples  : "
                    f"{head_pose_baseline['raw_samples']}"
                )

                print(
                    "Filtered     : "
                    f"{head_pose_baseline['filtered_samples']}"
                )

                print(
                    "Baseline Yaw : "
                    f"{head_pose_baseline['yaw']:.2f}°"
                )

                print(
                    "Baseline Pitch: "
                    f"{head_pose_baseline['pitch']:.2f}°"
                )

                print(
                    "Yaw Stability: "
                    f"{head_pose_baseline['yaw_std']:.2f}°"
                )

                print(
                    "Pitch Stability: "
                    f"{head_pose_baseline['pitch_std']:.2f}°"
                )

                print(
                    "Status       : "
                    f"{'VALID' if head_pose_baseline['valid'] else 'FALLBACK'}"
                )

                print()

                # Calibration frame is NOT an interview sample.
                continue

        # ====================================================
        # NORMAL FRAME
        # ====================================================

        analyzed_frames += 1

        # ====================================================
        # EMOTION
        # ====================================================

        try:

            emotion_result = (
                detect_emotion(
                    frame,
                    current_time=video_time
                )
            )

            emotion = (
                emotion_result.get(
                    "emotion",
                    "UNKNOWN"
                )
            )

            emotion_confidence = safe_float(
                emotion_result.get(
                    "confidence",
                    0.0
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
                and
                emotion_error
                != last_emotion_error
            ):

                print(
                    "[Emotion] "
                    f"{video_time:.2f}s: "
                    f"{emotion_error}"
                )

                last_emotion_error = (
                    emotion_error
                )

        except Exception as e:

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
                "[Emotion Error] "
                f"{video_time:.2f}s: "
                f"{type(e).__name__}: {e}"
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
                            0.0
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
                            0.0
                        )
                    ),
                    2
                ),

            "head_pitch":
                round(
                    safe_float(
                        head_result.get(
                            "pitch",
                            0.0
                        )
                    ),
                    2
                ),

            "head_roll":
                round(
                    safe_float(
                        head_result.get(
                            "roll",
                            0.0
                        )
                    ),
                    2
                ),

            "head_confidence":
                round(
                    safe_float(
                        head_result.get(
                            "confidence",
                            0.0
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
                100.0
                if duration > 0
                else 0.0
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

    cap.release()

    # ========================================================
    # EYE SUMMARY
    # ========================================================

    average_eye_score = (
        float(
            np.mean(
                eye_scores
            )
        )
        if eye_scores
        else 0.0
    )

    eye_contact_percentage = (
        average_eye_score
    )

    looking_away_percentage = (
        100.0
        -
        eye_contact_percentage
    )

    yes_count = sum(
        1
        for x in eye_states
        if x == "YES"
    )

    no_count = sum(
        1
        for x in eye_states
        if x == "NO"
    )

    unknown_count = sum(
        1
        for x in eye_states
        if x not in (
            "YES",
            "NO"
        )
    )

    # ========================================================
    # HEAD SUMMARY
    # ========================================================

    center_count = sum(
        1
        for x in head_poses
        if x == "Center"
    )

    away_count = sum(
        1
        for x in head_poses
        if x in (
            "Looking Left",
            "Looking Right",
            "Looking Up",
            "Looking Down"
        )
    )

    pose_count = len(
        head_poses
    )

    center_percentage = (
        center_count
        /
        pose_count
        *
        100.0
        if pose_count
        else 0.0
    )

    looking_away_pose_percentage = (
        away_count
        /
        pose_count
        *
        100.0
        if pose_count
        else 0.0
    )

    average_yaw = (
        float(
            np.mean(
                yaw_values
            )
        )
        if yaw_values
        else 0.0
    )

    average_pitch = (
        float(
            np.mean(
                pitch_values
            )
        )
        if pitch_values
        else 0.0
    )

    average_roll = (
        float(
            np.mean(
                roll_values
            )
        )
        if roll_values
        else 0.0
    )

    average_head_confidence = (
        float(
            np.mean(
                head_confidences
            )
        )
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

    calibration_score = 0.0

    if head_pose_baseline[
        "valid"
    ]:

        stability_score = np.mean([

            max(
                0.0,
                1.0
                -
                head_pose_baseline[
                    "yaw_std"
                ]
                /
                15.0
            ),

            max(
                0.0,
                1.0
                -
                head_pose_baseline[
                    "pitch_std"
                ]
                /
                12.0
            ),

            max(
                0.0,
                1.0
                -
                head_pose_baseline[
                    "roll_std"
                ]
                /
                10.0
            ),

        ])

        calibration_score = (

            0.5
            *
            stability_score
            *
            100.0

            +

            0.5
            *
            head_pose_baseline[
                "average_confidence"
            ]
        )

    reliability = (

        0.30
        *
        average_head_confidence

        +

        0.25
        *
        calibration_score

        +

        0.20
        *
        float(
            emotion_summary.get(
                "face_detection_rate",
                0.0
            )
        )

        +

        0.25
        *
        (
            100.0
            if eye_scores
            else 0.0
        )
    )

    reliability = float(
        np.clip(
            reliability,
            0.0,
            100.0
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

        "emotion":
            emotion_summary,

        "emotion_timeline":
            emotion_results,

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

        "quality": {

            "estimated_reliability":
                round(
                    reliability,
                    2
                ),

            "note":
                (
                    "Reliability is a system-quality "
                    "score, not ground-truth model "
                    "accuracy. True accuracy requires "
                    "manually labelled frames."
                ),
        },

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
# REPORT
# ============================================================

def print_video_report(
    result
):

    video = result["video"]
    eye = result["eye_contact"]
    emotion = result["emotion"]
    head = result["head_pose"]
    quality = result["quality"]

    print()

    print("=" * 65)
    print(
        "             VIDEO ANALYSIS REPORT"
    )
    print("=" * 65)

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

    print()
    print("EYE CONTACT")
    print("-" * 45)

    print(
        f"Average V6 Score  : "
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
        f"{head['average_yaw']:.2f}"
    )

    print(
        f"Average Pitch     : "
        f"{head['average_pitch']:.2f}"
    )

    print(
        f"Average Roll      : "
        f"{head['average_roll']:.2f}"
    )

    print(
        f"Detection Conf.   : "
        f"{head['average_confidence']:.1f}%"
    )

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
        f"{'VALID' if calibration.get('valid') else 'FALLBACK'}"
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
        f"{calibration.get('yaw', 0.0):.2f}"
    )

    print(
        f"Baseline Pitch    : "
        f"{calibration.get('pitch', 0.0):.2f}"
    )

    print(
        f"Yaw Stability     : "
        f"{calibration.get('yaw_std', 0.0):.2f}"
    )

    print(
        f"Pitch Stability   : "
        f"{calibration.get('pitch_std', 0.0):.2f}"
    )

    print()
    print("SYSTEM QUALITY")
    print("-" * 45)

    print(
        f"Estimated Reliability : "
        f"{quality['estimated_reliability']:.1f}%"
    )

    print(
        "IMPORTANT: this is reliability, "
        "NOT mathematical accuracy."
    )

    print(
        "Ground-truth labels are required "
        "for true accuracy."
    )

    print()
    print("=" * 65)

    print(
        "             VIDEO ANALYSIS FINISHED"
    )

    print("=" * 65)
    print()


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage:\n"
            "python test_video_analysis.py "
            "<video_path>"
        )

        sys.exit(1)

    video_path = sys.argv[1]

    result = analyze_video(
        video_path
    )

    save_video_result(
        result,
        "video_analysis.json"
    )

    print_video_report(
        result
    )

    print(
        "\nJSON saved as:\n"
        "video_analysis.json"
    )