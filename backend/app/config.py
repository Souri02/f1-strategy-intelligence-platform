from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "F1 Strategy Intelligence Platform"
    data_dir: Path = Path("./data")
    default_season: int = 2024
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="F1_",
        extra="ignore",
    )


settings = Settings()
