import os
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=str(env_path), override=False)


def get_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    db_path = Path(os.getenv("DB_FILE", "./revin.db")).resolve()
    return f"sqlite:///{db_path}"


class Settings:
    database_url: str = get_database_url()
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    app_name: str = os.getenv("APP_NAME", "revin-mini")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")


settings = Settings()


