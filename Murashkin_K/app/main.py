import uvicorn
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from datetime import timedelta
import aiohttp
import csv
import io
from typing import List
import os

from database import get_db, engine
import models
import schemas
from crud import UserCRUD, ContactCRUD, NoteCRUD
from config import settings, app, STATIC_DIR
from auth import authenticate_user, create_access_token, get_current_user

models.Base.metadata.create_all(bind=engine)

@app.get("/")
async def read_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": "Frontend files not found. Please check if static files are properly installed."}


@app.post("/api/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = UserCRUD.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    db_user_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    return UserCRUD.create_user(db=db, user=user)


@app.post("/api/token", response_model=schemas.Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/random-users")
async def get_random_users():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://randomuser.me/api/?results=10') as response:
            data = await response.json()
            users = []
            for user in data['results']:
                users.append({
                    'first_name': user['name']['first'],
                    'last_name': user['name']['last'],
                    'email': user['email'],
                    'phone': user['phone'],
                    'picture': user['picture']['large']
                })
            return users


@app.get("/api/contacts", response_model=List[schemas.Contact])
async def read_contacts(
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    contacts = ContactCRUD.get_contacts(db, user_id=current_user.id, skip=skip, limit=limit)
    return contacts


@app.post("/api/contacts", response_model=schemas.Contact)
async def create_contact(
    contact: schemas.Contact,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return ContactCRUD.create_contact(db=db, contact=contact, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@app.delete("/api/contacts/{contact_id}")
async def delete_contact(
        contact_id: int,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    contact = ContactCRUD.delete_contact(db, contact_id=contact_id, user_id=current_user.id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}


@app.get("/api/contacts/{contact_id}/notes", response_model=List[schemas.Note])
async def read_notes(
        contact_id: int,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return NoteCRUD.get_notes(db, contact_id=contact_id, user_id=current_user.id)


@app.post("/api/contacts/{contact_id}/notes", response_model=schemas.Note)
async def create_note(
        contact_id: int,
        note: schemas.Note,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return NoteCRUD.create_note(db=db, note=note, contact_id=contact_id, user_id=current_user.id)


@app.put("/api/notes/{note_id}", response_model=schemas.Note)
async def update_note(
        note_id: int,
        note: schemas.Note,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_note = NoteCRUD.update_note(db, note_id=note_id, note=note, user_id=current_user.id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return db_note


@app.delete("/api/notes/{note_id}")
async def delete_note(
        note_id: int,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    note = NoteCRUD.delete_note(db, note_id=note_id, user_id=current_user.id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}


@app.get("/api/contacts/export/csv")
async def export_contacts_csv(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    contacts = ContactCRUD.get_contacts(db, user_id=current_user.id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['First Name', 'Last Name', 'Email', 'Phone'])

    for contact in contacts:
        writer.writerow([contact.first_name, contact.last_name, contact.email, contact.phone])

    output.seek(0)

    return Response(
        content=output.getvalue(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=contacts.csv'}
    )


if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

