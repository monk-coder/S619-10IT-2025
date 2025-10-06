from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..models import CityHistory, User


router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[schemas.HistoryItem])
def read_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  entries = (
    db.query(CityHistory)
    .filter(CityHistory.user_id == current_user.id)
    .order_by(CityHistory.searched_at.desc())
    .limit(20)
    .all()
  )
  return entries
