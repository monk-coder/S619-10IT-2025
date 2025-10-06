from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
  email: EmailStr
  password: str = Field(min_length=6)


class UserOut(BaseModel):
  id: int
  email: EmailStr
  created_at: datetime

  class Config:
    from_attributes = True


class Token(BaseModel):
  access_token: str
  token_type: str = "bearer"


class TokenPayload(BaseModel):
  sub: Optional[str] = None
  exp: Optional[int] = None


class TaskBase(BaseModel):
  title: str
  city: str


class TaskCreate(TaskBase):
  pass


class TaskOut(TaskBase):
  id: int
  is_done: bool
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True


class HistoryItem(BaseModel):
  id: int
  city: str
  searched_at: datetime

  class Config:
    from_attributes = True
