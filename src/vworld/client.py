"""High-level client for VWorld HTTP endpoints."""

from __future__ import annotations

import os
from collections.abc import Iterator
from enum import Enum
from pathlib import Path
from typing import Any, TypeAlias
from urllib.parse import quote

from ._http import _VworldHttp
from ._params import (
    bbox as bbox_param,
)
from ._params import (
    clean_params,
    csv,
    pixel_size,
    point,
    validate_page,
    validate_page_size,
    validate_static_size,
    validate_zoom,
)
from .exceptions import VworldAuthError, VworldInvalidParameterError
from .models import (
    AddressCategory,
    AddressType,
    BBoxLike,
    BinaryResponse,
    Crs,
    DistrictCategory,
    ImageFormat,
    LatLon,
    LegendType,
    PointLike,
    ReverseGeocodeType,
    SearchType,
    StaticMapBase,
    TextResponse,
    TileLayer,
)
from .pagination import iter_pages as iter_vworld_pages
from .pagination import response_items

JsonObject = dict[str, Any]
SearchCategory: TypeAlias = (
    str
    | AddressCategory
    | DistrictCategory
    | list[str | AddressCategory | DistrictCategory]
    | tuple[str | AddressCategory | DistrictCategory, ...]
)
StringList: TypeAlias = str | list[str] | tuple[str, ...]


_REST_VERSION = "2.0"
_DEFAULT_FORMAT = "json"
_DEFAULT_ERROR_FORMAT = "json"
_DEFAULT_CRS = Crs.WGS84
_DEFAULT_OGC_CRS = Crs.GOOGLE_MERCATOR

_TILE_ZOOM_RANGES: dict[str, tuple[int, int]] = {
    TileLayer.BASE.value: (6, 19),
    TileLayer.WHITE.value: (6, 18),
    TileLayer.MIDNIGHT.value: (6, 18),
    TileLayer.HYBRID.value: (6, 19),
    TileLayer.SATELLITE.value: (6, 19),
}

_TILE_EXTENSIONS: dict[str, str] = {
    TileLayer.BASE.value: "png",
    TileLayer.WHITE.value: "png",
    TileLayer.MIDNIGHT.value: "png",
    TileLayer.HYBRID.value: "png",
    TileLayer.SATELLITE.value: "jpeg",
}


def _attr_filter(value: str | list[str] | tuple[str, ...] | None) -> str | None:
    if value is None or isinstance(value, str):
        return value
    return "|".join(value)


def _text_value(value: str | Enum) -> str:
    return str(value.value) if isinstance(value, Enum) else str(value)


def _read_env_file(path: str | os.PathLike[str]) -> dict[str, str]:
    env_path = Path(path)
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


class VworldClient:
    """Client entrypoint for VWorld REST, OGC, static image, and tile endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        domain: str | None = None,
        timeout: float = 10.0,
        max_retries: int = 2,
        retry_backoff: float = 0.5,
        session: Any | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("VWORLD_API_KEY") or os.getenv("VWORLD_KEY")
        self.domain = domain if domain is not None else os.getenv("VWORLD_DOMAIN")
        self.timeout = timeout
        self._http = (
            _VworldHttp(
                self.api_key,
                timeout=timeout,
                max_retries=max_retries,
                retry_backoff=retry_backoff,
                session=session,
            )
            if self.api_key
            else None
        )

    @classmethod
    def from_env(cls, **kwargs: Any) -> VworldClient:
        """Create a client from ``VWORLD_API_KEY`` or ``VWORLD_KEY``."""

        return cls(**kwargs)

    @classmethod
    def from_env_file(
        cls,
        path: str | os.PathLike[str] = ".env",
        **kwargs: Any,
    ) -> VworldClient:
        """Create a client from a local dotenv-style file."""

        values = _read_env_file(path)
        api_key = (
            kwargs.pop("api_key")
            if "api_key" in kwargs
            else values.get("VWORLD_API_KEY") or values.get("VWORLD_KEY")
        )
        domain = kwargs.pop("domain") if "domain" in kwargs else values.get("VWORLD_DOMAIN")
        return cls(api_key=api_key, domain=domain, **kwargs)

    def _require_http(self) -> _VworldHttp:
        if self._http is None:
            raise VworldAuthError("VWORLD_API_KEY is not set and api_key was not provided")
        return self._http

    def _with_domain(self, params: JsonObject, domain: str | None = None) -> JsonObject:
        if domain is not None:
            params["domain"] = domain
        elif self.domain:
            params["domain"] = self.domain
        return params

    # Search API 2.0
    def search(
        self,
        query: str,
        type: str | SearchType,
        *,
        category: SearchCategory | None = None,
        size: int = 10,
        page: int = 1,
        bbox: BBoxLike | None = None,
        crs: str | Crs = _DEFAULT_CRS,
        callback: str | None = None,
    ) -> JsonObject:
        """Call Search API 2.0 (``/req/search``)."""

        if not query:
            raise VworldInvalidParameterError("query must not be empty")
        normalized_type = _text_value(type).lower()
        if normalized_type not in {"place", "address", "district", "road"}:
            raise VworldInvalidParameterError("type must be place, address, district, or road")
        if normalized_type in {"address", "district"} and category is None:
            raise VworldInvalidParameterError(
                "category is required for address and district search"
            )
        validate_page_size(size)
        validate_page(page)

        params = {
            "service": "search",
            "request": "search",
            "version": _REST_VERSION,
            "format": _DEFAULT_FORMAT,
            "errorformat": _DEFAULT_ERROR_FORMAT,
            "query": query,
            "type": normalized_type,
            "category": csv(category),
            "size": size,
            "page": page,
            "bbox": bbox_param(bbox),
            "crs": crs,
            "callback": callback,
        }
        return self._require_http().get_json("/req/search", params)

    def search_place(self, query: str, **kwargs: Any) -> JsonObject:
        """Search places such as buildings, facilities, agencies, and stores."""

        return self.search(query, "place", **kwargs)

    def search_address(
        self,
        query: str,
        *,
        category: str | AddressCategory = AddressCategory.ROAD,
        **kwargs: Any,
    ) -> JsonObject:
        """Search road or parcel addresses."""

        return self.search(query, "address", category=category, **kwargs)

    def search_district(
        self,
        query: str,
        *,
        category: str | DistrictCategory = DistrictCategory.LEVEL4,
        **kwargs: Any,
    ) -> JsonObject:
        """Search administrative districts."""

        return self.search(query, "district", category=category, **kwargs)

    def search_road(self, query: str, **kwargs: Any) -> JsonObject:
        """Search road names."""

        return self.search(query, "road", **kwargs)

    def iter_search_pages(
        self,
        query: str,
        type: str | SearchType,
        *,
        category: SearchCategory | None = None,
        size: int = 1000,
        start_page: int = 1,
        max_pages: int = 100,
        max_items: int | None = None,
        bbox: BBoxLike | None = None,
        crs: str | Crs = _DEFAULT_CRS,
        callback: str | None = None,
    ) -> Iterator[JsonObject]:
        """VWorld ``response.page`` 메타데이터를 따라 Search API 페이지를 순회합니다."""

        yield from iter_vworld_pages(
            lambda page: self.search(
                query,
                type,
                category=category,
                size=size,
                page=page,
                bbox=bbox,
                crs=crs,
                callback=callback,
            ),
            start_page=start_page,
            max_pages=max_pages,
            max_items=max_items,
        )

    def iter_search_items(
        self,
        query: str,
        type: str | SearchType,
        *,
        category: SearchCategory | None = None,
        size: int = 1000,
        start_page: int = 1,
        max_pages: int = 100,
        max_items: int | None = None,
        bbox: BBoxLike | None = None,
        crs: str | Crs = _DEFAULT_CRS,
        callback: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Search API 결과 아이템을 여러 페이지에 걸쳐 순회합니다."""

        yielded = 0
        pages = self.iter_search_pages(
            query,
            type,
            category=category,
            size=size,
            start_page=start_page,
            max_pages=max_pages,
            max_items=max_items,
            bbox=bbox,
            crs=crs,
            callback=callback,
        )
        for payload in pages:
            for item in response_items(payload):
                if max_items is not None and yielded >= max_items:
                    return
                yield item
                yielded += 1

    # Geocoder API 2.0
    def get_coord(
        self,
        address: str,
        type: str | AddressType,
        *,
        refine: bool = True,
        simple: bool = False,
        crs: str | Crs = _DEFAULT_CRS,
        callback: str | None = None,
    ) -> JsonObject:
        """Convert an address to coordinates via Geocoder API 2.0."""

        if not address:
            raise VworldInvalidParameterError("address must not be empty")
        normalized_type = _text_value(type).lower()
        if normalized_type not in {"road", "parcel"}:
            raise VworldInvalidParameterError("type must be road or parcel")
        params = {
            "service": "address",
            "request": "getcoord",
            "version": _REST_VERSION,
            "format": _DEFAULT_FORMAT,
            "errorformat": _DEFAULT_ERROR_FORMAT,
            "type": normalized_type,
            "address": address,
            "refine": refine,
            "simple": simple,
            "crs": crs,
            "callback": callback,
        }
        return self._require_http().get_json("/req/address", params)

    def geocode(
        self,
        address: str,
        type: str | AddressType = AddressType.ROAD,
        **kwargs: Any,
    ) -> JsonObject:
        """Alias for :meth:`get_coord`."""

        return self.get_coord(address, type, **kwargs)

    def get_address(
        self,
        point_value: PointLike,
        *,
        type: str | ReverseGeocodeType = ReverseGeocodeType.BOTH,
        zipcode: bool = True,
        simple: bool = False,
        crs: str | Crs = _DEFAULT_CRS,
        callback: str | None = None,
    ) -> JsonObject:
        """Convert coordinates to road and/or parcel addresses."""

        normalized_type = _text_value(type).lower()
        if normalized_type not in {"road", "parcel", "both"}:
            raise VworldInvalidParameterError("type must be road, parcel, or both")
        params = {
            "service": "address",
            "request": "getaddress",
            "version": _REST_VERSION,
            "format": _DEFAULT_FORMAT,
            "errorformat": _DEFAULT_ERROR_FORMAT,
            "point": point(point_value),
            "type": normalized_type,
            "zipcode": zipcode,
            "simple": simple,
            "crs": crs,
            "callback": callback,
        }
        return self._require_http().get_json("/req/address", params)

    def reverse_geocode(self, point_value: PointLike, **kwargs: Any) -> JsonObject:
        """Alias for :meth:`get_address`."""

        return self.get_address(point_value, **kwargs)

    def reverse_geocode_latlon(self, lat: float, lon: float, **kwargs: Any) -> JsonObject:
        """Reverse geocode a WGS84 latitude/longitude point."""

        return self.get_address(LatLon(lat=lat, lon=lon), **kwargs)

    # 2D Data API 2.0
    def get_data_feature(
        self,
        data: str,
        *,
        geom_filter: str | None = None,
        attr_filter: StringList | None = None,
        columns: StringList | None = None,
        geometry: bool = True,
        attribute: bool = True,
        buffer: int | float | None = None,
        size: int = 10,
        page: int = 1,
        crs: str | Crs = _DEFAULT_CRS,
        callback: str | None = None,
        domain: str | None = None,
    ) -> JsonObject:
        """Query 2D Data API 2.0 features via ``/req/data``."""

        if not data:
            raise VworldInvalidParameterError("data must not be empty")
        validate_page_size(size)
        validate_page(page)
        params = self._with_domain(
            {
                "service": "data",
                "request": "GetFeature",
                "version": _REST_VERSION,
                "format": _DEFAULT_FORMAT,
                "errorformat": _DEFAULT_ERROR_FORMAT,
                "data": data,
                "geomFilter": geom_filter,
                "attrFilter": _attr_filter(attr_filter),
                "columns": csv(columns),
                "geometry": geometry,
                "attribute": attribute,
                "buffer": buffer,
                "size": size,
                "page": page,
                "crs": crs,
                "callback": callback,
            },
            domain,
        )
        return self._require_http().get_json("/req/data", params)

    def iter_data_feature_pages(
        self,
        data: str,
        *,
        geom_filter: str | None = None,
        attr_filter: StringList | None = None,
        columns: StringList | None = None,
        geometry: bool = True,
        attribute: bool = True,
        buffer: int | float | None = None,
        size: int = 1000,
        start_page: int = 1,
        max_pages: int = 100,
        max_items: int | None = None,
        crs: str | Crs = _DEFAULT_CRS,
        callback: str | None = None,
        domain: str | None = None,
    ) -> Iterator[JsonObject]:
        """VWorld 페이지네이션을 따라 2D Data ``GetFeature`` 페이지를 순회합니다."""

        yield from iter_vworld_pages(
            lambda page: self.get_data_feature(
                data,
                geom_filter=geom_filter,
                attr_filter=attr_filter,
                columns=columns,
                geometry=geometry,
                attribute=attribute,
                buffer=buffer,
                size=size,
                page=page,
                crs=crs,
                callback=callback,
                domain=domain,
            ),
            start_page=start_page,
            max_pages=max_pages,
            max_items=max_items,
        )

    def iter_data_feature_items(
        self,
        data: str,
        *,
        geom_filter: str | None = None,
        attr_filter: StringList | None = None,
        columns: StringList | None = None,
        geometry: bool = True,
        attribute: bool = True,
        buffer: int | float | None = None,
        size: int = 1000,
        start_page: int = 1,
        max_pages: int = 100,
        max_items: int | None = None,
        crs: str | Crs = _DEFAULT_CRS,
        callback: str | None = None,
        domain: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """2D Data ``GetFeature`` 결과 아이템을 여러 페이지에 걸쳐 순회합니다."""

        yielded = 0
        pages = self.iter_data_feature_pages(
            data,
            geom_filter=geom_filter,
            attr_filter=attr_filter,
            columns=columns,
            geometry=geometry,
            attribute=attribute,
            buffer=buffer,
            size=size,
            start_page=start_page,
            max_pages=max_pages,
            max_items=max_items,
            crs=crs,
            callback=callback,
            domain=domain,
        )
        for payload in pages:
            for item in response_items(payload):
                if max_items is not None and yielded >= max_items:
                    return
                yield item
                yielded += 1

    def get_data_feature_type(
        self,
        data: str,
        *,
        crs: str | Crs = _DEFAULT_CRS,
        callback: str | None = None,
        domain: str | None = None,
    ) -> JsonObject:
        """Call the documented ``GetFeatureType`` operation for a 2D data service."""

        if not data:
            raise VworldInvalidParameterError("data must not be empty")
        params = self._with_domain(
            {
                "service": "data",
                "request": "GetFeatureType",
                "version": _REST_VERSION,
                "format": _DEFAULT_FORMAT,
                "errorformat": _DEFAULT_ERROR_FORMAT,
                "data": data,
                "crs": crs,
                "callback": callback,
            },
            domain,
        )
        return self._require_http().get_json("/req/data", params)

    # WMS/WFS API 2.0 reference
    def wms_get_capabilities(
        self,
        *,
        version: str = "1.3.0",
        exceptions: str = "text/xml",
        domain: str | None = None,
    ) -> TextResponse:
        """Call WMS ``GetCapabilities``."""

        params = self._with_domain(
            {
                "SERVICE": "WMS",
                "REQUEST": "GetCapabilities",
                "VERSION": version,
                "EXCEPTIONS": exceptions,
            },
            domain,
        )
        text, content_type = self._require_http().get_text("/req/wms", params)
        return TextResponse(text=text, content_type=content_type)

    def wms_get_map_url(self, **kwargs: Any) -> str:
        """Build a WMS ``GetMap`` URL without fetching it."""

        return self._require_http().build_url("/req/wms", self._wms_get_map_params(**kwargs))

    def wms_get_map(self, **kwargs: Any) -> BinaryResponse:
        """Call WMS ``GetMap`` and return map image bytes."""

        content, content_type = self._require_http().get_bytes(
            "/req/wms",
            self._wms_get_map_params(**kwargs),
        )
        return BinaryResponse(content=content, content_type=content_type)

    def _wms_get_map_params(
        self,
        *,
        layers: str | list[str] | tuple[str, ...],
        bbox: BBoxLike,
        width: int,
        height: int,
        styles: str | list[str] | tuple[str, ...] | None = None,
        crs: str | Crs = _DEFAULT_OGC_CRS,
        format: str = "image/png",
        transparent: bool = False,
        bgcolor: str = "0xFFFFFF",
        exceptions: str = "text/xml",
        version: str = "1.3.0",
        domain: str | None = None,
    ) -> JsonObject:
        if width <= 0 or height <= 0:
            raise VworldInvalidParameterError("width and height must be positive")
        return self._with_domain(
            {
                "SERVICE": "WMS",
                "REQUEST": "GetMap",
                "VERSION": version,
                "LAYERS": csv(layers),
                "STYLES": csv(styles),
                "CRS": crs,
                "BBOX": bbox_param(bbox),
                "WIDTH": width,
                "HEIGHT": height,
                "FORMAT": format,
                "TRANSPARENT": transparent,
                "BGCOLOR": bgcolor,
                "EXCEPTIONS": exceptions,
            },
            domain,
        )

    def wms_get_feature_info(
        self,
        *,
        layers: str | list[str] | tuple[str, ...],
        query_layers: str | list[str] | tuple[str, ...],
        bbox: BBoxLike,
        width: int,
        height: int,
        i: int,
        j: int,
        styles: str | list[str] | tuple[str, ...] | None = None,
        crs: str | Crs = _DEFAULT_OGC_CRS,
        info_format: str = "text/xml",
        feature_count: int | None = None,
        version: str = "1.3.0",
        domain: str | None = None,
    ) -> TextResponse:
        """Call WMS ``GetFeatureInfo``."""

        if width <= 0 or height <= 0:
            raise VworldInvalidParameterError("width and height must be positive")
        if i < 0 or j < 0:
            raise VworldInvalidParameterError("i and j must be non-negative")
        params = self._with_domain(
            {
                "SERVICE": "WMS",
                "REQUEST": "GetFeatureInfo",
                "VERSION": version,
                "LAYERS": csv(layers),
                "QUERY_LAYERS": csv(query_layers),
                "STYLES": csv(styles),
                "CRS": crs,
                "BBOX": bbox_param(bbox),
                "WIDTH": width,
                "HEIGHT": height,
                "I": i,
                "J": j,
                "INFO_FORMAT": info_format,
                "FEATURE_COUNT": feature_count,
            },
            domain,
        )
        text, content_type = self._require_http().get_text("/req/wms", params)
        return TextResponse(text=text, content_type=content_type)

    def wfs_get_capabilities(
        self,
        *,
        version: str = "1.1.0",
        exceptions: str = "text/xml",
        domain: str | None = None,
    ) -> TextResponse:
        """Call WFS ``GetCapabilities``."""

        params = self._with_domain(
            {
                "SERVICE": "WFS",
                "REQUEST": "GetCapabilities",
                "VERSION": version,
                "EXCEPTIONS": exceptions,
            },
            domain,
        )
        text, content_type = self._require_http().get_text("/req/wfs", params)
        return TextResponse(text=text, content_type=content_type)

    def wfs_describe_feature_type(
        self,
        type_name: str | list[str] | tuple[str, ...],
        *,
        version: str = "1.1.0",
        output_format: str | None = None,
        domain: str | None = None,
    ) -> TextResponse:
        """Call WFS ``DescribeFeatureType``."""

        params = self._with_domain(
            {
                "SERVICE": "WFS",
                "REQUEST": "DescribeFeatureType",
                "VERSION": version,
                "TYPENAME": csv(type_name),
                "OUTPUTFORMAT": output_format,
            },
            domain,
        )
        text, content_type = self._require_http().get_text("/req/wfs", params)
        return TextResponse(text=text, content_type=content_type)

    def wfs_get_feature(
        self,
        type_name: str | list[str] | tuple[str, ...],
        *,
        bbox: BBoxLike | None = None,
        property_name: str | list[str] | tuple[str, ...] | None = None,
        max_features: int | None = None,
        srs_name: str | Crs = _DEFAULT_OGC_CRS,
        output: str = "GML2",
        exceptions: str = "text/xml",
        filter: str | None = None,
        version: str = "1.1.0",
        domain: str | None = None,
    ) -> TextResponse:
        """Call WFS ``GetFeature``."""

        if max_features is not None and max_features < 1:
            raise VworldInvalidParameterError("max_features must be at least 1")
        params = self._with_domain(
            {
                "SERVICE": "WFS",
                "REQUEST": "GetFeature",
                "VERSION": version,
                "TYPENAME": csv(type_name),
                "BBOX": bbox_param(bbox),
                "PROPERTYNAME": csv(property_name),
                "MAXFEATURES": max_features,
                "SRSNAME": srs_name,
                "OUTPUT": output,
                "EXCEPTIONS": exceptions,
                "FILTER": filter,
            },
            domain,
        )
        text, content_type = self._require_http().get_text("/req/wfs", params)
        return TextResponse(text=text, content_type=content_type)

    # Legend and StaticMap Image API 2.0
    def get_legend_graphic(
        self,
        layer: str,
        *,
        style: str | None = None,
        type: str | LegendType = LegendType.ALL,
        format: str | ImageFormat = ImageFormat.PNG,
    ) -> BinaryResponse:
        """Call Image API ``GetLegendGraphic``."""

        return self._image_legend("GetLegendGraphic", layer, style=style, type=type, format=format)

    def get_legend_style(
        self,
        layer: str,
        *,
        style: str | None = None,
        type: str | LegendType = LegendType.ALL,
        format: str | ImageFormat = ImageFormat.PNG,
    ) -> BinaryResponse:
        """Call Image API ``GetLegendStyle``."""

        return self._image_legend("GetLegendStyle", layer, style=style, type=type, format=format)

    def legend_graphic_url(self, layer: str, **kwargs: Any) -> str:
        """Build a ``GetLegendGraphic`` URL without fetching it."""

        return self._require_http().build_url(
            "/req/image",
            self._legend_params("GetLegendGraphic", layer, **kwargs),
        )

    def legend_style_url(self, layer: str, **kwargs: Any) -> str:
        """Build a ``GetLegendStyle`` URL without fetching it."""

        return self._require_http().build_url(
            "/req/image",
            self._legend_params("GetLegendStyle", layer, **kwargs),
        )

    def _image_legend(self, request: str, layer: str, **kwargs: Any) -> BinaryResponse:
        content, content_type = self._require_http().get_bytes(
            "/req/image",
            self._legend_params(request, layer, **kwargs),
        )
        return BinaryResponse(content=content, content_type=content_type)

    def _legend_params(
        self,
        request: str,
        layer: str,
        *,
        style: str | None = None,
        type: str | LegendType = LegendType.ALL,
        format: str | ImageFormat = ImageFormat.PNG,
    ) -> JsonObject:
        if not layer:
            raise VworldInvalidParameterError("layer must not be empty")
        type_value = _text_value(type).upper()
        if type_value not in {"ALL", "LAYER", "SUB"}:
            raise VworldInvalidParameterError("type must be ALL, LAYER, or SUB")
        return {
            "service": "image",
            "request": request,
            "version": _REST_VERSION,
            "format": format,
            "errorformat": _DEFAULT_ERROR_FORMAT,
            "layer": layer,
            "style": style,
            "type": type_value,
        }

    def static_map_url(self, **kwargs: Any) -> str:
        """Build a StaticMap ``GetMap`` URL without fetching it."""

        return self._require_http().build_url("/req/image", self._static_map_params(**kwargs))

    def static_map(self, **kwargs: Any) -> BinaryResponse:
        """Call StaticMap API 2.0 and return image bytes."""

        content, content_type = self._require_http().get_bytes(
            "/req/image",
            self._static_map_params(**kwargs),
        )
        return BinaryResponse(content=content, content_type=content_type)

    def _static_map_params(
        self,
        *,
        center: PointLike,
        zoom: int,
        size: str | tuple[int, int],
        basemap: str | StaticMapBase = StaticMapBase.GRAPHIC,
        crs: str | Crs = _DEFAULT_CRS,
        format: str | ImageFormat = ImageFormat.PNG,
        layers: str | list[str] | tuple[str, ...] | None = None,
        styles: str | list[str] | tuple[str, ...] | None = None,
        marker: str | list[str] | tuple[str, ...] | None = None,
        route: str | list[str] | tuple[str, ...] | None = None,
    ) -> JsonObject:
        validate_zoom(zoom)
        validate_static_size(size)
        return {
            "service": "image",
            "request": "getmap",
            "version": _REST_VERSION,
            "format": format,
            "errorformat": _DEFAULT_ERROR_FORMAT,
            "basemap": basemap,
            "center": point(center),
            "crs": crs,
            "zoom": zoom,
            "size": pixel_size(size),
            "layers": csv(layers),
            "styles": csv(styles),
            "marker": marker,
            "route": route,
        }

    def static_map_latlon(self, lat: float, lon: float, **kwargs: Any) -> BinaryResponse:
        """Call StaticMap with a WGS84 latitude/longitude center."""

        return self.static_map(center=LatLon(lat=lat, lon=lon), **kwargs)

    def static_map_latlon_url(self, lat: float, lon: float, **kwargs: Any) -> str:
        """Build a StaticMap URL with a WGS84 latitude/longitude center."""

        return self.static_map_url(center=LatLon(lat=lat, lon=lon), **kwargs)

    # WMTS/TMS tile endpoints
    def wmts_tile_url(
        self,
        layer: str | TileLayer,
        tile_matrix: int,
        tile_row: int,
        tile_col: int,
        *,
        tile_type: str | None = None,
    ) -> str:
        """Build a WMTS GetTile URL."""

        layer_text = self._normalize_tile_layer(layer)
        ext = tile_type or _TILE_EXTENSIONS[layer_text]
        self._validate_tile(layer_text, tile_matrix, tile_row, tile_col, ext)
        return self._tile_url(
            "wmts",
            (layer_text, str(tile_matrix), str(tile_row), f"{tile_col}.{ext}"),
        )

    def get_wmts_tile(self, *args: Any, **kwargs: Any) -> BinaryResponse:
        """Fetch a WMTS tile."""

        return self._fetch_absolute(self.wmts_tile_url(*args, **kwargs))

    def wmts_theme_tile_url(
        self,
        category: str,
        year: int | str,
        city: str,
        tile_matrix: int,
        tile_row: int,
        tile_col: int,
        *,
        tile_type: str = "png",
    ) -> str:
        """Build a WMTS overseas satellite theme tile URL."""

        self._validate_theme_tile(tile_matrix, tile_row, tile_col, tile_type)
        return self._tile_url(
            "wmts",
            (
                TileLayer.SATELLITE.value,
                "themes",
                category,
                str(year),
                city,
                str(tile_matrix),
                str(tile_row),
                f"{tile_col}.{tile_type}",
            ),
        )

    def get_wmts_theme_tile(self, *args: Any, **kwargs: Any) -> BinaryResponse:
        """Fetch a WMTS overseas satellite theme tile."""

        return self._fetch_absolute(self.wmts_theme_tile_url(*args, **kwargs))

    def wmts_capabilities_url(self) -> str:
        """Build the WMTS GetCapabilities URL."""

        return self._tile_url("wmts", ("WMTSCapabilities.xml",))

    def get_wmts_capabilities(self) -> TextResponse:
        """Fetch WMTS capabilities XML."""

        return self._fetch_absolute_text(self.wmts_capabilities_url())

    def tms_resource_url(self) -> str:
        """Build the TMS TileMap resource URL."""

        return self._tile_url("tms", ())

    def get_tms_resource(self) -> TextResponse:
        """Fetch the TMS TileMap resource XML."""

        return self._fetch_absolute_text(self.tms_resource_url())

    def tms_tile_url(
        self,
        tile_map: str | TileLayer,
        tile_matrix: int,
        tile_row: int,
        tile_col: int,
        *,
        tile_type: str | None = None,
    ) -> str:
        """Build a TMS tile URL."""

        layer_text = self._normalize_tile_layer(tile_map)
        ext = tile_type or _TILE_EXTENSIONS[layer_text]
        self._validate_tile(layer_text, tile_matrix, tile_row, tile_col, ext)
        return self._tile_url(
            "tms",
            (layer_text, str(tile_matrix), str(tile_row), f"{tile_col}.{ext}"),
        )

    def get_tms_tile(self, *args: Any, **kwargs: Any) -> BinaryResponse:
        """Fetch a TMS tile."""

        return self._fetch_absolute(self.tms_tile_url(*args, **kwargs))

    def tms_theme_tile_url(
        self,
        category: str,
        year: int | str,
        city: str,
        tile_matrix: int,
        tile_row: int,
        tile_col: int,
        *,
        tile_type: str = "png",
    ) -> str:
        """Build a TMS overseas satellite theme tile URL."""

        self._validate_theme_tile(tile_matrix, tile_row, tile_col, tile_type)
        return self._tile_url(
            "tms",
            (
                TileLayer.SATELLITE.value,
                "themes",
                category,
                str(year),
                city,
                str(tile_matrix),
                str(tile_row),
                f"{tile_col}.{tile_type}",
            ),
        )

    def get_tms_theme_tile(self, *args: Any, **kwargs: Any) -> BinaryResponse:
        """Fetch a TMS overseas satellite theme tile."""

        return self._fetch_absolute(self.tms_theme_tile_url(*args, **kwargs))

    def _tile_url(self, service: str, parts: tuple[str, ...]) -> str:
        http = self._require_http()
        encoded = "/".join(quote(part, safe=".") for part in parts)
        suffix = f"/{encoded}" if encoded else ""
        return f"{http.BASE_URL}/req/{service}/1.0.0/{quote(http.api_key, safe='')}{suffix}"

    def _fetch_absolute(self, url: str) -> BinaryResponse:
        http = self._require_http()
        path = url.removeprefix(http.BASE_URL)
        content, content_type = http.get_bytes(path, params={}, include_key=False)
        return BinaryResponse(content=content, content_type=content_type)

    def _fetch_absolute_text(self, url: str) -> TextResponse:
        http = self._require_http()
        path = url.removeprefix(http.BASE_URL)
        text, content_type = http.get_text(path, params={}, include_key=False)
        return TextResponse(text=text, content_type=content_type)

    def _normalize_tile_layer(self, layer: str | TileLayer) -> str:
        text = layer.value if isinstance(layer, TileLayer) else str(layer)
        for valid in _TILE_ZOOM_RANGES:
            if text.lower() == valid.lower():
                return valid
        raise VworldInvalidParameterError(
            "layer must be Base, white, midnight, Hybrid, or Satellite"
        )

    def _validate_tile(
        self,
        layer: str,
        tile_matrix: int,
        tile_row: int,
        tile_col: int,
        tile_type: str,
    ) -> None:
        min_zoom, max_zoom = _TILE_ZOOM_RANGES[layer]
        validate_zoom(tile_matrix, min_zoom=min_zoom, max_zoom=max_zoom)
        if tile_row < 0 or tile_col < 0:
            raise VworldInvalidParameterError("tile_row and tile_col must be non-negative")
        allowed = _TILE_EXTENSIONS[layer]
        if tile_type.lower() != allowed.lower():
            raise VworldInvalidParameterError(f"{layer} tile_type must be {allowed}")

    def _validate_theme_tile(
        self,
        tile_matrix: int,
        tile_row: int,
        tile_col: int,
        tile_type: str,
    ) -> None:
        validate_zoom(tile_matrix, min_zoom=6, max_zoom=19)
        if tile_row < 0 or tile_col < 0:
            raise VworldInvalidParameterError("tile_row and tile_col must be non-negative")
        if tile_type.lower() not in {"png", "jpeg", "jpg"}:
            raise VworldInvalidParameterError("theme tile_type must be png, jpeg, or jpg")

    # Debug/advanced escape hatch
    def build_rest_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        """Build an authenticated URL for an advanced VWorld REST request."""

        return self._require_http().build_url(path, clean_params(params or {}))
