"""Small data models and constants used by the client."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TileLayer(str, Enum):
    """VWorld background tile layers."""

    BASE = "Base"
    WHITE = "white"
    MIDNIGHT = "midnight"
    HYBRID = "Hybrid"
    SATELLITE = "Satellite"


@dataclass(frozen=True, slots=True)
class BinaryResponse:
    """Binary response returned by image and tile helpers."""

    content: bytes
    content_type: str | None = None


@dataclass(frozen=True, slots=True)
class TextResponse:
    """Text response returned by OGC XML helpers."""

    text: str
    content_type: str | None = None
