import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = 4096

    langsmith_api_key: str | None = Field(
        None,
        alias="LANGSMITH_API_KEY",
    )
    langsmith_project: str = "forgeai"
    langsmith_tracing: bool = True

    working_directory: Path = Field(
        default_factory=Path.cwd,
    )
    forgeai_dir: Path = Field(
        default=Path(".forgeai"),
    )
    plans_directory: Path = Field(
        default=Path(".forgeai/plans"),
    )

    max_iterations: int = 50
    approval_required: bool = True

    checkpoint_db: str = "checkpoints.db"

    log_level: str = "INFO"
    debug: bool = False

    @property
    def mcp_config_path(self) -> Path:
        return self.forgeai_dir / "mcp_config.json"

    def __init__(self, **data):
        super().__init__(**data)

        if not self.forgeai_dir.is_absolute():
            self.forgeai_dir = self.working_directory / self.forgeai_dir

        db_dir = self.forgeai_dir / "db"
        db_dir.mkdir(parents=True, exist_ok=True)

        rules_dir = self.forgeai_dir / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        prompts_dir = self.forgeai_dir / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)

        if not self.plans_directory.is_absolute():
            object.__setattr__(
                self,
                "plans_directory",
                self.working_directory / self.plans_directory,
            )

        self.plans_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.checkpoint_db.startswith(("file:", "sqlite:", "/")):
            db_path = db_dir / self.checkpoint_db
            object.__setattr__(
                self,
                "checkpoint_db",
                str(db_path),
            )

    def configure_langsmith(self) -> None:
        if self.langsmith_api_key and self.langsmith_tracing:
            os.environ["LANGSMITH_API_KEY"] = self.langsmith_api_key
            os.environ["LANGSMITH_PROJECT"] = self.langsmith_project
            os.environ["LANGSMITH_TRACING"] = "true"


settings = Settings()
settings.configure_langsmith()
