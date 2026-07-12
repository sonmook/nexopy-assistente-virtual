from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


@dataclass(frozen=True)
class Settings:
    root_dir: Path = ROOT_DIR
    knowledge_path: Path = ROOT_DIR / "data" / "conhecimentos.json"
    evaluation_path: Path = ROOT_DIR / "tests" / "casos_avaliacao.json"
    outputs_dir: Path = ROOT_DIR / "outputs"
    min_similarity: float = float(os.getenv("MIN_SIMILARITY", "0.16"))
    top_k: int = int(os.getenv("TOP_K", "3"))
    use_gemini: bool = _as_bool(os.getenv("USE_GEMINI"), default=False)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()

    @property
    def gemini_enabled(self) -> bool:
        return self.use_gemini and bool(self.gemini_api_key)
