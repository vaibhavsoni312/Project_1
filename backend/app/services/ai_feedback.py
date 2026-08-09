def generate_feedback(deltas):

    feedback = []

    for delta in deltas:

        feature = delta["feature"]
        after = delta["after"]

        if feature == "filler_word":
            feedback.append({
                "timestamp": delta["timestamp"],
                "feedback": "Try replacing filler words with a short pause."
            })

        elif feature == "nervous":
            feedback.append({
                "timestamp": delta["timestamp"],
                "feedback": "Your expression suggests nervousness here. Slow down and take a breath."
            })

        elif feature == "eye_contact" and after == "NO":
            feedback.append({
                "timestamp": delta["timestamp"],
                "feedback": "You looked away from the camera here. Try to hold eye contact a little longer."
            })

        elif feature == "head_pose" and after != "Center":
            feedback.append({
                "timestamp": delta["timestamp"],
                "feedback": f"Your head turned away from center ({after}). Keep facing the camera when possible."
            })

        elif feature == "emotion" and after in ("fear", "sad", "angry", "disgust"):
            feedback.append({
                "timestamp": delta["timestamp"],
                "feedback": f"Your expression shifted to {after} here. Worth reviewing this moment."
            })

    return feedback