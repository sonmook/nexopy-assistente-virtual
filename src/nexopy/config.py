from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
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
    feedback_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("NEXOPY_FEEDBACK_PATH", str(ROOT_DIR / "outputs" / "feedback.sqlite3"))
        )
    )
    min_similarity: float = field(
        default_factory=lambda: float(os.getenv("MIN_SIMILARITY", "0.16"))
    )
    top_k: int = field(default_factory=lambda: int(os.getenv("TOP_K", "3")))
    use_gemini: bool = _as_bool(os.getenv("USE_GEMINI"), default=False)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()

    def __post_init__(self) -> None:
        if (
            isinstance(self.min_similarity, bool)
            or not isinstance(self.min_similarity, (int, float))
            or not math.isfinite(self.min_similarity)
            or not 0 < self.min_similarity <= 1
        ):
            raise ValueError("MIN_SIMILARITY deve ser finito, maior que zero e no máximo 1.")
        if isinstance(self.top_k, bool) or not isinstance(self.top_k, int) or self.top_k < 1:
            raise ValueError("TOP_K deve ser um inteiro positivo.")

    @property
    def gemini_enabled(self) -> bool:
        return self.use_gemini and bool(self.gemini_api_key)
