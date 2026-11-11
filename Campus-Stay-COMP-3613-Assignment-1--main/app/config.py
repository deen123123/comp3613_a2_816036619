"""Settings loaded from the environment, falling back to .env then .env.example."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env_file() -> None:
    for name in (".env", ".env.example", "env.example"):
        path = ROOT / name
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            os.environ.setdefault(key.strip(), value)
        return


def _normalise_database_url(uri: str) -> str:
    # Render hands out postgres:// URLs; SQLAlchemy wants postgresql://
    if uri.startswith("postgres://"):
        uri = "postgresql://" + uri[len("postgres://"):]
    # Keep a relative SQLite file next to the project, whatever the cwd is.
    prefix = "sqlite:///"
    if uri.startswith(prefix) and not uri.startswith("sqlite:////") and ":memory:" not in uri:
        uri = prefix + str(ROOT / uri[len(prefix):])
    return uri


_load_env_file()


class Settings:
    app_name = "Campus Stay"

    def __init__(self) -> None:
        self.database_url = _normalise_database_url(
            os.environ.get("DATABASE_URI", "sqlite:///database.db")
        )
        self.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
        self.env = os.environ.get("ENV", "development").lower()
        self.port = int(os.environ.get("PORT") or os.environ.get("APP_PORT") or 5000)
        self.config_password = os.environ.get("CONFIG_PASSWORD", "")

    @property
    def is_production(self) -> bool:
        return self.env == "production"


settings = Settings()
