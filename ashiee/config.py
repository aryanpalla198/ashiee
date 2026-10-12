"""
Ashiee Configuration & Security Settings
Defines security tiers, workspace policies, model selections, and defaults.
"""

import os
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field


class ExecutionPolicy(str, Enum):
    ALWAYS_PROCEED = "always-proceed"
    REQUEST_REVIEW = "request-review"
    STRICT = "strict"


class FileAccessPolicy(str, Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


class ModelProvider(str, Enum):
    ANTIGRAVITY = "antigravity"
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


class SecurityConfig(BaseModel):
    execution_policy: ExecutionPolicy = Field(
        default=ExecutionPolicy.ALWAYS_PROCEED,
        description="Controls whether terminal commands need user approval."
    )
    file_access_policy: FileAccessPolicy = Field(
        default=FileAccessPolicy.ALLOW,
        description="Controls access to files outside workspace root."
    )
    disallowed_commands: list[str] = Field(
        default_factory=lambda: ["format", "rm -rf /", "del /f /s /q C:\\", "shutdown"],
        description="Commands strictly blocked from execution."
    )
    command_timeout_seconds: int = Field(
        default=120,
        description="Timeout for background or shell command execution."
    )


def _load_env_vars():
    env_files = [
        Path(os.getcwd()) / ".env",
        Path(__file__).parent.parent / ".env",
        Path.home() / ".ashiee" / ".env",
    ]
    for env_path in env_files:
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k not in os.environ and v:
                            os.environ[k] = v
            except Exception:
                pass

_load_env_vars()


class LLMConfig(BaseModel):
    provider: ModelProvider = Field(
        default_factory=lambda: (
            ModelProvider.GEMINI if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
            else (ModelProvider.OPENAI if os.getenv("OPENAI_API_KEY") else ModelProvider.MOCK)
        )
    )
    model_name: str = Field(default="gemini-2.5-flash")
    api_key: str | None = Field(
        default_factory=lambda: (
            os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
        )
    )
    temperature: float = Field(default=0.2)
    max_output_tokens: int = Field(default=8192)


class AshieeConfig(BaseModel):
    workspace_root: Path = Field(default_factory=lambda: Path(os.getcwd()).resolve())
    app_data_dir: Path = Field(default_factory=lambda: Path.home() / ".ashiee")
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

    def ensure_directories(self) -> None:
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        (self.app_data_dir / "sessions").mkdir(parents=True, exist_ok=True)
        (self.app_data_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        (self.app_data_dir / "scratch").mkdir(parents=True, exist_ok=True)
