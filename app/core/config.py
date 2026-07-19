import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_base_dir = Path(__file__).resolve().parent.parent
_project_dir = _base_dir.parent


class Settings:
    app_name: str = "Verse Vault"
    base_dir: Path = _base_dir
    project_dir: Path = _project_dir
    templates_dir: Path = base_dir / "templates"
    static_dir: Path = base_dir / "static"
    database_path: Path = Path(
        os.getenv("DATABASE_PATH", str(_project_dir / "bible-sqlite.db"))
    )
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{database_path.resolve()}",
    )


settings = Settings()
