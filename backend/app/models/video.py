from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VideoInDB(BaseModel):
    id: Optional[str] = None
    user_id: str
    filename: str
    filepath: str
    uploaded_at: datetime