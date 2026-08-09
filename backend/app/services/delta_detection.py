def detect_deltas(timeline):
    deltas = []
    last_seen = {}

    for current in timeline:
        feature_type = current["type"]

        # First time this feature appears
        if feature_type not in last_seen:
            last_seen[feature_type] = current["value"]
            continue

        previous_value = last_seen[feature_type]

        # Only compare the same feature type
        if previous_value != current["value"]:
            deltas.append({
                "timestamp": current["timestamp"],
                "feature": feature_type,
                "before": previous_value,
                "after": current["value"]
            })

        # Update latest value
        last_seen[feature_type] = current["value"]

    return deltas
timeline = [
    {
        "timestamp": 5,
        "type": "emotion",
        "value": "neutral"
    },
    {
        "timestamp": 10,
        "type": "filler_word",
        "value": "um"
    },
    {
        "timestamp": 15,
        "type": "emotion",
        "value": "nervous"
    },
    {
        "timestamp": 20,
        "type": "emotion",
        "value": "confident"
    }
]

result = detect_deltas(timeline)

print(result)