from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from app.config import settings
import hashlib

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    # Check for legacy SHA256 hash (64 hex chars)
    if len(hashed) == 64:
        try:
            # Try to interpret as hex
            int(hashed, 16)
            # It is likely a SHA256 hash
            legacy_hash = hashlib.sha256(plain.encode()).hexdigest()
            return legacy_hash == hashed
        except ValueError:
            pass
            
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    # Default to 30 mins if not set
    expire_minutes = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    
    # Default secret/algo if not set
    secret = getattr(settings, "SECRET_KEY", "secret")
    algo = getattr(settings, "ALGORITHM", "HS256")
    
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, secret, algorithm=algo)


def decode_token(token: str):
    secret = getattr(settings, "SECRET_KEY", "secret")
    algo = getattr(settings, "ALGORITHM", "HS256")
    try:
        data = jwt.decode(token, secret, algorithms=[algo])
        return data
    except Exception:
        return None