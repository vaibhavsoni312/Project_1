# test.py

from app.ai.video_analyzer import analyze_video, print_video_report
from app.ai.audio_extractor import extract_audio
from Project_1.backend.app.ai.voice_analyzer import analyze_voice
from feature_engine import (
    adapt_video_result,
    build_features,
    generate_simple_feedback,
)


VIDEO_PATH = "sample.mp4"


# ============================================================
# STEP 1: VIDEO ANALYSIS (eye contact + head pose + emotion)
# ============================================================

print("Running video analysis...")

analysis_result = analyze_video(VIDEO_PATH)

print_video_report(analysis_result)


# ============================================================
# STEP 2: EXTRACT AUDIO + VOICE ANALYSIS
# ============================================================

print("Extracting audio...")

audio_path = extract_audio(VIDEO_PATH)

print(f"Audio extracted to: {audio_path}")
print("Running voice analysis (Whisper model load ho raha hai, thoda time lagega)...")

voice_result = analyze_voice(audio_path)

print()
print("VOICE ANALYSIS RESULT:")
print(voice_result)


# ============================================================
# STEP 3: FEATURE ENGINE (final scores)
# ============================================================

voice_data, eye_data, emotion_data, head_pose_data = adapt_video_result(
    analysis_result, voice_result
)

final_scores = build_features(
    voice_data, eye_data, emotion_data, head_pose_data
)

feedback = generate_simple_feedback(final_scores)


# ============================================================
# FINAL OUTPUT
# ============================================================

print()
print("=" * 65)
print("             FINAL SCORES")
print("=" * 65)

print("Communication :", final_scores["high_level"]["communication"])
print("Confidence    :", final_scores["high_level"]["confidence"])
print("Body Language :", final_scores["high_level"]["body_language"])

print()
print("FEEDBACK:")
for line in feedback:
    print(" -", line)

print()
print("=" * 65)
print("             TEST COMPLETE")
print("=" * 65)