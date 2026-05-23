from __future__ import annotations

import pytest

from vworld._http import _VworldHttp
from vworld.exceptions import (
    VworldAuthError,
    VworldNetworkError,
    VworldNoDataError,
    VworldRateLimitError,
    VworldServerError,
)

BASE = "https://api.vworld.kr"


def test_json_ok_adds_key_and_returns_payload(ok_payload, http_mock):
    http_mock.add("GET", BASE + "/req/search", json=ok_payload)

    data = _VworldHttp("test-key", retry_backoff=0).get_json("/req/search", {"service": "search"})

    assert data == ok_payload
    assert "key=test-key" in str(http_mock.calls[0].request.url)
    assert "service=search" in str(http_mock.calls[0].request.url)


def test_json_parse_and_shape_errors(http_mock):
    http_mock.add(
        "GET",
        BASE + "/bad-json",
        body="not-json",
        content_type="application/json",
    )
    http_mock.add("GET", BASE + "/list-json", json=[])

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
def test_vworld_error_code_mapping(code, exc_type, http_mock):
    http_mock.add(
        "GET",
        BASE + "/req/search",
        json={"response": {"status": "ERROR", "error": {"code": code, "text": "boom"}}},
    )

    with pytest.raises(exc_type):
        _VworldHttp("test-key", retry_backoff=0).get_json("/req/search")


def test_not_found_maps_to_no_data(http_mock):
    http_mock.add("GET", BASE + "/req/search", json={"response": {"status": "NOT_FOUND"}})

    with pytest.raises(VworldNoDataError):
        _VworldHttp("test-key", retry_backoff=0).get_json("/req/search")


def test_binary_json_error_payload_is_mapped(http_mock):
    http_mock.add(
        "GET",
        BASE + "/req/image",
        json={"response": {"status": "ERROR", "error": {"code": "INVALID_KEY", "text": "bad"}}},
        content_type="application/json",
    )

    with pytest.raises(VworldAuthError):
        _VworldHttp("test-key", retry_backoff=0).get_bytes("/req/image")


def test_binary_invalid_json_content_type_is_ignored(http_mock):
    http_mock.add(
        "GET",
        BASE + "/req/image",
        body=b"not-json",
        content_type="application/json",
    )

    content, _ = _VworldHttp("test-key", retry_backoff=0).get_bytes("/req/image")

    assert content == b"not-json"


def test_xml_exception_payload_is_server_error(http_mock):
    http_mock.add(
        "GET",
        BASE + "/req/wmts/1.0.0/test-key/Base/1/2/3.png",
        body="<ExceptionReport/>",
        content_type="text/xml",
    )

    with pytest.raises(VworldServerError):
        _VworldHttp("test-key", retry_backoff=0).get_bytes(
            "/req/wmts/1.0.0/test-key/Base/1/2/3.png",
            include_key=False,
        )


def test_retries_5xx_then_succeeds(ok_payload, http_mock):
    http_mock.add("GET", BASE + "/req/search", status=503)
    http_mock.add("GET", BASE + "/req/search", json=ok_payload)

    data = _VworldHttp("test-key", retry_backoff=0, max_retries=1).get_json("/req/search")

    assert data["response"]["status"] == "OK"
    assert len(http_mock.calls) == 2


def test_network_timeout_maps_to_network_error(monkeypatch):
    import httpx

    class BadSession:
        def get(self, *args, **kwargs):
            raise httpx.TimeoutException("too slow")

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
def test_http_status_mapping(status, exc_type, http_mock):
    http_mock.add("GET", BASE + "/req/search", status=status, body="status error")

    with pytest.raises(exc_type):
        _VworldHttp("test-key", retry_backoff=0, max_retries=0).get_json("/req/search")


def test_non_error_or_non_dict_error_envelopes_return_or_raise(http_mock):
    http_mock.add("GET", BASE + "/unknown-status", json={"response": {"status": "PENDING"}})
    http_mock.add(
        "GET",
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


def test_http_close_calls_session_close():
    closed = []

    class FakeSession:
        def close(self):
            closed.append(True)

    http = _VworldHttp("test-key", retry_backoff=0, session=FakeSession())
    http.close()

    assert closed == [True]
