"""Shared configuration loader utilities."""

import json
from pathlib import Path

from pydantic import BaseModel


class Config(BaseModel):
    """Configuration model for repo and year."""

    repo: str
    year: int


def load_config() -> Config:
    """Load configuration from config.json."""
    # config.json is in the project root, one level up from backend/
    config_path = Path(__file__).parent.parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(
            "config.json not found. Please create it with repo and year."
        )
    with open(config_path, encoding="utf-8") as f:
        return Config.model_validate(json.load(f))

