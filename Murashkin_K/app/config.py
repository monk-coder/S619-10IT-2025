from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # API Keys
    EMAIL_API_KEY: str = os.getenv("EMAIL_API_KEY")
    SMS_API_SECRET: str = os.getenv("SMS_API_SECRET")


settings = Settings()
