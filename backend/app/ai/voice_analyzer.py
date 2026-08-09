# app/ai/voice_analyzer.py

import re
import numpy as np
import librosa
from faster_whisper import WhisperModel


WHISPER_MODEL = "base"
SAMPLE_RATE = 16000
SILENCE_DB = -35
MIN_PAUSE = 0.35

FILLER_PATTERNS = {
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
    "kind of": r"\bkind of\b",
}

# Model loaded once at import time (not per-request — otherwise every
# upload would reload Whisper, which is slow)
_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")


def analyze_voice(audio_file):
    """
    Runs voice analysis on an audio file and returns a dict
    matching feature_engine.calculate_voice_features() input format.
    """

    audio, sr = librosa.load(audio_file, sr=SAMPLE_RATE, mono=True)
    duration = len(audio) / sr

    if duration <= 0:
        return _empty_result()

    peak = np.max(np.abs(audio))
    audio_normalized = audio / peak if peak > 0 else audio.copy()

    # ---------------- VOLUME ----------------
    rms = librosa.feature.rms(y=audio_normalized, frame_length=2048, hop_length=512)[0]
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    volume_std = float(np.std(rms_db))

    # ---------------- TRANSCRIPTION ----------------
    segments, info = _model.transcribe(
        audio_file,
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300},
        word_timestamps=True,
    )

    segment_data = []
    all_words = []

    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        all_words.extend(re.findall(r"\b[\w'-]+\b", text))
        segment_data.append({
            "start": float(segment.start),
            "end": float(segment.end),
            "text": text,
        })

    word_count = len(all_words)

    speaking_time = sum(
        max(0, item["end"] - item["start"]) for item in segment_data
    )

    active_wpm = (word_count / speaking_time * 60) if speaking_time > 0 else 0

    # ---------------- PAUSES ----------------
    pauses = []
    for i in range(1, len(segment_data)):
        gap = segment_data[i]["start"] - segment_data[i - 1]["end"]
        if gap >= MIN_PAUSE:
            pauses.append(gap)

    total_pauses = len(pauses)
    average_pause = float(np.mean(pauses)) if pauses else 0.0

    # ---------------- SILENCE ----------------
    whisper_silence = max(0, duration - speaking_time)
    whisper_silence_ratio = (whisper_silence / duration * 100) if duration > 0 else 0

    # ---------------- FILLERS ----------------
    full_text = " ".join(item["text"] for item in segment_data).lower()
    total_fillers = sum(
        len(re.findall(pattern, full_text)) for pattern in FILLER_PATTERNS.values()
    )
    filler_rate = (total_fillers / word_count * 100) if word_count > 0 else 0

    # ---------------- PITCH ----------------
    try:
        f0, _, _ = librosa.pyin(
            audio_normalized,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C6"),
            sr=sr,
            frame_length=2048,
            hop_length=512,
        )
        valid_pitch = f0[~np.isnan(f0)]
        pitch_std = float(np.std(valid_pitch)) if len(valid_pitch) > 0 else 0.0
    except Exception:
        pitch_std = 0.0

    return {
        "speaking_rate": round(active_wpm, 2),
        "silence_ratio": round(whisper_silence_ratio, 2),
        "pause_count": total_pauses,
        "average_pause": round(average_pause, 2),
        "filler_rate": round(filler_rate, 2),
        "pitch_variation": round(pitch_std, 2),
        "volume_variation": round(volume_std, 2),
        "word_count": word_count,
        "duration": round(duration, 2),
        "language": info.language,
    }


def _empty_result():
    return {
        "speaking_rate": 0, "silence_ratio": 0, "pause_count": 0,
        "average_pause": 0, "filler_rate": 0, "pitch_variation": 0,
        "volume_variation": 0, "word_count": 0, "duration": 0, "language": "unknown",
    }