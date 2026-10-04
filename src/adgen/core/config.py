import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PROMPTS = ROOT / "prompts"
FONTS = ROOT / "assets" / "fonts"

load_dotenv(ROOT / ".env")

GENERATOR_MODEL = "vertex_ai/gemini-3.1-flash-image"
PLANNER_MODEL = "vertex_ai/gemini-3.8-flash"
JUDGE_MODEL = "anthropic/claude-sonnet-5"
PANEL_MODELS = ("anthropic/claude-opus-5-5", "openai/gpt-5.5")

LOCKED_STRATEGY = "d2"
MAX_EDGE = 1024


@dataclass(frozen=True)
class ProxySettings:
    base_url: str
    api_key: str

    @classmethod
    def from_env(cls) -> "ProxySettings":
        base_url = os.environ.get("LITELLM_BASE_URL")
        api_key = os.environ.get("LITELLM_API_KEY")
        if not (base_url and api_key):
            raise RuntimeError("LITELLM_BASE_URL and LITELLM_API_KEY must be set in .env")
        return cls(base_url=base_url.rstrip("/").removesuffix("/v1"), api_key=api_key)
