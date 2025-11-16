from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Base schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    picture: Optional[str] = None


class NoteBase(BaseModel):
    content: str


# Create schemas (for POST requests)
class UserCreate(UserBase):
    password: str


class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    picture: Optional[str] = None

class NoteCreate(NoteBase):
    pass


# Update schemas (for PUT/PATCH requests)
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    picture: Optional[str] = None


class NoteUpdate(BaseModel):
    content: Optional[str] = None


# Response schemas (for GET responses)
class User(UserBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: str


class Contact(ContactBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Note(NoteBase):
    id: int
    contact_id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Detailed response schemas with relationships
class ContactWithNotes(Contact):
    notes: list[Note] = []


class UserWithContacts(User):
    contacts: list[Contact] = []


class NoteWithContact(Note):
    contact: Optional[Contact] = None


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None