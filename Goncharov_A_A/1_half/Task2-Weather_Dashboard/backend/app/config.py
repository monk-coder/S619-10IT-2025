from functools import lru_cache

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
  api_v1_prefix: str = Field("/api", alias="API_V1_PREFIX")
  secret_key: str = Field("super-secret-key", alias="SECRET_KEY")
  access_token_expire_minutes: int = Field(60 * 24, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
  algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
  database_url: str = Field("sqlite:///./weather.db", alias="DATABASE_URL")
  openweather_key: str | None = Field(default=None, alias="OPEN_WEATHER_KEY")

  class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
  return Settings()
