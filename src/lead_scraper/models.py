from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lead:
    """Normalized business lead."""

    name: str
    phone: str | None = None
    address: str | None = None
    category: str | None = None
    source_query: str | None = None
    source_url: str | None = None

