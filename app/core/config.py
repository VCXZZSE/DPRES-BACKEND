from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    DATABASE_URL: str
    API_HOST: str = '0.0.0.0'
    API_PORT: int = 8000
    FRONTEND_ORIGINS: str = 'http://localhost:5173'

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SMTP_HOST: str = ''
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ''
    SMTP_PASSWORD: str = ''
    SMTP_FROM_EMAIL: str = ''
    SMTP_USE_TLS: bool = True

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(',') if origin.strip()]

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_FROM_EMAIL)


settings = Settings()  # type: ignore
