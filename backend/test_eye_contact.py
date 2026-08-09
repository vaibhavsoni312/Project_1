import cv2
import time

from app.ai.eye_contact import detect_eye_contact


# =========================================================
# CAMERA
# =========================================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera could not be opened.")
    exit()


# =========================================================
# CAMERA SETTINGS
# =========================================================

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


# =========================================================
# SESSION
# =========================================================

start_time = time.time()

total_frames = 0
eye_contact_frames = 0
looking_away_frames = 0
unknown_frames = 0


# =========================================================
# PRINT HEADER
# =========================================================

print()
print("==============================================")
print("       PREP-CHECK - EYE CONTACT V6")
print("==============================================")
print()
print("Look directly at the camera.")
print("Calibration will happen automatically.")
print()
print("Press Q to finish.")
print()


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    ret, frame = cap.read()

    if not ret:
        print("ERROR: Could not read camera frame.")
        break

    total_frames += 1

    # =====================================================
    # MIRROR CAMERA
    # =====================================================

    # This makes the webcam behave like a normal selfie camera.
    frame = cv2.flip(frame, 1)

    # =====================================================
    # EYE CONTACT DETECTION
    # =====================================================

    try:

        result = detect_eye_contact(frame)

    except Exception as e:

        print("Detection error:", e)

        cv2.imshow(
            "PREP-CHECK - Eye Contact V6",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        continue

    # =====================================================
    # RESULT
    # =====================================================

    state = result.get(
        "eye_contact",
        "UNKNOWN"
    )

    score = result.get(
        "score",
        0
    )

    direction = result.get(
        "direction",
        "Unknown"
    )

    calibrated = result.get(
        "calibrated",
        False
    )

    # =====================================================
    # COUNT
    # =====================================================

    if state == "YES":

        eye_contact_frames += 1

    elif state == "NO":

        looking_away_frames += 1

    else:

        unknown_frames += 1

    # =====================================================
    # TERMINAL OUTPUT
    # =====================================================

    if total_frames % 15 == 0:

        print(
            f"Eye Contact: {state} | "
            f"Gaze: {direction} | "
            f"Score: {score:.0f}%"
        )

    # =====================================================
    # CALIBRATION DISPLAY
    # =====================================================

    if not calibrated:

        cv2.putText(
            frame,
            "CALIBRATING - Look at camera",
            (30, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

    else:

        # =================================================
        # EYE CONTACT
        # =================================================

        if state == "YES":

            text_color = (
                0,
                255,
                0
            )

        elif state == "NO":

            text_color = (
                0,
                0,
                255
            )

        else:

            text_color = (
                0,
                255,
                255
            )

        cv2.putText(
            frame,
            f"Eye Contact: {score:.0f}%",
            (30, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            text_color,
            2
        )

        # =================================================
        # GAZE
        # =================================================

        cv2.putText(
            frame,
            f"Gaze: {direction}",
            (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2
        )

        # =================================================
        # STATUS
        # =================================================

        cv2.putText(
            frame,
            f"Status: {state}",
            (30, 155),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            text_color,
            2
        )

    # =====================================================
    # WINDOW
    # =====================================================

    cv2.imshow(
        "PREP-CHECK - Eye Contact V6",
        frame
    )

    # =====================================================
    # QUIT
    # =====================================================

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):

        break


# =========================================================
# CLEANUP
# =========================================================

cap.release()

cv2.destroyAllWindows()


# =========================================================
# FINAL REPORT
# =========================================================

duration = time.time() - start_time

counted_frames = (
    eye_contact_frames +
    looking_away_frames
)

if counted_frames > 0:

    final_score = (
        eye_contact_frames /
        counted_frames
    ) * 100

else:

    final_score = 0


print()
print("==============================================")
print("          EYE CONTACT FINAL REPORT")
print("==============================================")

print(
    f"Duration          : {duration:.1f} sec"
)

print(
    f"Total Frames      : {total_frames}"
)

print(
    f"Eye Contact Frames: {eye_contact_frames}"
)

print(
    f"Looking Away      : {looking_away_frames}"
)

print(
    f"Unknown Frames    : {unknown_frames}"
)

print(
    f"Counted Frames    : {counted_frames}"
)

print(
    f"Final Score       : {final_score:.1f}%"
)

print("==============================================")
print()