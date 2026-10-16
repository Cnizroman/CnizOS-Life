from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
import uuid

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(sub: str, expires_delta: timedelta | None = None) -> str:
    exp = datetime.now(tz=timezone.utc) + (expires_delta or timedelta(seconds=settings.JWT_ACCESS_TTL))
    to_encode = {"sub": sub, "exp": exp, "jti": str(uuid.uuid4()), "type": "access"}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(sub: str) -> str:
    exp = datetime.now(tz=timezone.utc) + timedelta(seconds=settings.JWT_REFRESH_TTL)
    to_encode = {"sub": sub, "exp": exp, "jti": str(uuid.uuid4()), "type": "refresh"}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(str(e))
