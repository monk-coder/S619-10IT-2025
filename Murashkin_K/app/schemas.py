from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    email: EmailStr = Field(..., example="john@example.com")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, example="securepassword123")


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class ContactBase(BaseModel):
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Doe")
    email: str = Field(..., example="john@example.com")
    phone: str = Field(..., example="+1234567890")
    picture: str = Field(..., example="https://example.com/photo.jpg")



class Contact(ContactBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class NoteBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, example="This is a note")


class Note(NoteBase):
    id: int
    contact_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
