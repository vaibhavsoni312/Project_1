import json
from datetime import datetime


# ============================================================
# FEATURE ENGINE
# ============================================================

def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, float(value)))


# ============================================================
# VOICE
# ============================================================

def calculate_voice_features(data):

    speaking_rate = float(data.get("speaking_rate", 0))
    silence_ratio = float(data.get("silence_ratio", 0))
    pause_count = int(data.get("pause_count", 0))
    average_pause = float(data.get("average_pause", 0))
    filler_rate = float(data.get("filler_rate", 0))
    pitch_variation = float(data.get("pitch_variation", 0))
    volume_variation = float(data.get("volume_variation", 0))

    # Speaking rate
    if 120 <= speaking_rate <= 160:
        rate_score = 100
    elif 105 <= speaking_rate < 120 or 160 < speaking_rate <= 180:
        rate_score = 85
    elif 90 <= speaking_rate < 105 or 180 < speaking_rate <= 200:
        rate_score = 70
    else:
        rate_score = 50

    # Silence
    if 10 <= silence_ratio <= 25:
        silence_score = 100
    elif 5 <= silence_ratio < 10 or 25 < silence_ratio <= 35:
        silence_score = 80
    elif silence_ratio < 5:
        silence_score = 70
    else:
        silence_score = 50

    # Pauses
    if pause_count == 0:
        pause_score = 75
    elif average_pause <= 1:
        pause_score = 100
    elif average_pause <= 2:
        pause_score = 80
    elif average_pause <= 3:
        pause_score = 60
    else:
        pause_score = 40

    # Fillers
    if filler_rate <= 1:
        filler_score = 100
    elif filler_rate <= 3:
        filler_score = 85
    elif filler_rate <= 6:
        filler_score = 70
    else:
        filler_score = 50

    # Pitch
    if 15 <= pitch_variation <= 60:
        pitch_score = 100
    elif 10 <= pitch_variation < 15 or 60 < pitch_variation <= 80:
        pitch_score = 80
    else:
        pitch_score = 60

    # Volume
    if 5 <= volume_variation <= 15:
        volume_score = 100
    elif volume_variation < 5 or 15 < volume_variation <= 25:
        volume_score = 80
    else:
        volume_score = 60

    voice_score = (
        rate_score * 0.25 +
        silence_score * 0.15 +
        pause_score * 0.15 +
        filler_score * 0.15 +
        pitch_score * 0.15 +
        volume_score * 0.15
    )

    return {
        "speaking_rate": speaking_rate,
        "silence_ratio": silence_ratio,
        "pause_count": pause_count,
        "average_pause": average_pause,
        "filler_rate": filler_rate,
        "pitch_variation": pitch_variation,
        "volume_variation": volume_variation,

        "rate_score": round(rate_score, 2),
        "silence_score": round(silence_score, 2),
        "pause_score": round(pause_score, 2),
        "filler_score": round(filler_score, 2),
        "pitch_score": round(pitch_score, 2),
        "volume_score": round(volume_score, 2),

        "voice_feature_score": round(voice_score, 2)
    }


# ============================================================
# EYE CONTACT
# ============================================================

def calculate_eye_contact_features(data):

    percentage = float(
        data.get("eye_contact_percentage", 0)
    )

    percentage = clamp(percentage)

    if percentage >= 75:
        score = 100
    elif percentage >= 60:
        score = 85
    elif percentage >= 45:
        score = 70
    elif percentage >= 30:
        score = 55
    else:
        score = 40

    return {
        "eye_contact_percentage": round(percentage, 2),
        "eye_contact_score": round(score, 2)
    }


# ============================================================
# EMOTION
# ============================================================

def calculate_emotion_features(data):

    emotion = str(
        data.get(
            "dominant_emotion",
            "unknown"
        )
    ).lower()

    confidence = clamp(
        data.get(
            "emotion_confidence",
            0
        )
    )

    positive = {
        "happy",
        "neutral"
    }

    negative = {
        "angry",
        "fear",
        "sad",
        "disgust"
    }

    if emotion in positive:
        base_score = 90

    elif emotion == "surprise":
        base_score = 75

    elif emotion in negative:
        base_score = 55

    else:
        base_score = 70

    emotion_score = (
        base_score * 0.7 +
        confidence * 0.3
    )

    return {
        "dominant_emotion": emotion,
        "emotion_confidence": round(confidence, 2),
        "emotion_score": round(
            clamp(emotion_score),
            2
        )
    }


# ============================================================
# HEAD POSE
# ============================================================

def calculate_head_pose_features(data):

    score = clamp(
        data.get(
            "head_pose_score",
            0
        )
    )

    return {
        "head_pose_score": round(score, 2)
    }


# ============================================================
# HIGH LEVEL FEATURES
# ============================================================

def calculate_communication(
    voice_score,
    emotion_score
):

    return round(
        clamp(
            voice_score * 0.75 +
            emotion_score * 0.25
        ),
        2
    )


def calculate_confidence(
    voice_score,
    eye_score,
    emotion_score
):

    return round(
        clamp(
            voice_score * 0.40 +
            eye_score * 0.40 +
            emotion_score * 0.20
        ),
        2
    )


def calculate_body_language(
    eye_score,
    head_score,
    emotion_score
):

    return round(
        clamp(
            eye_score * 0.45 +
            head_score * 0.35 +
            emotion_score * 0.20
        ),
        2
    )

# ============================================================
# ADAPTER — connects video_analyzer + voice_analyzer output
# to build_features() input format
# ============================================================

def adapt_video_result(video_result, voice_result):
    """
    Converts video_analyzer + voice_analyzer raw outputs into the
    shape build_features() expects.
    """

    eye = video_result.get("eye_contact", {})
    emotion = video_result.get("emotion", {})
    head = video_result.get("head_pose", {})

    eye_data = {
        "eye_contact_percentage": eye.get("eye_contact_percentage", 0)
    }

    emotion_data = {
        "dominant_emotion": emotion.get("dominant_emotion", "unknown"),
        "emotion_confidence": emotion.get("average_confidence", 0),
    }

    # head_pose_data: video_analyzer doesn't give a single 0-100 score,
    # so we derive one from center_percentage (time spent facing camera).
    head_pose_data = {
        "head_pose_score": head.get("center_percentage", 0)
    }

    voice_data = voice_result  # already in the right shape

    return voice_data, eye_data, emotion_data, head_pose_data


# ============================================================
# SIMPLE FEEDBACK (replaces delta_detection + ai_feedback)
# ============================================================

def generate_simple_feedback(result):
    feedback = []

    voice = result["voice"]
    eye = result["eye_contact"]
    emotion = result["emotion"]
    head = result["head_pose"]

    if voice["rate_score"] < 70:
        feedback.append("Your speaking pace needs adjustment — try to stay closer to 120-160 words per minute.")

    if voice["filler_score"] < 70:
        feedback.append("You used filler words fairly often. Try pausing instead of saying 'um' or 'like'.")

    if voice["pause_score"] < 60:
        feedback.append("Your pauses were quite long — practice keeping a steadier flow.")

    if eye["eye_contact_score"] < 70:
        feedback.append(f"Eye contact was only {eye['eye_contact_percentage']}%. Try to look at the camera more consistently.")

    if head["head_pose_score"] < 60:
        feedback.append("You turned away from the camera frequently. Keep facing forward when possible.")

    if emotion["dominant_emotion"] in ("angry", "fear", "sad", "disgust"):
        feedback.append(f"Your dominant expression was '{emotion['dominant_emotion']}'. Try to stay relaxed and neutral/positive.")

    if not feedback:
        feedback.append("Solid performance overall — keep it up!")

    return feedback
# ============================================================
# MAIN FEATURE ENGINE
# ============================================================

def build_features(
    voice_data,
    eye_data,
    emotion_data,
    head_pose_data
):

    voice = calculate_voice_features(
        voice_data
    )

    eye = calculate_eye_contact_features(
        eye_data
    )

    emotion = calculate_emotion_features(
        emotion_data
    )

    head = calculate_head_pose_features(
        head_pose_data
    )

    communication = calculate_communication(
        voice["voice_feature_score"],
        emotion["emotion_score"]
    )

    confidence = calculate_confidence(
        voice["voice_feature_score"],
        eye["eye_contact_score"],
        emotion["emotion_score"]
    )

    body_language = calculate_body_language(
        eye["eye_contact_score"],
        head["head_pose_score"],
        emotion["emotion_score"]
    )

    return {

        "timestamp":
            datetime.now().isoformat(),

        "voice":
            voice,

        "eye_contact":
            eye,

        "emotion":
            emotion,

        "head_pose":
            head,

        "high_level": {

            "communication":
                communication,

            "confidence":
                confidence,

            "body_language":
                body_language
        }
    }


# ============================================================
# SAVE RESULT
# ============================================================

def save_features(
    result,
    filename="feature_result.json"
):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=4
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 65)
    print("             FEATURE ENGINE TEST")
    print("=" * 65)
    print()

    # --------------------------------------------------------
    # TEMPORARY TEST INPUT
    #
    # IMPORTANT:
    # These are ONLY for testing the engine.
    # Later actual modules will send these dictionaries.
    # --------------------------------------------------------

    voice_data = {

        "speaking_rate": 103.4,

        "silence_ratio": 16.9,

        "pause_count": 1,

        "average_pause": 0.55,

        "filler_rate": 0.0,

        "pitch_variation": 37.9,

        "volume_variation": 11.77
    }

    eye_data = {

        "eye_contact_percentage": 70.0
    }

    emotion_data = {

        "dominant_emotion": "neutral",

        "emotion_confidence": 70.0
    }

    head_pose_data = {

        "head_pose_score": 80.0
    }

    result = build_features(

        voice_data,

        eye_data,

        emotion_data,

        head_pose_data
    )

    print("COMMUNICATION :", result["high_level"]["communication"])
    print("CONFIDENCE    :", result["high_level"]["confidence"])
    print("BODY LANGUAGE :", result["high_level"]["body_language"])

    print()
    print("Saving feature_result.json...")

    save_features(
        result
    )

    print("Saved successfully.")
    print()

    print("=" * 65)
    print("              FEATURE ENGINE TEST PASSED")
    print("=" * 65)
    print()