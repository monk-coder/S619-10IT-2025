from sqlalchemy.orm import Session
import models
from auth import get_password_hash
from schemas import UserCreate, ContactCreate, NoteCreate, NoteUpdate

class UserCRUD:
    @staticmethod
    def get_user_by_username(db: Session, username: str):
        return db.query(models.User).filter(models.User.username == username).first()

    @staticmethod
    def create_user(db: Session, user: UserCreate):
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

class ContactCRUD:
    @staticmethod
    def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
        return db.query(models.Contact).filter(models.Contact.user_id == user_id).offset(skip).limit(limit).all()

    @staticmethod
    def create_contact(db: Session, contact: ContactCreate, user_id: int):
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

    @staticmethod
    def get_contact(db: Session, contact_id: int, user_id: int):
        return db.query(models.Contact).filter(
            models.Contact.id == contact_id,
            models.Contact.user_id == user_id
        ).first()

    @staticmethod
    def delete_contact(db: Session, contact_id: int, user_id: int):
        contact = ContactCRUD.get_contact(db, contact_id, user_id)
        if contact:
            db.delete(contact)
            db.commit()
        return contact

class NoteCRUD:
    @staticmethod
    def get_notes(db: Session, contact_id: int, user_id: int):
        return db.query(models.Note).filter(
            models.Note.contact_id == contact_id,
            models.Note.user_id == user_id
        ).all()

    @staticmethod
    def create_note(db: Session, note: NoteCreate, contact_id: int, user_id: int):
        db_note = models.Note(
            **note.dict(),
            contact_id=contact_id,
            user_id=user_id
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        return db_note

    @staticmethod
    def get_note(db: Session, note_id: int, user_id: int):
        return db.query(models.Note).filter(
            models.Note.id == note_id,
            models.Note.user_id == user_id
        ).first()

    @staticmethod
    def update_note(db: Session, note_id: int, note: NoteUpdate, user_id: int):
        db_note = NoteCRUD.get_note(db, note_id, user_id)
        if db_note:
            for key, value in note.dict(exclude_unset=True).items():
                setattr(db_note, key, value)
            db.commit()
            db.refresh(db_note)
        return db_note

    @staticmethod
    def delete_note(db: Session, note_id: int, user_id: int):
        note = NoteCRUD.get_note(db, note_id, user_id)
        if note:
            db.delete(note)
            db.commit()
        return note


user_repository = UserCRUD()
contact_repository = ContactCRUD()
note_repository = NoteCRUD()