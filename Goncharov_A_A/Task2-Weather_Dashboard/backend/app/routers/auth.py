from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..config import get_settings
from ..dependencies import get_current_user
from ..database import get_db
from ..models import User
from ..security import create_access_token, get_password_hash, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
  email = payload.email.lower()
  existing = db.query(User).filter(User.email == email).first()
  if existing:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь уже существует")
  user = User(email=email, hashed_password=get_password_hash(payload.password))
  db.add(user)
  db.commit()
  db.refresh(user)
  return user


@router.post("/login", response_model=schemas.Token)
def login_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
  email = payload.email.lower()
  user = db.query(User).filter(User.email == email).first()
  if not user or not verify_password(payload.password, user.hashed_password):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные")
  token = create_access_token(user.email, timedelta(minutes=settings.access_token_expire_minutes))
  return schemas.Token(access_token=token)


@router.get("/me", response_model=schemas.UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
  return current_user
