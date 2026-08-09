from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import certifi
import os

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = AsyncIOMotorClient(
    MONGODB_URI,
    tlsCAFile=certifi.where()
)

db = client[DATABASE_NAME]