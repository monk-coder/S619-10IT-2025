from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

load_dotenv()

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

    SQLALCHEMY_DATABASE_URL: str = os.getenv("SQLALCHEMY_DATABASE_URL")

settings = Settings()



app = FastAPI(title="Contact Manager API")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(CURRENT_DIR, "static")

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()