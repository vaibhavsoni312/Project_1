from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from uuid import uuid4
from datetime import datetime
import shutil
import os

from app.database import db
from app.services.auth import verify_token

router = APIRouter(
    prefix="/video",
    tags=["Video"]
)

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    token_data: dict = Depends(verify_token)
):

    if not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400,
            detail="Only video files are allowed"
        )

    extension = file.filename.split(".")[-1]

    filename = f"{uuid4()}.{extension}"

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    video = {
        "user_id": token_data["user_id"],
        "filename": filename,
        "filepath": filepath,
        "uploaded_at": datetime.utcnow()
    }

    result = await db.videos.insert_one(video)

    return {
        "message": "Video uploaded successfully",
        "video_id": str(result.inserted_id),
        "filename": filename
    }