from urllib.parse import urlsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PublicSettings(BaseSettings):
    # Deliberately do not load the local app's .env or Settings.
    model_config = SettingsConfigDict(env_prefix="SMCR_PUBLIC_", env_file=None, extra="ignore")
    base_url: str = "http://127.0.0.1:8010"

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in ("", "/")
            or (parsed.scheme != "https" and not (
                parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "::1")
            ))
        ):
            raise ValueError("Set a canonical HTTPS origin, or HTTP localhost for development.")
        return value.rstrip("/")

    @property
    def allowed_hosts(self) -> list[str]:
        return [urlsplit(self.base_url).netloc]
