VibeCheck

Know exactly why and where you lost the room.

VibeCheck is a communication-practice tool. You record yourself doing a practice session (a talk, a pitch, an interview answer — whatever you're rehearsing), and the app analyzes the recording to tell you how you actually came across: your confidence, eye contact, speaking pace, filler word usage, dominant emotion, and head posture. Over multiple sessions, it tracks how you're improving.

What it does
Record — capture a practice session using your camera and mic, directly in the browser.
Analyze — the recording is uploaded to the backend, which runs it through video and audio analysis (emotion detection, eye contact tracking, head pose estimation, speech-to-text, and voice/speech pattern analysis).
Review — get a scored breakdown (confidence, communication, body language, eye contact %, speaking pace, filler word rate) plus written AI feedback on what to improve.
Track progress — compare sessions over time to see trends: is your eye contact improving? Are filler words going down?
Features
Email/password signup & login (JWT-based auth)
In-browser video + audio recording (no external recording software needed)
Automated analysis per session:
Voice — speaking rate, pause count, filler word rate
Eye contact — percentage of time spent looking at the camera
Emotion — dominant emotion detected and confidence score
Head pose — posture/orientation tracking
High-level scores — confidence, communication, body language
AI-generated written feedback per session
Session history (Activity page) with all past recordings and scores
Progress tracking (Progress page) — trend charts across sessions, biggest wins, filler word tracking over time
Tech Stack
Frontend
Framework: React + Vite
Routing: React Router
Styling: Plain CSS (per-page stylesheets)
Auth: JWT stored in localStorage, sent as Authorization: Bearer header
Backend
Framework: Python (FastAPI-style, run via Uvicorn)
Auth: OAuth2 password flow (/auth/signup, /auth/login), JWT issuance
Video handling: file upload endpoint, stored server-side, processed asynchronously into scores
Analysis modules: emotion detection, eye contact tracking, head pose estimation, speech-to-text, voice/speaking-pattern analysis
Project structure
VibeCheck/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── audio_extractor.py
│   │   │   ├── emotion_detector.py
│   │   │   ├── emotion.py
│   │   │   ├── eye_contact.py
│   │   │   ├── face_detector.py
│   │   │   ├── feature_engine.py
│   │   │   ├── head_pose.py
│   │   │   ├── video_analyzer.py
│   │   │   └── voice_analyzer.py
│   │   │
│   │   ├── models/
│   │   │   ├── .gitkeep
│   │   │   ├── face_landmarker.task
│   │   │   ├── user.py
│   │   │   └── video.py
│   │   │
│   │   ├── routes/
│   │   │   ├── .gitkeep
│   │   │   ├── auth.py
│   │   │   └── video.py
│   │   │
│   │   ├── services/
│   │   │   ├── .gitkeep
│   │   │   ├── auth.py
│   │   │   └── security.py
│   │   │
│   │   ├── database.py
│   │   └── main.py
│   │
│   ├── test_files/
│   │   ├── test_emotion_module.py
│   │   ├── test_emotion_v3.py
│   │   ├── test_emotion.py
│   │   ├── test_eye_contact.py
│   │   ├── test_head_pose.py
│   │   ├── test_speech_to_text.py
│   │   ├── test_video_analysis.py
│   │   └── test_voice_analysis.py
│   │
│   ├── uploads/
│   │   ├── sample.mp4
│   │   ├── sample.wav
│   │   ├── test.py
│   │   └── video_analysis.json
│   │
│   ├── .env
│   ├── .gitignore
│   ├── README.md
│   ├── requirements.txt
│   └── run.py
│
├── frontend/
│   └── vite-project/
│       ├── public/
│       │
│       ├── src/
│       │   ├── assets/
│       │   │   ├── hero.png
│       │   │   ├── logo.svg
│       │   │   └── vite.svg
│       │   │
│       │   ├── activity.css
│       │   ├── activity.jsx
│       │   ├── analysis.css
│       │   ├── analysis.jsx
│       │   ├── api.js
│       │   ├── App.css
│       │   ├── App.jsx
│       │   ├── dashboard.css
│       │   ├── dashboard.jsx
│       │   ├── index.css
│       │   ├── login.jsx
│       │   ├── main.jsx
│       │   ├── progress.css
│       │   ├── progress.jsx
│       │   ├── record.css
│       │   └── record.jsx
│       │
│       ├── .env
│       ├── .gitignore
│       ├── eslint.config.js
│       ├── index.html
│       ├── package-lock.json
│       ├── package.json
│       ├── README.md
│       └── vite.config.js
│
└── README.md
