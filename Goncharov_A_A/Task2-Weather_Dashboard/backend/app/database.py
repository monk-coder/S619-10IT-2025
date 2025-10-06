from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

from .config import get_settings


settings = get_settings()


def _get_engine():
  if settings.database_url.startswith("sqlite"):
    return create_engine(settings.database_url, connect_args={"check_same_thread": False})
  return create_engine(settings.database_url)


engine = _get_engine()
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


class Base(DeclarativeBase):
  pass


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
