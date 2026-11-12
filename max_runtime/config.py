from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Entity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity_id: str = Field(pattern=r"^(light|switch|media_player|scene)\.[a-z0-9_]+$")
    aliases: list[str] = Field(min_length=1)
    actions: list[Literal["turn_on", "turn_off", "volume_set", "media_play", "media_pause",
                          "select_source"]] = Field(default_factory=lambda: ["turn_on", "turn_off"])


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state_dir: Path = Path.home() / ".local/share/max"
    household: str = "home"
    public_url: str = ""
    api_token: str = Field(min_length=32, repr=False)
    identity_salt: str = Field(min_length=32, repr=False)
    bridge_token: str = Field(default="", repr=False)
    alexa_skill_id: str = ""
    alexa_users: list[str] = Field(default_factory=list, repr=False)
    owner_alexa_user: str = Field(default="", repr=False)
    ha_url: str = "http://127.0.0.1:8123"
    ha_token: str = Field(default="", repr=False)
    ha_refresh_token: str = Field(default="", repr=False)
    ha_client_id: str = "http://localhost:8787/"
    ha_authorize_url: str = ""
    entities: dict[str, Entity] = Field(default_factory=dict)
    openclaw_bin: str = "openclaw"
    openclaw_agent: str = Field(default="max", pattern=r"^[a-z0-9_-]+$")
    engine_timeout: float = Field(default=120, ge=5, le=600)
    searxng_url: str = "http://127.0.0.1:8888"
    worker_count: int = Field(default=2, ge=1, le=4)
    max_pending: int = Field(default=50, ge=1, le=200)
    retention_days: int = Field(default=30, ge=1, le=365)

    @model_validator(mode="after")
    def validate_separation(self):
        if self.bridge_token and self.bridge_token == self.api_token:
            raise ValueError("La clave de voz debe ser distinta de la clave de administración")
        if self.owner_alexa_user and self.owner_alexa_user not in self.alexa_users:
            raise ValueError("El perfil del operador debe ser un usuario Alexa autorizado")
        return self

    @classmethod
    def load(cls):
        path = Path(os.environ.get("MAX_CONFIG", Path.home() / ".config/max/config.json"))
        return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save(self):
        path = Path(os.environ.get("MAX_CONFIG", Path.home() / ".config/max/config.json"))
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = path.with_suffix(".tmp")
        temporary.touch(mode=0o600, exist_ok=True)
        temporary.chmod(0o600)
        temporary.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    @property
    def db_path(self):
        return self.state_dir / "max.sqlite3"
