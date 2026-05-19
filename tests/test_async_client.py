from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

import pytest

from vworld import AsyncVworldClient, VworldClient
from vworld.exceptions import VworldAuthError, VworldInvalidParameterError

BASE = "https://api.vworld.kr"


def _query(call) -> dict[str, list[str]]:
    return parse_qs(urlparse(str(call.request.url)).query, keep_blank_values=True)


def test_async_search_uses_httpx_and_returns_payload(ok_payload, http_mock):
    http_mock.add("GET", BASE + "/req/search", json=ok_payload)

    async def run() -> dict:
        async with AsyncVworldClient("test-key", retry_backoff=0) as client:
            return await client.search_place("판교", size=1)

    payload = asyncio.run(run())

    assert payload == ok_payload
    query = _query(http_mock.calls[0])
    assert query["key"] == ["test-key"]
    assert query["query"] == ["판교"]
    assert query["size"] == ["1"]


def test_sync_client_aio_factory_returns_async_client(ok_payload, http_mock):
    http_mock.add("GET", BASE + "/req/address", json=ok_payload)

    async def run() -> dict:
        async with VworldClient.aio(api_key="test-key", retry_backoff=0) as client:
            return await client.geocode("판교로 242")

    payload = asyncio.run(run())

    assert payload == ok_payload
    query = _query(http_mock.calls[0])
    assert query["request"] == ["getcoord"]
    assert query["address"] == ["판교로 242"]


def test_async_data_feature_preserves_explicit_blank_domain(ok_payload, http_mock):
    http_mock.add("GET", BASE + "/req/data", json=ok_payload)

    async def run() -> dict:
        client = AsyncVworldClient("test-key", domain="example.com", retry_backoff=0)
        try:
            return await client.get_data_feature("LT_C_ADEMD_INFO", domain="")
        finally:
            await client.aclose()

    asyncio.run(run())

    assert _query(http_mock.calls[0])["domain"] == [""]


def test_async_image_and_tile_fetches(http_mock):
    http_mock.add(
        "GET",
        BASE + "/req/image",
        body=b"map",
        content_type="image/png",
    )
    http_mock.add(
        "GET",
        BASE + "/req/wmts/1.0.0/test-key/Base/11/793/1746.png",
        body=b"tile",
        content_type="image/png",
    )

    async def run():
        async with AsyncVworldClient("test-key", retry_backoff=0) as client:
            static_map = await client.static_map(
                center=(126.978271, 37.566643),
                zoom=16,
                size=(128, 128),
            )
            tile = await client.get_wmts_tile("Base", 11, 793, 1746)
            return static_map, tile

    static_map, tile = asyncio.run(run())

    assert static_map.content == b"map"
    assert tile.content == b"tile"
    assert _query(http_mock.calls[0])["request"] == ["getmap"]


def test_async_validation_and_missing_key(monkeypatch):
    async def bad_search() -> None:
        client = AsyncVworldClient("test-key", retry_backoff=0)
        try:
            await client.search("판교", "address", category=None)
        finally:
            await client.aclose()

    with pytest.raises(VworldInvalidParameterError):
        asyncio.run(bad_search())

    monkeypatch.delenv("VWORLD_API_KEY", raising=False)
    monkeypatch.delenv("VWORLD_KEY", raising=False)
    with pytest.raises(VworldAuthError):
        asyncio.run(AsyncVworldClient(api_key=None).search_place("판교"))
