from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
  return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
  return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
  expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
  to_encode = {"sub": subject, "exp": expire}
  return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
  try:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
  except JWTError as exc:
    raise ValueError("Invalid token") from exc
