"""Public data models, enums, and coordinate helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import TypeAlias

from .exceptions import VworldInvalidParameterError


def _require_finite_number(value: float, name: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise VworldInvalidParameterError(f"{name} must be finite")
    return number


def _require_lat(value: float) -> float:
    number = _require_finite_number(value, "lat")
    if not -90 <= number <= 90:
        raise VworldInvalidParameterError("lat must be between -90 and 90")
    return number


def _require_lon(value: float) -> float:
    number = _require_finite_number(value, "lon")
    if not -180 <= number <= 180:
        raise VworldInvalidParameterError("lon must be between -180 and 180")
    return number


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


@dataclass(frozen=True, slots=True)
class LonLat:
    """WGS84 longitude/latitude point.

    VWorld point parameters are ``x,y``. For EPSG:4326 that means
    ``lon,lat``. Use this model when the order should be explicit.
    """

    lon: float
    lat: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "lon", _require_lon(self.lon))
        object.__setattr__(self, "lat", _require_lat(self.lat))

    def as_xy(self) -> tuple[float, float]:
        """Return the VWorld point order: ``(x, y) == (lon, lat)``."""

        return (self.lon, self.lat)


@dataclass(frozen=True, slots=True)
class LatLon:
    """WGS84 latitude/longitude point for common Korean "위경도" usage."""

    lat: float
    lon: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "lat", _require_lat(self.lat))
        object.__setattr__(self, "lon", _require_lon(self.lon))

    def as_xy(self) -> tuple[float, float]:
        """Return the VWorld point order: ``(x, y) == (lon, lat)``."""

        return (self.lon, self.lat)

    def as_lonlat(self) -> LonLat:
        """Return the equivalent :class:`LonLat` value."""

        return LonLat(lon=self.lon, lat=self.lat)


@dataclass(frozen=True, slots=True)
class BBox:
    """Bounding box in VWorld order: ``minx,miny,maxx,maxy``."""

    minx: float
    miny: float
    maxx: float
    maxy: float

    def __post_init__(self) -> None:
        minx = _require_finite_number(self.minx, "minx")
        miny = _require_finite_number(self.miny, "miny")
        maxx = _require_finite_number(self.maxx, "maxx")
        maxy = _require_finite_number(self.maxy, "maxy")
        if minx > maxx:
            raise VworldInvalidParameterError("minx must be less than or equal to maxx")
        if miny > maxy:
            raise VworldInvalidParameterError("miny must be less than or equal to maxy")
        object.__setattr__(self, "minx", minx)
        object.__setattr__(self, "miny", miny)
        object.__setattr__(self, "maxx", maxx)
        object.__setattr__(self, "maxy", maxy)

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
