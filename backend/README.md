# VibeCheck — Backend
FastAPI backend powering VibeCheck's video/voice analysis pipeline —
handles auth, video upload, and AI-driven scoring.
## Tech Stack

- **Framework:** FastAPI
- **Database:** MongoDB (Atlas) via Motor (async driver)
- **Auth:** JWT (python-jose) + bcrypt password hashing
- **AI/ML:**
  - MediaPipe — face landmarks, eye contact, head pose
  - DeepFace — facial emotion recognition
  - Faster-Whisper — speech-to-text
  - Librosa — audio feature extraction (pitch, volume, pauses)

## Project Structure

backend/
├── app/
│   ├── ai/
│   │   ├── audio_extractor.py
│   │   ├── emotion_detector.py
│   │   ├── emotion.py
│   │   ├── eye_contact.py
│   │   ├── face_detector.py
│   │   ├── feature_engine.py
│   │   ├── head_pose.py
│   │   ├── video_analyzer.py
│   │   └── voice_analyzer.py
│   │
│   ├── models/
│   │   ├── .gitkeep
│   │   ├── face_landmarker.task
│   │   ├── user.py
│   │   └── video.py
│   │
│   ├── routes/
│   │   ├── .gitkeep
│   │   ├── auth.py
│   │   └── video.py
│   │
│   ├── services/
│   │   ├── .gitkeep
│   │   ├── auth.py
│   │   └── security.py
│   │
│   ├── database.py
│   └── main.py
│
├── test_files/
│   ├── test_emotion_module.py
│   ├── test_emotion_v3.py
│   ├── test_emotion.py
│   ├── test_eye_contact.py
│   ├── test_head_pose.py
│   ├── test_speech_to_text.py
│   ├── test_video_analysis.py
│   └── test_voice_analysis.py
│
├── uploads/
│   ├── sample.mp4
│   ├── sample.wav
│   ├── test.py
│   └── video_analysis.json
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── run.py
---

## Setup

### 1. Create virtual environment

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
```
### 2. activate virtual environement

```bash
.\.venv\Scripts\Activate.ps1
```
### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install ffmpeg

Required for extracting audio from uploaded videos.

- Windows: `winget install ffmpeg` (restart terminal after)
- Confirm with: `ffmpeg -version`

### 5. Environment variables

Create a `.env` file in `backend/`:

env
**SECRET_KEY**= secret key
**ALGORITHM**=HS256
**MONGODB_URI**= in env

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

Server runs at `http://127.0.0.1:8000`
Interactive API docs: `http://127.0.0.1:8000/docs`

---

## API Endpoints

| Method | Endpoint         | Auth required | Description                          |
|--------|------------------|:---:|---------------------------------------|
| POST   | `/auth/signup`   | ❌ | Create a new account                  |
| POST   | `/auth/login`    | ❌ | Login, returns JWT token              |
| GET    | `/auth/me`       | ✅ | Get current logged-in user            |
| POST   | `/video/upload`  | ✅ | Upload video → returns scores + feedback |

`/video/upload` expects `multipart/form-data` with a `file` field, and an
`Authorization: Bearer <token>` header.

---

## Testing the AI pipeline standalone

Without going through the API, you can test the full pipeline directly:

```bash
python test.py
```

This runs `video_analyzer` + `voice_analyzer` + `feature_engine` on
`sample.mp4` and prints the final scores + feedback.

---
