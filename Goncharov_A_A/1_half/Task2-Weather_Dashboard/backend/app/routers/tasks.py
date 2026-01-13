from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..models import User, WeatherTask


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[schemas.TaskOut])
def list_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  tasks = (
    db.query(WeatherTask)
    .filter(WeatherTask.user_id == current_user.id)
    .order_by(WeatherTask.created_at.desc())
    .all()
  )
  return tasks


@router.post("", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: schemas.TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  task = WeatherTask(user_id=current_user.id, title=payload.title, city=payload.city)
  db.add(task)
  db.commit()
  db.refresh(task)
  return task


@router.patch("/{task_id}/toggle", response_model=schemas.TaskOut)
def toggle_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  task = db.query(WeatherTask).filter(WeatherTask.id == task_id, WeatherTask.user_id == current_user.id).first()
  if not task:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
  task.is_done = not task.is_done
  db.commit()
  db.refresh(task)
  return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  task = db.query(WeatherTask).filter(WeatherTask.id == task_id, WeatherTask.user_id == current_user.id).first()
  if not task:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
  db.delete(task)
  db.commit()
