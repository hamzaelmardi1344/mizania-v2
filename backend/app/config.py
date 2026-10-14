from dataclasses import dataclass, field
import os
from pathlib import Path
from urllib.parse import urlsplit

@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./data/mizania.db"))
    storage: Path = field(default_factory=lambda: Path(os.getenv("STORAGE_PATH", "./data/files")))
    origin: str = field(default_factory=lambda: os.getenv("APP_ORIGIN", "http://localhost:3000").rstrip("/"))
    environment: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    session_seconds: int = 8 * 3600
    max_upload: int = 10 * 1024 * 1024
    clamav_host: str = field(default_factory=lambda: os.getenv("CLAMAV_HOST", ""))
    clamav_port: int = 3310
    @property
    def secure(self) -> bool:
        return self.origin.startswith("https://")
    def validate(self):
        if self.environment not in {"development", "test", "production"}:
            raise RuntimeError("Invalid APP_ENV")
        if self.environment == "production":
            # Legal/operational sign-off is a release gate, not a promise in code.
            if not self.secure or urlsplit(self.origin).hostname in {"localhost", "127.0.0.1"}:
                raise RuntimeError("Production requires the real HTTPS origin")
            if not self.database_url.startswith("postgresql") or not self.clamav_host:
                raise RuntimeError("Production requires PostgreSQL and file scanning")
            if os.getenv("RELEASE_REVIEW_APPROVED") != "true":
                raise RuntimeError("Production release requires documented security and regulatory review")
