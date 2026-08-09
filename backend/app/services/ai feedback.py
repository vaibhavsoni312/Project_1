def generate_feedback(deltas):

    feedback = []

    for delta in deltas:

        if delta["feature"] == "filler_word":
            feedback.append({
                "timestamp": delta["timestamp"],
                "feedback": "Try replacing filler words with a short pause."
            })

        elif delta["feature"] == "nervous":
            feedback.append({
                "timestamp": delta["timestamp"],
                "feedback": "Your expression suggests nervousness here. Slow down and take a breath."
            })

    return feedback