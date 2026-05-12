"""Public data models, enums, and coordinate helpers."""

from __future__ import annotations

from enum import Enum
from math import isfinite
from typing import Any, TypeAlias

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator, model_validator

from .exceptions import VworldInvalidParameterError


def _require_finite_number(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise VworldInvalidParameterError(f"{name} must be a finite number") from exc
    if not isfinite(number):
        raise VworldInvalidParameterError(f"{name} must be finite")
    return number


def _require_lat(value: Any) -> float:
    number = _require_finite_number(value, "lat")
    if not -90 <= number <= 90:
        raise VworldInvalidParameterError("lat must be between -90 and 90")
    return number


def _require_lon(value: Any) -> float:
    number = _require_finite_number(value, "lon")
    if not -180 <= number <= 180:
        raise VworldInvalidParameterError("lon must be between -180 and 180")
    return number


class _FrozenModel(BaseModel):
    """Shared immutable Pydantic model settings for public value objects."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)


class Crs(str, Enum):
    """Coordinate reference systems supported by VWorld reference pages."""

    WGS84 = "EPSG:4326"
    GRS80 = "EPSG:4019"
    WEB_MERCATOR = "EPSG:3857"
    GOOGLE_MERCATOR = "EPSG:900913"
    WEST_GRS80_500K = "EPSG:5180"
    CENTRAL_GRS80_500K = "EPSG:5181"
    JEJU_GRS80 = "EPSG:5182"
    EAST_GRS80_500K = "EPSG:5183"
    EAST_SEA_GRS80_500K = "EPSG:5184"
    WEST_GRS80 = "EPSG:5185"
    CENTRAL_GRS80 = "EPSG:5186"
    EAST_GRS80 = "EPSG:5187"
    EAST_SEA_GRS80 = "EPSG:5188"
    UTMK = "EPSG:5179"


class SearchType(str, Enum):
    """Search API ``type`` values."""

    PLACE = "place"
    ADDRESS = "address"
    DISTRICT = "district"
    ROAD = "road"


class AddressCategory(str, Enum):
    """Search API address category values."""

    ROAD = "road"
    PARCEL = "parcel"


class DistrictCategory(str, Enum):
    """Search API district category values."""

    LEVEL1 = "L1"
    LEVEL2 = "L2"
    LEVEL3 = "L3"
    LEVEL4 = "L4"


class AddressType(str, Enum):
    """Geocoder address type values."""

    ROAD = "road"
    PARCEL = "parcel"


class ReverseGeocodeType(str, Enum):
    """Reverse geocoder address type values."""

    ROAD = "road"
    PARCEL = "parcel"
    BOTH = "both"


class LegendType(str, Enum):
    """Legend image ``type`` values."""

    ALL = "ALL"
    LAYER = "LAYER"
    SUB = "SUB"


class ImageFormat(str, Enum):
    """Common image format values accepted by VWorld image endpoints."""

    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    BMP = "bmp"


class StaticMapBase(str, Enum):
    """StaticMap base map names documented by VWorld."""

    NONE = "NONE"
    GRAPHIC = "GRAPHIC"
    GRAPHIC_WHITE = "GRAPHIC_WHITE"
    GRAPHIC_NIGHT = "GRAPHIC_NIGHT"
    PHOTO = "PHOTO"
    PHOTO_HYBRID = "PHOTO_HYBRID"
    HYBRID = "PHOTO_HYBRID"


class TileLayer(str, Enum):
    """VWorld background tile layers."""

    BASE = "Base"
    WHITE = "white"
    MIDNIGHT = "midnight"
    HYBRID = "Hybrid"
    SATELLITE = "Satellite"


class LonLat(_FrozenModel):
    """WGS84 longitude/latitude point.

    VWorld point parameters are ``x,y``. For EPSG:4326 that means
    ``lon,lat``. Use this model when the order should be explicit.
    """

    lon: float
    lat: float

    def __init__(self, lon: float, lat: float) -> None:
        super().__init__(lon=lon, lat=lat)

    @field_validator("lon", mode="before")
    @classmethod
    def _validate_lon(cls, value: Any) -> float:
        return _require_lon(value)

    @field_validator("lat", mode="before")
    @classmethod
    def _validate_lat(cls, value: Any) -> float:
        return _require_lat(value)

    def as_xy(self) -> tuple[float, float]:
        """Return the VWorld point order: ``(x, y) == (lon, lat)``."""

        return (self.lon, self.lat)


class LatLon(_FrozenModel):
    """WGS84 latitude/longitude point for common ``lat, lon`` usage."""

    lat: float
    lon: float

    def __init__(self, lat: float, lon: float) -> None:
        super().__init__(lat=lat, lon=lon)

    @field_validator("lat", mode="before")
    @classmethod
    def _validate_lat(cls, value: Any) -> float:
        return _require_lat(value)

    @field_validator("lon", mode="before")
    @classmethod
    def _validate_lon(cls, value: Any) -> float:
        return _require_lon(value)

    def as_xy(self) -> tuple[float, float]:
        """Return the VWorld point order: ``(x, y) == (lon, lat)``."""

        return (self.lon, self.lat)

    def as_lonlat(self) -> LonLat:
        """Return the equivalent :class:`LonLat` value."""

        return LonLat(lon=self.lon, lat=self.lat)


class BBox(_FrozenModel):
    """Bounding box in VWorld order: ``minx,miny,maxx,maxy``."""

    minx: float
    miny: float
    maxx: float
    maxy: float

    def __init__(self, minx: float, miny: float, maxx: float, maxy: float) -> None:
        super().__init__(minx=minx, miny=miny, maxx=maxx, maxy=maxy)

    @field_validator("minx", "miny", "maxx", "maxy", mode="before")
    @classmethod
    def _validate_finite(cls, value: Any, info: ValidationInfo) -> float:
        return _require_finite_number(value, str(info.field_name))

    @model_validator(mode="after")
    def _validate_order(self) -> BBox:
        if self.minx > self.maxx:
            raise VworldInvalidParameterError("minx must be less than or equal to maxx")
        if self.miny > self.maxy:
            raise VworldInvalidParameterError("miny must be less than or equal to maxy")
        return self

    @classmethod
    def from_latlon(
        cls,
        *,
        south: float,
        west: float,
        north: float,
        east: float,
    ) -> BBox:
        """Create an EPSG:4326 bbox from geographic names."""

        return cls(
            minx=_require_lon(west),
            miny=_require_lat(south),
            maxx=_require_lon(east),
            maxy=_require_lat(north),
        )

    def as_tuple(self) -> tuple[float, float, float, float]:
        """Return ``(minx, miny, maxx, maxy)``."""

        return (self.minx, self.miny, self.maxx, self.maxy)


PointLike: TypeAlias = str | tuple[float, float] | LatLon | LonLat
BBoxLike: TypeAlias = str | tuple[float, float, float, float] | BBox


def latlon(lat: float, lon: float) -> LatLon:
    """Create a validated WGS84 latitude/longitude point."""

    return LatLon(lat=lat, lon=lon)


def lonlat(lon: float, lat: float) -> LonLat:
    """Create a validated WGS84 longitude/latitude point."""

    return LonLat(lon=lon, lat=lat)


def bbox_from_latlon(*, south: float, west: float, north: float, east: float) -> BBox:
    """Create a VWorld-order bbox from geographic bounds."""

    return BBox.from_latlon(south=south, west=west, north=north, east=east)


class BinaryResponse(_FrozenModel):
    """Binary response returned by image and tile helpers."""

    content: bytes
    content_type: str | None = None

    def __init__(self, content: bytes, content_type: str | None = None) -> None:
        super().__init__(content=content, content_type=content_type)


class TextResponse(_FrozenModel):
    """Text response returned by OGC XML helpers."""

    text: str
    content_type: str | None = None

    def __init__(self, text: str, content_type: str | None = None) -> None:
        super().__init__(text=text, content_type=content_type)
