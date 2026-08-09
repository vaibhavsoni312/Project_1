def build_shared_timeline(features):
    timeline = []

    for feature in features:
        timeline.append({
            "timestamp": feature["timestamp"],
            "type": feature["type"],
            "value": feature["value"]
        })

    return sorted(timeline, key=lambda x: x["timestamp"])

