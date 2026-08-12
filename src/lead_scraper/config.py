from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Application configuration."""

    project_root: Path
    data_dir: Path
    database_path: Path


def load_config() -> AppConfig:
    package_root = Path(__file__).resolve().parents[2]
    data_dir = package_root / "data"
    return AppConfig(
        project_root=package_root,
        data_dir=data_dir,
        database_path=data_dir / "leads.sqlite",
    )

