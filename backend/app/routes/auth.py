from fastapi import APIRouter, HTTPException

from app.database import db
from app.models.user import UserSignup, UserLogin
from app.services.security import hash_password, verify_password
from app.services.auth import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/signup")
async def signup(user: UserSignup):

    existing_user = await db.users.find_one({
        "email": user.email
    })

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    hashed_password = hash_password(user.password)

    new_user = {
        "name": user.name,
        "email": user.email,
        "hashed_password": hashed_password
    }

    result = await db.users.insert_one(new_user)

    token = create_access_token({
        "user_id": str(result.inserted_id)
    })

    return {
        "message": "Signup Successful",
        "access_token": token
    }


@router.post("/login")
async def login(user: UserLogin):

    existing_user = await db.users.find_one({
        "email": user.email
    })

    if not existing_user:
        raise HTTPException(
            status_code=400,
            detail="Invalid email or password"
        )

    if not verify_password(
        user.password,
        existing_user["hashed_password"]
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid email or password"
        )

    token = create_access_token({
        "user_id": str(existing_user["_id"])
    })

    return {
        "message": "Login Successful",
        "access_token": token
    }