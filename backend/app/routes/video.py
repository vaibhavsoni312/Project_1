from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from uuid import uuid4
from datetime import datetime
import shutil
import os

from app.database import db
from app.services.auth import verify_token

from app.ai.video_analyzer import analyze_video
from app.ai.insights import generate_insights


router = APIRouter(
    prefix="/video",
    tags=["Video"]
)


UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    token_data: dict = Depends(verify_token)
):

    # ============================================================
    # VALIDATE VIDEO
    # ============================================================

    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400,
            detail="Only video files are allowed"
        )


    # ============================================================
    # CREATE UNIQUE FILENAME
    # ============================================================

    extension = file.filename.split(".")[-1]

    filename = f"{uuid4()}.{extension}"

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )


    # ============================================================
    # SAVE VIDEO
    # ============================================================

    with open(filepath, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )


    # ============================================================
    # SAVE INITIAL VIDEO RECORD
    # ============================================================

    video = {

        "user_id": token_data["user_id"],

        "filename": filename,

        "filepath": filepath,

        "uploaded_at": datetime.utcnow(),

        "status": "processing"
    }


    result = await db.videos.insert_one(video)


    # ============================================================
    # AI ANALYSIS PIPELINE
    # ============================================================

    try:

        # --------------------------------------------------------
        # VIDEO ANALYZER
        # --------------------------------------------------------

        analysis_result = analyze_video(
            filepath
        )


        # --------------------------------------------------------
        # SHARED TIMELINE
        # DELTA DETECTION
        # AI FEEDBACK
        # --------------------------------------------------------

        insights = generate_insights(
            analysis_result
        )


        # --------------------------------------------------------
        # UPDATE MONGODB
        # --------------------------------------------------------

        await db.videos.update_one(

            {
                "_id": result.inserted_id
            },

            {
                "$set": {

                    "analysis": analysis_result,

                    "deltas": insights["deltas"],

                    "feedback": insights["feedback"],

                    "status": "completed"
                }
            }
        )


    # ============================================================
    # ANALYSIS FAILED
    # ============================================================

    except Exception as e:

        await db.videos.update_one(

            {
                "_id": result.inserted_id
            },

            {
                "$set": {

                    "status": "failed",

                    "analysis_error": str(e)
                }
            }
        )


        raise HTTPException(

            status_code=500,

            detail=f"Video analysis failed: {str(e)}"
        )


    # ============================================================
    # FINAL RESPONSE
    # ============================================================

    return {

        "message":
            "Video uploaded and analyzed successfully",

        "video_id":
            str(result.inserted_id),

        "filename":
            filename,

        "status":
            "completed",

        "deltas":
            insights["deltas"],

        "feedback":
            insights["feedback"]
    }

    