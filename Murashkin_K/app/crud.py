from sqlalchemy.orm import Session
import models
import schemas
from auth import get_password_hash

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Contact).filter(models.Contact.user_id == user_id).offset(skip).limit(limit).all()


def create_contact(db: Session, contact: schemas.ContactCreate, user_id: int):
    # Проверяем, существует ли уже контакт с таким email у этого пользователя
    existing_contact = db.query(models.Contact).filter(
        models.Contact.email == contact.email,
        models.Contact.user_id == user_id
    ).first()

    if existing_contact:
        raise ValueError("Contact already exists in your list")

    db_contact = models.Contact(**contact.dict(), user_id=user_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contact(db: Session, contact_id: int, user_id: int):
    return db.query(models.Contact).filter(
        models.Contact.id == contact_id,
        models.Contact.user_id == user_id
    ).first()

def delete_contact(db: Session, contact_id: int, user_id: int):
    contact = get_contact(db, contact_id, user_id)
    if contact:
        db.delete(contact)
        db.commit()
    return contact

def get_notes(db: Session, contact_id: int, user_id: int):
    return db.query(models.Note).filter(
        models.Note.contact_id == contact_id,
        models.Note.user_id == user_id
    ).all()

def create_note(db: Session, note: schemas.NoteCreate, contact_id: int, user_id: int):
    db_note = models.Note(
        **note.dict(),
        contact_id=contact_id,
        user_id=user_id
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def get_note(db: Session, note_id: int, user_id: int):
    return db.query(models.Note).filter(
        models.Note.id == note_id,
        models.Note.user_id == user_id
    ).first()

def update_note(db: Session, note_id: int, note: schemas.NoteUpdate, user_id: int):
    db_note = get_note(db, note_id, user_id)
    if db_note:
        for key, value in note.dict().items():
            setattr(db_note, key, value)
        db.commit()
        db.refresh(db_note)
    return db_note

def delete_note(db: Session, note_id: int, user_id: int):
    note = get_note(db, note_id, user_id)
    if note:
        db.delete(note)
        db.commit()
    return note