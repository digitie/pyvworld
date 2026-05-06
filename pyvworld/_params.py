"""Parameter normalization helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import Enum
from math import isfinite
from typing import Any

from .exceptions import VworldInvalidParameterError
from .models import BBox, BBoxLike, LatLon, LonLat, PointLike

Params = dict[str, Any]


def clean_params(params: Mapping[str, Any]) -> Params:
    """Remove ``None`` values and convert Python values to VWorld query values."""

    cleaned: Params = {}
    for key, value in params.items():
        if value is None:
            continue
        cleaned[key] = query_value(value)
    return cleaned


def query_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (list, tuple)):
        return [query_value(item) for item in value]
    return value


def csv(value: str | Iterable[Any] | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return ",".join(str(query_value(item)) for item in value)


def bbox(value: BBoxLike | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, BBox):
        value = value.as_tuple()
    if len(value) != 4:
        raise VworldInvalidParameterError("bbox must contain minx, miny, maxx, maxy")
    _require_finite(value, "bbox")
    return ",".join(_format_number(part) for part in value)


def point(value: PointLike) -> str:
    if isinstance(value, str):
        if "," not in value:
            raise VworldInvalidParameterError("point must use the 'x,y' format")
        return value
    if isinstance(value, (LatLon, LonLat)):
        value = value.as_xy()
    if len(value) != 2:
        raise VworldInvalidParameterError("point must contain x and y")
    _require_finite(value, "point")
    return ",".join(_format_number(part) for part in value)


def pixel_size(value: str | tuple[int, int]) -> str:
    if isinstance(value, str):
        if "," not in value:
            raise VworldInvalidParameterError("size must use the 'width,height' format")
        return value
    if len(value) != 2:
        raise VworldInvalidParameterError("size must contain width and height")
    width, height = value
    if width <= 0 or height <= 0:
        raise VworldInvalidParameterError("size width and height must be positive")
    return f"{width},{height}"


def validate_page_size(size: int) -> None:
    if not 1 <= size <= 1000:
        raise VworldInvalidParameterError("size must be between 1 and 1000")


def validate_page(page: int) -> None:
    if page < 1:
        raise VworldInvalidParameterError("page must be at least 1")


def validate_zoom(zoom: int, *, min_zoom: int = 6, max_zoom: int = 18) -> None:
    if not min_zoom <= zoom <= max_zoom:
        raise VworldInvalidParameterError(f"zoom must be between {min_zoom} and {max_zoom}")


def validate_static_size(size_value: tuple[int, int] | str) -> None:
    if isinstance(size_value, str):
        parts = size_value.split(",")
        if len(parts) != 2:
            raise VworldInvalidParameterError("size must use the 'width,height' format")
        try:
            width, height = int(parts[0]), int(parts[1])
        except ValueError as exc:
            raise VworldInvalidParameterError("size must contain integer width and height") from exc
    else:
        width, height = size_value
    if width <= 0 or height <= 0:
        raise VworldInvalidParameterError("size width and height must be positive")
    if width > 1024 or height > 1024:
        raise VworldInvalidParameterError("static map size must not exceed 1024,1024")


def _require_finite(values: Iterable[float], name: str) -> None:
    for value in values:
        if not isfinite(float(value)):
            raise VworldInvalidParameterError(f"{name} values must be finite")


def _format_number(value: float) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return str(number)
