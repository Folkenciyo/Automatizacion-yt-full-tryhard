from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/automation_yt"
    redis_url: str = "redis://localhost:6379/0"
    youtube_api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    credentials_dir: str = "/app/credentials"
    render_output_dir: str = "/app/output"
    environment: str = "development"
    base_url: str = "http://localhost:8000"
    render_server_url: str = "https://render.folkenland.online"


settings = Settings()
