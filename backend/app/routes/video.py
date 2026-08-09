# app/routes/video.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from uuid import uuid4
from datetime import datetime
import shutil
import os

from app.database import db
from app.services.auth import verify_token

from app.ai.video_analyzer import analyze_video
from app.ai.audio_extractor import extract_audio
from app.ai.voice_analyzer import analyze_voice
from app.ai.feature_engine import (
    adapt_video_result,
    build_features,
    generate_simple_feedback,
)


router = APIRouter(prefix="/video", tags=["Video"])

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    token_data: dict = Depends(verify_token)
):
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video files are allowed")

    extension = file.filename.split(".")[-1]
    filename = f"{uuid4()}.{extension}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    video = {
        "user_id": token_data["user_id"],
        "filename": filename,
        "filepath": filepath,
        "uploaded_at": datetime.utcnow(),
        "status": "processing",
    }

    result = await db.videos.insert_one(video)

    try:
        # ---------------- VIDEO ANALYSIS ----------------
        analysis_result = analyze_video(filepath)

        # ---------------- VOICE ANALYSIS ----------------
        audio_path = extract_audio(filepath)
        voice_result = analyze_voice(audio_path)

        # ---------------- FEATURE ENGINE ----------------
        voice_data, eye_data, emotion_data, head_pose_data = adapt_video_result(
            analysis_result, voice_result
        )

        final_scores = build_features(
            voice_data, eye_data, emotion_data, head_pose_data
        )

        feedback = generate_simple_feedback(final_scores)

        await db.videos.update_one(
            {"_id": result.inserted_id},
            {"$set": {
                "analysis": analysis_result,
                "voice_analysis": voice_result,
                "final_scores": final_scores,
                "feedback": feedback,
                "status": "completed",
            }}
        )

    except Exception as e:
        await db.videos.update_one(
            {"_id": result.inserted_id},
            {"$set": {"status": "failed", "analysis_error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")

    return {
        "message": "Video uploaded and analyzed successfully",
        "video_id": str(result.inserted_id),
        "filename": filename,
        "status": "completed",
        "final_scores": final_scores,
        "feedback": feedback,
    }
@router.get("/my-sessions")
async def get_my_sessions(
    token_data: dict = Depends(verify_token)
):
    cursor = db.videos.find(
        {"user_id": token_data["user_id"]}
    ).sort("uploaded_at", -1)

    videos = await cursor.to_list(length=100)

    sessions = []
    for v in videos:
        sessions.append({
            "id": str(v["_id"]),
            "filename": v.get("filename"),
            "uploaded_at": v.get("uploaded_at").isoformat() if v.get("uploaded_at") else None,
            "status": v.get("status", "processing"),
            "final_scores": v.get("final_scores"),
            "feedback": v.get("feedback"),
        })

    return {"sessions": sessions}