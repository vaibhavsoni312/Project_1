# app/ai/audio_extractor.py

import subprocess
import os


def extract_audio(video_path):
    audio_path = os.path.splitext(video_path)[0] + ".wav"

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-ac", "1", "-ar", "16000",
            audio_path,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return audio_path