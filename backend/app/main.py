from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes import video

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Backend Running 🚀"}


app.include_router(auth_router)
app.include_router(video.router)