import cv2

from app.ai.head_pose import detect_head_pose


cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("❌ Camera could not be opened")
    exit()


while True:

    ret, frame = cap.read()

    if not ret:
        print("❌ Could not read frame")
        break

    frame = cv2.flip(
        frame,
        1
    )

    result = detect_head_pose(
        frame
    )

    pose = result["pose"]
    yaw = result["yaw"]
    pitch = result["pitch"]
    confidence = result["confidence"]


    print(
        f"Head Pose: {pose} | "
        f"Yaw: {yaw} | "
        f"Pitch: {pitch}"
    )


    cv2.putText(
        frame,
        f"Head Pose: {pose}",
        (30, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Yaw: {yaw}",
        (30, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Pitch: {pitch}",
        (30, 115),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Detection: {confidence}%",
        (30, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    cv2.imshow(
        "PREP-CHECK - Head Pose",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break


cap.release()

cv2.destroyAllWindows()