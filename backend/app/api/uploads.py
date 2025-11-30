import os
import time
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Header, status
from app.config import settings
from app.utils.security import decode_token
from app.models.user import User
import aiofiles  # pip install aiofiles

router = APIRouter(prefix="/uploads")

from app.api.deps import get_current_user

# ensure upload dir exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/")
async def upload(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    filename = f"{user.id}_{int(time.time())}_{file.filename}"
    path = os.path.join(settings.UPLOAD_DIR, filename)

    # Async write (recommended)
    async with aiofiles.open(path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    # --- fallback (synchronous) if you don't want aiofiles ---
    # content = await file.read()
    # with open(path, "wb") as f:
    #     f.write(content)

    url = f"/uploads/{filename}"
    return {"url": url}
