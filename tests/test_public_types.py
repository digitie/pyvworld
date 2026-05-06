from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import responses

from pyvworld import (
    AddressCategory,
    AddressType,
    BBox,
    BinaryResponse,
    Crs,
    DistrictCategory,
    ImageFormat,
    LegendType,
    ReverseGeocodeType,
    SearchType,
    StaticMapBase,
    TextResponse,
    VworldClient,
    latlon,
)

BASE = "https://api.vworld.kr"


def _query(call) -> dict[str, list[str]]:
    return parse_qs(urlparse(call.request.url).query)


def test_response_models_are_public_imports():
    assert BinaryResponse(b"ok").content == b"ok"
    assert TextResponse("<ok/>").text == "<ok/>"
    assert BinaryResponse(content=b"ok").model_dump() == {
        "content": b"ok",
        "content_type": None,
    }
    assert TextResponse(text="<ok/>").model_dump_json() == '{"text":"<ok/>","content_type":null}'


@responses.activate
def test_search_accepts_enums_and_bbox_model():
    responses.add(responses.GET, BASE + "/req/search", json={"response": {"status": "OK"}})
    client = VworldClient("test-key", retry_backoff=0)

    client.search(
        "pangyo",
        SearchType.ADDRESS,
        category=AddressCategory.PARCEL,
        bbox=BBox.from_latlon(south=37.4, west=126.9, north=37.6, east=127.1),
        crs=Crs.WGS84,
    )

    query = _query(responses.calls[0])
    assert query["type"] == ["address"]
    assert query["category"] == ["parcel"]
    assert query["bbox"] == ["126.9,37.4,127.1,37.6"]
    assert query["crs"] == ["EPSG:4326"]


@responses.activate
def test_geocoder_accepts_enums_and_latlon_helpers():
    responses.add(responses.GET, BASE + "/req/address", json={"response": {"status": "OK"}})
    responses.add(responses.GET, BASE + "/req/address", json={"response": {"status": "OK"}})
    responses.add(responses.GET, BASE + "/req/address", json={"response": {"status": "OK"}})
    client = VworldClient("test-key", retry_backoff=0)

    client.geocode("pangyo-ro 242", type=AddressType.ROAD)
    client.reverse_geocode(latlon(37.402352535, 127.101313354), type=ReverseGeocodeType.ROAD)
    client.reverse_geocode_latlon(37.402352535, 127.101313354)

    assert _query(responses.calls[0])["type"] == ["road"]
    assert _query(responses.calls[1])["point"] == ["127.101313354,37.402352535"]
    assert _query(responses.calls[1])["type"] == ["road"]
    assert _query(responses.calls[2])["point"] == ["127.101313354,37.402352535"]


@responses.activate
def test_search_district_accepts_enum_category():
    responses.add(responses.GET, BASE + "/req/search", json={"response": {"status": "OK"}})
    client = VworldClient("test-key", retry_backoff=0)

    client.search_district("pangyo", category=DistrictCategory.LEVEL3)

    assert _query(responses.calls[0])["category"] == ["L3"]


@responses.activate
def test_legend_and_static_map_accept_enums_and_latlon():
    responses.add(responses.GET, BASE + "/req/image", body=b"legend", content_type="image/png")
    client = VworldClient("test-key", retry_backoff=0)

    client.get_legend_style("lt_c_uq111", type=LegendType.SUB, format=ImageFormat.BMP)
    url = client.static_map_url(
        center=latlon(37.566643, 126.978271),
        zoom=16,
        size=(128, 128),
        basemap=StaticMapBase.PHOTO_HYBRID,
        format=ImageFormat.PNG,
    )
    helper_url = client.static_map_latlon_url(37.566643, 126.978271, zoom=16, size=(128, 128))

    query = _query(responses.calls[0])
    assert query["request"] == ["GetLegendStyle"]
    assert query["type"] == ["SUB"]
    assert query["format"] == ["bmp"]
    assert "basemap=PHOTO_HYBRID" in url
    assert "center=126.978271%2C37.566643" in url
    assert helper_url == (
        "https://api.vworld.kr/req/image?service=image&request=getmap&version=2.0"
        "&format=png&errorformat=json&basemap=GRAPHIC&center=126.978271%2C37.566643"
        "&crs=EPSG%3A4326&zoom=16&size=128%2C128&key=test-key"
    )
