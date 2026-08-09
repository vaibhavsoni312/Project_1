import sys
import os
import re
import time

import numpy as np
import librosa
from faster_whisper import WhisperModel


# ============================================================
# CONFIG
# ============================================================

WHISPER_MODEL = "base"
SAMPLE_RATE = 16000

# Silence detection
SILENCE_DB = -35

# Pause threshold
MIN_PAUSE = 0.35


# ============================================================
# INPUT
# ============================================================

if len(sys.argv) < 2:
    print()
    print("Usage:")
    print("python test_voice_analysis.py <audio_file>")
    print()
    sys.exit(1)


audio_file = sys.argv[1]

if not os.path.exists(audio_file):
    print()
    print("ERROR: File not found:")
    print(audio_file)
    print()
    sys.exit(1)


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 72)
print("                 PREP-CHECK - VOICE ANALYSIS V2")
print("=" * 72)

print()
print(f"Audio File : {audio_file}")
print(f"Sample Rate: {SAMPLE_RATE}")
print()


# ============================================================
# LOAD AUDIO
# ============================================================

print("Loading audio...")

audio, sr = librosa.load(
    audio_file,
    sr=SAMPLE_RATE,
    mono=True
)

duration = len(audio) / sr

print(f"Duration   : {duration:.2f} sec")
print()


# ============================================================
# NORMALIZE
# ============================================================

peak = np.max(np.abs(audio))

if peak > 0:
    audio_normalized = audio / peak
else:
    audio_normalized = audio.copy()


# ============================================================
# RMS / VOLUME
# ============================================================

rms = librosa.feature.rms(
    y=audio_normalized,
    frame_length=2048,
    hop_length=512
)[0]

rms_db = librosa.amplitude_to_db(
    rms,
    ref=np.max
)

average_volume = float(np.mean(rms_db))
volume_std = float(np.std(rms_db))
max_volume = float(np.max(rms_db))


# ============================================================
# BASIC SILENCE DETECTION
# ============================================================

frame_duration = 512 / sr

speech_mask = rms_db > SILENCE_DB

speech_duration_energy = (
    np.sum(speech_mask) * frame_duration
)

energy_silence_duration = max(
    0,
    duration - speech_duration_energy
)

energy_silence_ratio = (
    energy_silence_duration / duration * 100
    if duration > 0
    else 0
)


# ============================================================
# WHISPER
# ============================================================

print("Loading Whisper model...")

model_start = time.time()

model = WhisperModel(
    WHISPER_MODEL,
    device="cpu",
    compute_type="int8"
)

print(
    f"Whisper loaded in "
    f"{time.time() - model_start:.1f} sec"
)

print()
print("Analyzing speech...")
print()


# ============================================================
# TRANSCRIPTION
# ============================================================

segments, info = model.transcribe(
    audio_file,
    beam_size=5,
    vad_filter=True,
    vad_parameters={
        "min_silence_duration_ms": 300
    },
    word_timestamps=True
)


segment_data = []
all_words = []


for segment in segments:

    text = segment.text.strip()

    if not text:
        continue

    words = re.findall(
        r"\b[\w'-]+\b",
        text
    )

    all_words.extend(words)

    segment_data.append({
        "start": float(segment.start),
        "end": float(segment.end),
        "text": text
    })


word_count = len(all_words)


# ============================================================
# SPEAKING TIME
# ============================================================

speaking_time = 0.0

for item in segment_data:

    speaking_time += max(
        0,
        item["end"] - item["start"]
    )


# ============================================================
# SPEAKING RATE
# ============================================================

overall_wpm = (
    word_count / duration * 60
    if duration > 0
    else 0
)

active_wpm = (
    word_count / speaking_time * 60
    if speaking_time > 0
    else 0
)


# ============================================================
# WHISPER PAUSE DETECTION
# ============================================================

pauses = []

for i in range(1, len(segment_data)):

    previous_end = segment_data[i - 1]["end"]
    current_start = segment_data[i]["start"]

    gap = current_start - previous_end

    if gap >= MIN_PAUSE:
        pauses.append(gap)


total_pauses = len(pauses)

average_pause = (
    float(np.mean(pauses))
    if pauses
    else 0.0
)

longest_pause = (
    float(np.max(pauses))
    if pauses
    else 0.0
)

total_pause_duration = (
    float(np.sum(pauses))
    if pauses
    else 0.0
)


# ============================================================
# SILENCE BASED ON WHISPER
# ============================================================

whisper_silence = max(
    0,
    duration - speaking_time
)

whisper_silence_ratio = (
    whisper_silence / duration * 100
    if duration > 0
    else 0
)


# ============================================================
# FILLER WORD DETECTION
# ============================================================

filler_patterns = {

    "um": r"\bum+\b",

    "uh": r"\buh+\b",

    "er": r"\ber+\b",

    "like": r"\blike\b",

    "actually": r"\bactually\b",

    "basically": r"\bbasically\b",

    "literally": r"\bliterally\b",

    "you know": r"\byou know\b",

    "i mean": r"\bi mean\b",

    "sort of": r"\bsort of\b",

    "kind of": r"\bkind of\b"
}


full_text = " ".join(
    item["text"]
    for item in segment_data
).lower()


filler_counts = {}

total_fillers = 0


for name, pattern in filler_patterns.items():

    count = len(
        re.findall(
            pattern,
            full_text
        )
    )

    filler_counts[name] = count
    total_fillers += count


filler_rate = (
    total_fillers / word_count * 100
    if word_count > 0
    else 0
)


# ============================================================
# PITCH
# ============================================================

print("Estimating pitch...")

try:

    f0, voiced_flag, voiced_prob = librosa.pyin(
        audio_normalized,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C6"),
        sr=sr,
        frame_length=2048,
        hop_length=512
    )

    valid_pitch = f0[
        ~np.isnan(f0)
    ]

    if len(valid_pitch) > 0:

        average_pitch = float(
            np.mean(valid_pitch)
        )

        minimum_pitch = float(
            np.min(valid_pitch)
        )

        maximum_pitch = float(
            np.max(valid_pitch)
        )

        pitch_std = float(
            np.std(valid_pitch)
        )

    else:

        average_pitch = 0
        minimum_pitch = 0
        maximum_pitch = 0
        pitch_std = 0

except Exception as error:

    print(
        "Pitch warning:",
        error
    )

    average_pitch = 0
    minimum_pitch = 0
    maximum_pitch = 0
    pitch_std = 0


# ============================================================
# VOICE STABILITY
# ============================================================

# Coefficient of variation of RMS.
# Lower extreme variation = more stable volume.

if abs(average_volume) > 0:

    volume_stability = max(
        0,
        100 - (volume_std * 5)
    )

else:

    volume_stability = 0


volume_stability = min(
    100,
    volume_stability
)


# ============================================================
# SPEAKING RATE INTERPRETATION
# ============================================================

if 120 <= active_wpm <= 160:

    rate_quality = "GOOD"

elif 100 <= active_wpm < 120:

    rate_quality = "SLIGHTLY SLOW"

elif 160 < active_wpm <= 180:

    rate_quality = "SLIGHTLY FAST"

elif active_wpm < 100:

    rate_quality = "SLOW"

else:

    rate_quality = "FAST"


# ============================================================
# PAUSE INTERPRETATION
# ============================================================

if total_pauses == 0:

    pause_quality = "NO SIGNIFICANT PAUSES"

elif average_pause <= 1.0:

    pause_quality = "GOOD"

elif average_pause <= 2.0:

    pause_quality = "MODERATE"

else:

    pause_quality = "LONG PAUSES"


# ============================================================
# FILLER INTERPRETATION
# ============================================================

if filler_rate <= 1:

    filler_quality = "EXCELLENT"

elif filler_rate <= 3:

    filler_quality = "GOOD"

elif filler_rate <= 6:

    filler_quality = "MODERATE"

else:

    filler_quality = "HIGH"


# ============================================================
# SIMPLE FEATURE SCORE
# ============================================================
#
# IMPORTANT:
# This is NOT the final interview confidence score.
#
# It is only a technical voice-quality indicator.
#


# Rate score

if 120 <= active_wpm <= 160:

    rate_score = 100

elif 100 <= active_wpm < 120:

    rate_score = 85

elif 160 < active_wpm <= 180:

    rate_score = 85

elif 80 <= active_wpm < 100:

    rate_score = 70

elif 180 < active_wpm <= 200:

    rate_score = 70

else:

    rate_score = 50


# Pause score

if total_pauses == 0:

    pause_score = 80

elif average_pause <= 1.0:

    pause_score = 100

elif average_pause <= 2.0:

    pause_score = 80

elif average_pause <= 3.0:

    pause_score = 60

else:

    pause_score = 40


# Filler score

if filler_rate <= 1:

    filler_score = 100

elif filler_rate <= 3:

    filler_score = 85

elif filler_rate <= 6:

    filler_score = 70

else:

    filler_score = 50


technical_voice_score = (
    rate_score * 0.40
    +
    pause_score * 0.25
    +
    filler_score * 0.20
    +
    volume_stability * 0.15
)


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 72)
print("                    VOICE ANALYSIS V2 REPORT")
print("=" * 72)

print()

print(f"Detected Language      : {info.language}")
print(
    f"Language Probability   : "
    f"{info.language_probability:.2f}"
)

print()

print(f"Duration               : {duration:.2f} sec")
print(f"Speaking Time          : {speaking_time:.2f} sec")
print(f"Word Count             : {word_count}")

print()

print(
    f"Overall Speaking Rate  : "
    f"{overall_wpm:.1f} words/min"
)

print(
    f"Active Speaking Rate   : "
    f"{active_wpm:.1f} words/min"
)

print(
    f"Rate Assessment        : "
    f"{rate_quality}"
)

print()

print(
    f"Energy Silence         : "
    f"{energy_silence_duration:.2f} sec"
)

print(
    f"Energy Silence Ratio   : "
    f"{energy_silence_ratio:.1f}%"
)

print(
    f"Whisper Silence        : "
    f"{whisper_silence:.2f} sec"
)

print(
    f"Whisper Silence Ratio  : "
    f"{whisper_silence_ratio:.1f}%"
)

print()

print(
    f"Total Pauses           : "
    f"{total_pauses}"
)

print(
    f"Total Pause Duration   : "
    f"{total_pause_duration:.2f} sec"
)

print(
    f"Average Pause          : "
    f"{average_pause:.2f} sec"
)

print(
    f"Longest Pause          : "
    f"{longest_pause:.2f} sec"
)

print(
    f"Pause Assessment       : "
    f"{pause_quality}"
)

print()

print(
    f"Average Volume         : "
    f"{average_volume:.2f} dB"
)

print(
    f"Volume Variation       : "
    f"{volume_std:.2f}"
)

print(
    f"Volume Stability       : "
    f"{volume_stability:.1f}/100"
)

print()

print(
    f"Average Pitch          : "
    f"{average_pitch:.1f} Hz"
)

print(
    f"Minimum Pitch          : "
    f"{minimum_pitch:.1f} Hz"
)

print(
    f"Maximum Pitch          : "
    f"{maximum_pitch:.1f} Hz"
)

print(
    f"Pitch Variation        : "
    f"{pitch_std:.1f} Hz"
)

print()

print(
    f"Total Filler Words     : "
    f"{total_fillers}"
)

print(
    f"Filler Rate            : "
    f"{filler_rate:.2f}%"
)

print(
    f"Filler Assessment      : "
    f"{filler_quality}"
)

print()

print("FILLER WORD BREAKDOWN")
print("-" * 45)

for name, count in filler_counts.items():

    if count > 0:

        print(
            f"{name:<18}: {count}"
        )

print()

print("-" * 45)

print(
    f"Rate Feature Score     : "
    f"{rate_score:.1f}/100"
)

print(
    f"Pause Feature Score    : "
    f"{pause_score:.1f}/100"
)

print(
    f"Filler Feature Score   : "
    f"{filler_score:.1f}/100"
)

print(
    f"Volume Feature Score   : "
    f"{volume_stability:.1f}/100"
)

print()

print(
    f"TECHNICAL VOICE SCORE  : "
    f"{technical_voice_score:.1f}/100"
)

print()

print("=" * 72)
print("                 VOICE ANALYSIS V2 FINISHED")
print("=" * 72)
print()