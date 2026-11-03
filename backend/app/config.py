from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore", env_prefix="LQ_")
    database_url: str = "sqlite:///./labquality.db"
    storage_dir: str = "./storage"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cookie_secure: bool = False
    session_hours: int = 8
    model_api_key: str = ""
    model_id: str = "muse-spark-1.3"
    model_base_url: str = "https://api.meta.ai/v1"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_starttls: bool = True
    odk_url: str = ""
    odk_email: str = ""
    odk_password: str = ""

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_from and self.smtp_username and self.smtp_password)


@lru_cache
def settings() -> Settings:
    return Settings()
