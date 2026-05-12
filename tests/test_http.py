from __future__ import annotations

import pytest
import responses

from vworld._http import _VworldHttp
from vworld.exceptions import (
    VworldAuthError,
    VworldNetworkError,
    VworldNoDataError,
    VworldRateLimitError,
    VworldServerError,
)

BASE = "https://api.vworld.kr"


@responses.activate
def test_json_ok_adds_key_and_returns_payload(ok_payload):
    responses.add(responses.GET, BASE + "/req/search", json=ok_payload)

    data = _VworldHttp("test-key", retry_backoff=0).get_json("/req/search", {"service": "search"})

    assert data == ok_payload
    assert "key=test-key" in responses.calls[0].request.url
    assert "service=search" in responses.calls[0].request.url


@responses.activate
def test_json_parse_and_shape_errors():
    responses.add(
        responses.GET,
        BASE + "/bad-json",
        body="not-json",
        content_type="application/json",
    )
    responses.add(responses.GET, BASE + "/list-json", json=[])

    http = _VworldHttp("test-key", retry_backoff=0)
    with pytest.raises(VworldServerError):
        http.get_json("/bad-json")
    with pytest.raises(VworldServerError):
        http.get_json("/list-json")


@pytest.mark.parametrize(
    ("code", "exc_type"),
    [
        ("INVALID_KEY", VworldAuthError),
        ("INCORRECT_KEY", VworldAuthError),
        ("UNAVAILABLE_KEY", VworldAuthError),
        ("OVER_REQUEST_LIMIT", VworldRateLimitError),
        ("SYSTEM_ERROR", VworldServerError),
        ("PARAM_REQUIRED", VworldServerError),
    ],
)
@responses.activate
def test_vworld_error_code_mapping(code, exc_type):
    responses.add(
        responses.GET,
        BASE + "/req/search",
        json={"response": {"status": "ERROR", "error": {"code": code, "text": "boom"}}},
    )

    with pytest.raises(exc_type):
        _VworldHttp("test-key", retry_backoff=0).get_json("/req/search")


@responses.activate
def test_not_found_maps_to_no_data():
    responses.add(responses.GET, BASE + "/req/search", json={"response": {"status": "NOT_FOUND"}})

    with pytest.raises(VworldNoDataError):
        _VworldHttp("test-key", retry_backoff=0).get_json("/req/search")


@responses.activate
def test_binary_json_error_payload_is_mapped():
    responses.add(
        responses.GET,
        BASE + "/req/image",
        json={"response": {"status": "ERROR", "error": {"code": "INVALID_KEY", "text": "bad"}}},
        content_type="application/json",
    )

    with pytest.raises(VworldAuthError):
        _VworldHttp("test-key", retry_backoff=0).get_bytes("/req/image")


@responses.activate
def test_binary_invalid_json_content_type_is_ignored():
    responses.add(
        responses.GET,
        BASE + "/req/image",
        body=b"not-json",
        content_type="application/json",
    )

    content, _ = _VworldHttp("test-key", retry_backoff=0).get_bytes("/req/image")

    assert content == b"not-json"


@responses.activate
def test_xml_exception_payload_is_server_error():
    responses.add(
        responses.GET,
        BASE + "/req/wmts/1.0.0/test-key/Base/1/2/3.png",
        body="<ExceptionReport/>",
        content_type="text/xml",
    )

    with pytest.raises(VworldServerError):
        _VworldHttp("test-key", retry_backoff=0).get_bytes(
            "/req/wmts/1.0.0/test-key/Base/1/2/3.png",
            include_key=False,
        )


@responses.activate
def test_retries_5xx_then_succeeds(ok_payload):
    responses.add(responses.GET, BASE + "/req/search", status=503)
    responses.add(responses.GET, BASE + "/req/search", json=ok_payload)

    data = _VworldHttp("test-key", retry_backoff=0, max_retries=1).get_json("/req/search")

    assert data["response"]["status"] == "OK"
    assert len(responses.calls) == 2


def test_network_timeout_maps_to_network_error(monkeypatch):
    import requests

    class BadSession:
        def get(self, *args, **kwargs):
            raise requests.Timeout("too slow")

    with pytest.raises(VworldNetworkError):
        _VworldHttp("test-key", retry_backoff=0, max_retries=0, session=BadSession()).get_json(
            "/req/search"
        )


@pytest.mark.parametrize(
    ("status", "exc_type"),
    [
        (401, VworldAuthError),
        (429, VworldRateLimitError),
        (500, VworldServerError),
        (404, VworldServerError),
    ],
)
@responses.activate
def test_http_status_mapping(status, exc_type):
    responses.add(responses.GET, BASE + "/req/search", status=status, body="status error")

    with pytest.raises(exc_type):
        _VworldHttp("test-key", retry_backoff=0).get_json("/req/search")


@responses.activate
def test_non_error_or_non_dict_error_envelopes_return_or_raise():
    responses.add(responses.GET, BASE + "/unknown-status", json={"response": {"status": "PENDING"}})
    responses.add(
        responses.GET,
        BASE + "/string-error",
        json={"response": {"status": "ERROR", "error": "plain"}},
    )

    assert _VworldHttp("test-key", retry_backoff=0).get_json("/unknown-status")
    with pytest.raises(VworldServerError):
        _VworldHttp("test-key", retry_backoff=0).get_json("/string-error")


def test_build_url_can_omit_key():
    http = _VworldHttp("test-key", retry_backoff=0)

    assert http.build_url("/req/wmts/1.0.0/test-key/Base/11/1/2.png", include_key=False) == (
        "https://api.vworld.kr/req/wmts/1.0.0/test-key/Base/11/1/2.png"
    )


def test_http_repr_does_not_expose_api_key():
    assert "secret-key" not in repr(_VworldHttp("secret-key", retry_backoff=0))
