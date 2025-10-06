from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_access_token


def _extract_token(authorization: str | None) -> str | None:
  if not authorization:
    return None
  parts = authorization.split()
  if len(parts) == 2 and parts[0].lower() == "bearer":
    return parts[1]
  return None


def get_current_user(
  db: Session = Depends(get_db),
  authorization: str | None = Header(default=None, alias="Authorization")
):
  token = _extract_token(authorization)
  if not token:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
  try:
    payload = decode_access_token(token)
  except ValueError:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None
  email = payload.get("sub")
  if not email:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
  user = db.query(User).filter(User.email == email).first()
  if not user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
  return user


def get_optional_user(
  db: Session = Depends(get_db),
  authorization: str | None = Header(default=None, alias="Authorization")
):
  token = _extract_token(authorization)
  if not token:
    return None
  try:
    payload = decode_access_token(token)
  except ValueError:
    return None
  email = payload.get("sub")
  if not email:
    return None
  return db.query(User).filter(User.email == email).first()
