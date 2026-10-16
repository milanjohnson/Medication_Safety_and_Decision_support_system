# SOURCE: NOT IN PAPERS. Own configuration. Paths follow aakaash/CLAUDE.md (data/ at the repo
# root, gitignored; generated files under aakaash/artifacts/, gitignored).
"""Settings, read from the environment on every call so tests and users can override them."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

AAKAASH_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AAKAASH_DIR.parent


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    artifacts_dir: Path
    trace_path: Path
    encoder_name: str
    classifier_name: str


def get_settings() -> Settings:
    """FastAPI dependency. Override with MEDSAFE_DATA_DIR, MEDSAFE_ARTIFACTS_DIR,
    MEDSAFE_ENCODER, MEDSAFE_DDI_CLASSIFIER."""
    return Settings(
        data_dir=Path(os.environ.get("MEDSAFE_DATA_DIR", REPO_ROOT / "data")),
        artifacts_dir=Path(os.environ.get("MEDSAFE_ARTIFACTS_DIR", AAKAASH_DIR / "artifacts")),
        trace_path=AAKAASH_DIR / "PAPER_TRACE.md",
        encoder_name=os.environ.get("MEDSAFE_ENCODER", "tfidf"),
        classifier_name=os.environ.get("MEDSAFE_DDI_CLASSIFIER", "linear_baseline"),
    )
