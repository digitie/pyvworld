from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyvworld import (
    BBox,
    Crs,
    ImageFormat,
    LatLon,
    LonLat,
    StaticMapBase,
    bbox_from_latlon,
    latlon,
    lonlat,
)
from pyvworld._params import bbox, point
from pyvworld.exceptions import VworldInvalidParameterError


def test_latlon_and_lonlat_standardize_to_vworld_xy_order():
    assert LatLon(lat=37.566643, lon=126.978271).as_xy() == (126.978271, 37.566643)
    assert LonLat(lon=126.978271, lat=37.566643).as_xy() == (126.978271, 37.566643)
    assert latlon(37.566643, 126.978271).as_lonlat() == lonlat(126.978271, 37.566643)


def test_point_accepts_coordinate_models():
    assert point(latlon(37.5, 127.0)) == "127,37.5"
    assert point(lonlat(127.0, 37.5)) == "127,37.5"


def test_bbox_model_and_factory():
    box = bbox_from_latlon(south=37.4, west=126.9, north=37.6, east=127.1)

    assert box == BBox(minx=126.9, miny=37.4, maxx=127.1, maxy=37.6)
    assert bbox(box) == "126.9,37.4,127.1,37.6"


def test_coordinate_models_are_pydantic_models():
    point_model = LatLon.model_validate({"lat": "37.5", "lon": "127.0"})
    box = BBox.model_validate({"minx": "126.9", "miny": 37.4, "maxx": 127.1, "maxy": 37.6})

    assert point_model.model_dump() == {"lat": 37.5, "lon": 127.0}
    assert point_model.model_dump_json() == '{"lat":37.5,"lon":127.0}'
    assert box.as_tuple() == (126.9, 37.4, 127.1, 37.6)
    assert "properties" in LatLon.model_json_schema()


def test_coordinate_models_are_frozen():
    point_model = LatLon(lat=37.5, lon=127.0)

    with pytest.raises(ValidationError):
        point_model.lat = 38.0


@pytest.mark.parametrize(
    "factory",
    [
        lambda: latlon(91, 127),
        lambda: lonlat(181, 37),
        lambda: latlon("not-a-number", 127),
        lambda: BBox(minx=2, miny=0, maxx=1, maxy=3),
        lambda: BBox(minx=1, miny=4, maxx=2, maxy=3),
    ],
)
def test_coordinate_models_validate_ranges(factory):
    with pytest.raises(VworldInvalidParameterError):
        factory()


def test_crs_enum_values_are_plain_api_values():
    assert Crs.WGS84.value == "EPSG:4326"
    assert Crs.GOOGLE_MERCATOR.value == "EPSG:900913"


def test_image_and_static_map_enums_include_official_values():
    assert ImageFormat.BMP.value == "bmp"
    assert StaticMapBase.NONE.value == "NONE"
    assert StaticMapBase.GRAPHIC_WHITE.value == "GRAPHIC_WHITE"
    assert StaticMapBase.GRAPHIC_NIGHT.value == "GRAPHIC_NIGHT"
    assert StaticMapBase.PHOTO_HYBRID.value == "PHOTO_HYBRID"
    assert StaticMapBase.HYBRID.value == "PHOTO_HYBRID"
