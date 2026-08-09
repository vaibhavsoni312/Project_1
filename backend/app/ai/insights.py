from app.services.timeline import build_shared_timeline
from app.services.delta_detection import detect_deltas
from app.services.ai_feedback import generate_feedback


# Which columns of a video_analyzer frame become tracked "features".
TRACKED_FEATURES = ("eye_contact", "head_pose", "emotion")


def _frames_to_events(frame_timeline):
    events = []

    for frame in frame_timeline:
        timestamp = frame.get("time", 0)

        for feature in TRACKED_FEATURES:
            value = frame.get(feature)

            if value is None:
                continue

            events.append({
                "timestamp": timestamp,
                "type": feature,
                "value": value,
            })

    return events


def generate_insights(analysis_result):
    """
    Takes the dict returned by video_analyzer.analyze_video()
    and returns {"deltas": [...], "feedback": [...]}.
    """

    frame_timeline = analysis_result.get("timeline", [])

    events = _frames_to_events(frame_timeline)

    ordered_timeline = build_shared_timeline(events)

    deltas = detect_deltas(ordered_timeline)

    feedback = generate_feedback(deltas)

    return {
        "deltas": deltas,
        "feedback": feedback,
    }