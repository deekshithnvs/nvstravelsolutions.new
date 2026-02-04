import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "NVS Vendor Portal"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-dev")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480 # 8 hours
    
    # Essential Database URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{(Path(__file__).resolve().parent.parent / 'nvs_portal.db').as_posix()}")

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()


from fastapi.templating import Jinja2Templates

# Calculate Project Base Dir (parent of core/)
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))
