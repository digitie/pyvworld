from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from pyvworld import VworldClient

pytestmark = pytest.mark.live


def _local_env() -> dict[str, str]:
    path = Path(".env")
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@pytest.fixture(scope="module")
def live_client() -> VworldClient:
    local = _local_env()
    api_key = os.getenv("VWORLD_API_KEY") or os.getenv("VWORLD_KEY") or local.get("VWORLD_API_KEY")
    if not api_key:
        pytest.skip("VWORLD_API_KEY is required for live tests")
    domain = os.getenv("VWORLD_DOMAIN") or local.get("VWORLD_DOMAIN")
    return VworldClient(api_key, domain=domain, timeout=20, max_retries=1, retry_backoff=0)


def _status(payload: dict[str, Any]) -> str:
    response = payload.get("response")
    assert isinstance(response, dict)
    status = response.get("status")
    assert isinstance(status, str)
    return status


def test_live_search_geocoder_and_data(live_client: VworldClient):
    search = live_client.search_address("성남시 분당구 판교로 242", size=1)
    assert _status(search) == "OK"

    geocoded = live_client.geocode("판교로 242", type="road")
    assert _status(geocoded) == "OK"
    point = geocoded["response"]["result"]["point"]
    x, y = float(point["x"]), float(point["y"])

    reverse = live_client.reverse_geocode((x, y), type="both")
    assert _status(reverse) == "OK"

    feature = live_client.get_data_feature(
        "LT_C_ADEMD_INFO",
        attr_filter="emd_cd:=:11650108",
        geometry=False,
        size=1,
        domain="",
    )
    assert _status(feature) == "OK"


def test_live_ogc_capabilities(live_client: VworldClient):
    if not live_client.domain:
        pytest.skip("VWORLD_DOMAIN is required for reliable live WMS/WFS capabilities tests")

    wms = live_client.wms_get_capabilities()
    assert "WMS_Capabilities" in wms.text

    wfs = live_client.wfs_get_capabilities()
    assert "WFS_Capabilities" in wfs.text


def test_live_images_and_tiles(live_client: VworldClient):
    legend = live_client.get_legend_graphic("lt_c_uq111", style="lt_c_uq111")
    assert legend.content_type is not None
    assert "image" in legend.content_type.lower()
    assert len(legend.content) > 100

    static = live_client.static_map(center=(126.978271, 37.566643), zoom=16, size=(128, 128))
    assert static.content_type is not None
    assert "image" in static.content_type.lower()
    assert len(static.content) > 100

    wmts_capabilities = live_client.get_wmts_capabilities()
    assert "Capabilities" in wmts_capabilities.text

    tile = live_client.get_wmts_tile("Base", 11, 793, 1746)
    assert tile.content_type is not None
    assert "image" in tile.content_type.lower()
    assert len(tile.content) > 100

    tms_resource = live_client.get_tms_resource()
    assert "TileMapService" in tms_resource.text
