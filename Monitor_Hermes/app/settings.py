from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Monitor Hermes"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
