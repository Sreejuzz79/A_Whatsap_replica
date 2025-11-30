# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.api.deps import get_current_user
from sqlalchemy import select
import traceback

router = APIRouter(prefix="/auth")

@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    print(f"DEBUG: get_profile returning user {user.id}: {user.username}, name={user.full_name}, avatar_len={len(user.avatar) if user.avatar else 0}")
    return {
        "id": user.id,
        "username": user.username,
        "profile_picture": user.avatar,
        "full_name": user.full_name,
        "about": user.about
    }


class ProfileUpdate(BaseModel):
    full_name: str = None
    about: str = None
    profile_picture: str = None


@router.patch("/profile")
async def update_profile(payload: ProfileUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.about is not None:
            user.about = payload.about
        if payload.profile_picture is not None:
            user.avatar = payload.profile_picture

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {
            "id": user.id,
            "username": user.username,
            "profile_picture": user.avatar,
            "full_name": user.full_name,
            "about": user.about
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"ERROR updating profile: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")


class RegisterIn(BaseModel):
    username: str
    password: str
    full_name: str = None


class LoginIn(BaseModel):
    username: str
    password: str


# dev-only debug wrapper for /auth/register
@router.post("/register")
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)):
    try:
        q = await db.execute(select(User).where(User.username == payload.username))
        existing = q.scalars().first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username taken")

        user = User(
            username=payload.username, 
            password_hash=hash_password(payload.password),
            full_name=payload.full_name
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        token = create_access_token(user.id)

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "about": user.about,
                "profile_picture": user.avatar
            },
            "access_token": token
        }

    except Exception as e:
        tb = traceback.format_exc()
        print(tb)  # prints to server console too
        # dev-only: return last 50 lines of trace in response
        raise HTTPException(status_code=500, detail={"error": str(e), "trace": tb.splitlines()[-50:]})


@router.post("/login")
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.username == payload.username))
    user = q.scalars().first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    token = create_access_token(user.id)
    print(f"DEBUG: login successful for user {user.id}: {user.username}, name={user.full_name}, avatar_len={len(user.avatar) if user.avatar else 0}")
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "about": user.about,
            "profile_picture": user.avatar
        },
        "access_token": token
    }
