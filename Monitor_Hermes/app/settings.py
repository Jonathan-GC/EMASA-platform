from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Monitor Hermes"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    # Broker MQTT
    BROKER_URL: str
    BROKER_PORT: int = 1883

    # MongoDB
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_INITDB_ROOT_USERNAME: str
    MONGO_INITDB_ROOT_PASSWORD: str
    MONGO_URI: str
    MONGO_DB: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    WS_SECRET: str

    # External Services
    SERVICE_API_KEY: str
    ATLAS_HOST_URL: str = "http://localhost:8000"
    ATLAS_VERIFY_SSL: bool = True

    # SSL/TLS Configuration for WSS (WebSocket Secure)
    SSL_KEYFILE: str | None = None
    SSL_CERTFILE: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def mongo_uri(self) -> str:
        return (
            f"mongodb://{self.MONGO_INITDB_ROOT_USERNAME}:{self.MONGO_INITDB_ROOT_PASSWORD}"
            f"@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB}"
        )

    @property
    def redis_uri(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"


settings = Settings()
