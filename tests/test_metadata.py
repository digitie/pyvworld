from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from vworld import (
    VworldResponseMetadata,
    make_cache_key,
    make_response_metadata,
    raw_to_json_safe,
    redact_credentials_in_text,
    request_params_from_url,
    sanitize_request_params,
)


def test_sanitize_request_params_removes_credentials_recursively() -> None:
    params = {
        "service": "search",
        "key": "secret",
        "nested": {"api_key": "secret", "page": 1},
        "items": [{"serviceKey": "secret", "size": 10}],
    }

    assert sanitize_request_params(params) == {
        "service": "search",
        "nested": {"page": 1},
        "items": [{"size": 10}],
    }


def test_metadata_factory_sanitizes_and_freezes() -> None:
    metadata = make_response_metadata(
        service_name="search",
        endpoint="/req/search",
        request_params={"query": "판교", "key": "secret"},
        collected_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
    )

    assert isinstance(metadata, VworldResponseMetadata)
    assert metadata.provider == "vworld"
    assert metadata.request_params == {"query": "판교"}
    with pytest.raises(ValidationError):
        metadata.endpoint = "/other"


def test_url_helpers_redact_query_keys_and_tile_path_keys() -> None:
    url = "https://api.vworld.kr/req/search?service=search&key=secret&page=1"
    tile_url = "https://api.vworld.kr/req/wmts/1.0.0/secret-key/Base/11/1/2.png"

    assert request_params_from_url(url) == {"service": "search", "page": "1"}
    assert redact_credentials_in_text(url) == (
        "https://api.vworld.kr/req/search?service=search&key=***&page=1"
    )
    assert redact_credentials_in_text(tile_url) == (
        "https://api.vworld.kr/req/wmts/1.0.0/***/Base/11/1/2.png"
    )


def test_cache_key_is_stable_and_ignores_credentials() -> None:
    first = make_cache_key("/req/search", {"query": "판교", "key": "one", "page": 1})
    second = make_cache_key("/req/search", {"page": 1, "key": "two", "query": "판교"})

    assert first == second
    assert first.startswith("vworld:v1:")


def test_raw_to_json_safe_converts_dates_enums_and_tuples() -> None:
    payload = raw_to_json_safe({"today": date(2026, 5, 7), "coords": (127, 37)})

    assert payload == {"today": "2026-05-07", "coords": [127, 37]}
