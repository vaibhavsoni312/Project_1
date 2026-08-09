from faster_whisper import WhisperModel
import sys
import os
import time


# ============================================================
# CONFIG
# ============================================================

MODEL_SIZE = "base"

# CPU because you're running on Mac
DEVICE = "cpu"

COMPUTE_TYPE = "int8"


# ============================================================
# CHECK INPUT
# ============================================================

if len(sys.argv) < 2:
    print()
    print("Usage:")
    print("python test_speech_to_text.py <video_or_audio_file>")
    print()
    print("Example:")
    print("python test_speech_to_text.py interview.mp4")
    print()
    sys.exit(1)


media_file = sys.argv[1]


if not os.path.exists(media_file):

    print()
    print("ERROR: File not found:")
    print(media_file)
    print()

    sys.exit(1)


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 65)
print("             PREP-CHECK - SPEECH TO TEXT")
print("=" * 65)

print()
print("Input File :", media_file)
print("Model      :", MODEL_SIZE)
print("Device     :", DEVICE)
print("Compute    :", COMPUTE_TYPE)
print()


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading Whisper model...")

load_start = time.time()

model = WhisperModel(
    MODEL_SIZE,
    device=DEVICE,
    compute_type=COMPUTE_TYPE
)

load_time = time.time() - load_start

print(
    f"Model loaded in {load_time:.1f} sec"
)

print()


# ============================================================
# TRANSCRIBE
# ============================================================

print("Transcribing interview...")
print("Please wait...")
print()


start_time = time.time()


segments, info = model.transcribe(
    media_file,
    beam_size=5,
    vad_filter=True,
    vad_parameters={
        "min_silence_duration_ms": 500
    }
)


# ============================================================
# COLLECT SEGMENTS
# ============================================================

transcript_segments = []


for segment in segments:

    start = segment.start
    end = segment.end
    text = segment.text.strip()

    if not text:
        continue


    transcript_segments.append({
        "start": start,
        "end": end,
        "text": text
    })


    # --------------------------------------------------------
    # LIVE TERMINAL OUTPUT
    # --------------------------------------------------------

    print(
        f"[{start:7.2f}s - {end:7.2f}s] "
        f"{text}"
    )


# ============================================================
# PROCESSING TIME
# ============================================================

processing_time = (
    time.time()
    -
    start_time
)


# ============================================================
# FINAL TRANSCRIPT
# ============================================================

full_transcript = " ".join(
    segment["text"]
    for segment
    in transcript_segments
)


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 65)
print("              SPEECH TO TEXT REPORT")
print("=" * 65)

print()

print(
    f"Detected Language    : "
    f"{info.language}"
)

print(
    f"Language Probability : "
    f"{info.language_probability:.2f}"
)

print(
    f"Segments             : "
    f"{len(transcript_segments)}"
)

print(
    f"Processing Time      : "
    f"{processing_time:.1f} sec"
)

print()

print("-" * 65)
print("FULL TRANSCRIPT")
print("-" * 65)

print()

if full_transcript:

    print(full_transcript)

else:

    print("No speech detected.")


print()

print("=" * 65)
print("                  TEST FINISHED")
print("=" * 65)