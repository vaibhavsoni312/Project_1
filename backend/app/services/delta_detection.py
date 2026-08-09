def detect_deltas(timeline):
    deltas = []
    last_seen = {}

    for current in timeline:
        feature_type = current["type"]

        if feature_type not in last_seen:
            last_seen[feature_type] = current["value"]
            continue

        previous_value = last_seen[feature_type]

        if previous_value != current["value"]:
            deltas.append({
                "timestamp": current["timestamp"],
                "feature": feature_type,
                "before": previous_value,
                "after": current["value"]
            })

        last_seen[feature_type] = current["value"]

    return deltas