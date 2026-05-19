"""HTTP helper and response-to-exception mapping."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from time import sleep
from typing import Any
from urllib.parse import urlencode, urljoin

import httpx

from ._params import Params, clean_params
from .exceptions import (
    VworldAuthError,
    VworldNetworkError,
    VworldNoDataError,
    VworldRateLimitError,
    VworldServerError,
)


def _new_client() -> httpx.Client:
    return httpx.Client(follow_redirects=True)


def _new_async_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=True)


@dataclass(slots=True)
class _VworldHttp:
    api_key: str = field(repr=False)
    timeout: float = 10.0
    max_retries: int = 2
    retry_backoff: float = 0.5
    session: Any = field(default_factory=lambda: _new_client())

    BASE_URL = "https://api.vworld.kr"

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = _new_client()

    def close(self) -> None:
        close = getattr(self.session, "close", None)
        if callable(close):
            close()

    def build_url(
        self,
        path: str,
        params: Params | None = None,
        *,
        include_key: bool = True,
    ) -> str:
        return _build_url(self.api_key, self.BASE_URL, path, params, include_key=include_key)

    def get_json(self, path: str, params: Params | None = None) -> dict[str, Any]:
        response = self._get(path, params)
        _raise_for_http_status(response)
        data = _json_object(response)
        _raise_for_vworld_status(data)
        return data

    def get_bytes(
        self,
        path: str,
        params: Params | None = None,
        *,
        include_key: bool = True,
    ) -> tuple[bytes, str | None]:
        response = self._get(path, params, include_key=include_key)
        _raise_for_http_status(response)
        _raise_if_error_payload(response)
        return bytes(response.content), _content_type(response)

    def get_text(
        self,
        path: str,
        params: Params | None = None,
        *,
        include_key: bool = True,
    ) -> tuple[str, str | None]:
        response = self._get(path, params, include_key=include_key)
        _raise_for_http_status(response)
        _raise_if_error_payload(response)
        return str(response.text), _content_type(response)

    def _get(self, path: str, params: Params | None, *, include_key: bool = True) -> Any:
        query = _query_params(self.api_key, params, include_key=include_key)
        attempts = max(0, self.max_retries) + 1
        last_error: VworldNetworkError | None = None
        for attempt in range(attempts):
            try:
                response = self.session.get(
                    urljoin(self.BASE_URL, path),
                    params=query,
                    timeout=self.timeout,
                )
            except httpx.TransportError as exc:
                last_error = VworldNetworkError(str(exc))
                if attempt < attempts - 1:
                    self._sleep_before_retry(attempt)
                    continue
                raise last_error from exc

            if 500 <= response.status_code < 600 and attempt < attempts - 1:
                self._sleep_before_retry(attempt)
                continue
            return response

        if last_error is not None:
            raise last_error
        raise VworldServerError("request failed after retries")

    def _sleep_before_retry(self, attempt: int) -> None:
        if self.retry_backoff > 0:
            sleep(self.retry_backoff * (2**attempt))


@dataclass(slots=True)
class _AsyncVworldHttp:
    api_key: str = field(repr=False)
    timeout: float = 10.0
    max_retries: int = 2
    retry_backoff: float = 0.5
    session: Any = field(default_factory=lambda: _new_async_client())

    BASE_URL = "https://api.vworld.kr"

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = _new_async_client()

    async def aclose(self) -> None:
        close = getattr(self.session, "aclose", None)
        if callable(close):
            await close()
            return
        sync_close = getattr(self.session, "close", None)
        if callable(sync_close):
            sync_close()

    def build_url(
        self,
        path: str,
        params: Params | None = None,
        *,
        include_key: bool = True,
    ) -> str:
        return _build_url(self.api_key, self.BASE_URL, path, params, include_key=include_key)

    async def get_json(self, path: str, params: Params | None = None) -> dict[str, Any]:
        response = await self._get(path, params)
        _raise_for_http_status(response)
        data = _json_object(response)
        _raise_for_vworld_status(data)
        return data

    async def get_bytes(
        self,
        path: str,
        params: Params | None = None,
        *,
        include_key: bool = True,
    ) -> tuple[bytes, str | None]:
        response = await self._get(path, params, include_key=include_key)
        _raise_for_http_status(response)
        _raise_if_error_payload(response)
        return bytes(response.content), _content_type(response)

    async def get_text(
        self,
        path: str,
        params: Params | None = None,
        *,
        include_key: bool = True,
    ) -> tuple[str, str | None]:
        response = await self._get(path, params, include_key=include_key)
        _raise_for_http_status(response)
        _raise_if_error_payload(response)
        return str(response.text), _content_type(response)

    async def _get(self, path: str, params: Params | None, *, include_key: bool = True) -> Any:
        query = _query_params(self.api_key, params, include_key=include_key)
        attempts = max(0, self.max_retries) + 1
        last_error: VworldNetworkError | None = None
        for attempt in range(attempts):
            try:
                response = await self.session.get(
                    urljoin(self.BASE_URL, path),
                    params=query,
                    timeout=self.timeout,
                )
            except httpx.TransportError as exc:
                last_error = VworldNetworkError(str(exc))
                if attempt < attempts - 1:
                    await self._sleep_before_retry(attempt)
                    continue
                raise last_error from exc

            if 500 <= response.status_code < 600 and attempt < attempts - 1:
                await self._sleep_before_retry(attempt)
                continue
            return response

        if last_error is not None:
            raise last_error
        raise VworldServerError("request failed after retries")

    async def _sleep_before_retry(self, attempt: int) -> None:
        if self.retry_backoff > 0:
            await asyncio.sleep(self.retry_backoff * (2**attempt))


def _query_params(
    api_key: str,
    params: Params | None,
    *,
    include_key: bool,
) -> dict[str, Any]:
    query = clean_params(params or {})
    if include_key:
        query.setdefault("key", api_key)
    return query


def _build_url(
    api_key: str,
    base_url: str,
    path: str,
    params: Params | None,
    *,
    include_key: bool,
) -> str:
    query = _query_params(api_key, params, include_key=include_key)
    url = urljoin(base_url, path)
    if not query:
        return url
    return f"{url}?{urlencode(query, doseq=True)}"


def _json_object(response: Any) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as exc:
        raise VworldServerError(f"JSON parse failure: {exc}") from exc
    if not isinstance(data, dict):
        raise VworldServerError("JSON response must be an object")
    return data


def _raise_for_http_status(response: Any) -> None:
    if response.status_code in (401, 403):
        raise VworldAuthError(f"HTTP {response.status_code}: {response.text[:200]}")
    if response.status_code == 429:
        raise VworldRateLimitError(response.text[:200])
    if 500 <= response.status_code < 600:
        raise VworldServerError(f"HTTP {response.status_code}: {response.text[:200]}")
    if response.status_code >= 400:
        raise VworldServerError(f"HTTP {response.status_code}: {response.text[:200]}")


def _raise_if_error_payload(response: Any) -> None:
    content_type = (_content_type(response) or "").lower()
    text = str(response.text[:1000]).lstrip()
    if "json" in content_type or text.startswith("{"):
        try:
            data = response.json()
        except ValueError:
            return
        if isinstance(data, dict):
            _raise_for_vworld_status(data)
    elif "ExceptionReport" in text or "TileMapServerError" in text:
        raise VworldServerError(text[:300])


def _raise_for_vworld_status(data: dict[str, Any]) -> None:
    root = data.get("response")
    if not isinstance(root, dict):
        return
    status = str(root.get("status", "")).upper()
    if status == "OK":
        return
    if status == "NOT_FOUND":
        raise VworldNoDataError("VWorld returned NOT_FOUND")
    if status != "ERROR":
        return

    error = root.get("error")
    if isinstance(error, dict):
        code = str(error.get("code", "UNKNOWN_ERROR"))
        text = str(error.get("text", ""))
    else:
        code = "UNKNOWN_ERROR"
        text = str(error or "")
    message = f"{code}: {text}".strip()
    if code in {"INVALID_KEY", "INCORRECT_KEY", "UNAVAILABLE_KEY"}:
        raise VworldAuthError(message)
    if code == "OVER_REQUEST_LIMIT":
        raise VworldRateLimitError(message)
    if code in {"SYSTEM_ERROR", "UNKNOWN_ERROR"}:
        raise VworldServerError(message)
    raise VworldServerError(message)


def _content_type(response: Any) -> str | None:
    value = response.headers.get("Content-Type")
    return str(value) if value is not None else None
