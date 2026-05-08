"""VWorld 응답 메타데이터와 민감정보 제거 헬퍼."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Any, Literal, TypeAlias
from urllib.parse import parse_qsl, urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]

PROVIDER: Literal["vworld"] = "vworld"

_CREDENTIAL_PARAM_NAMES = {
    "apikey",
    "api_key",
    "authkey",
    "auth_key",
    "key",
    "servicekey",
    "service_key",
}
_CREDENTIAL_TEXT_RE = re.compile(
    r"(?i)\b(api_key|auth_key|authKey|key|service_key|serviceKey)=([^&#\s]+)"
)
_TILE_KEY_RE = re.compile(r"(?i)(/req/(?:wmts|tms)/1\.0\.0/)([^/?#]+)")


class VworldResponseMetadata(BaseModel):
    """VWorld 응답 출처를 민감정보 없이 담는 메타데이터.

    ``request_params``에는 ``key`` 같은 원본 인증값을 보관하지 않습니다.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: Literal["vworld"] = PROVIDER
    service_name: str
    endpoint: str
    request_params: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("request_params", mode="before")
    @classmethod
    def _sanitize_params(cls, value: object) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise TypeError("request_params must be a mapping")
        return sanitize_request_params(value)


def is_credential_param(name: str) -> bool:
    """인증 정보를 담는 것으로 알려진 파라미터 이름인지 반환합니다."""

    return name.replace("-", "_").lower() in _CREDENTIAL_PARAM_NAMES


def sanitize_request_params(params: Mapping[str, Any]) -> dict[str, Any]:
    """요청 파라미터에서 인증값을 담는 키를 제거해 반환합니다."""

    sanitized: dict[str, Any] = {}
    for key, value in params.items():
        text_key = str(key)
        if is_credential_param(text_key):
            continue
        sanitized[text_key] = _sanitize_value(value)
    return sanitized


def redact_credentials_in_text(text: str) -> str:
    """텍스트에서 인증 쿼리 값과 VWorld 타일 경로 키를 마스킹합니다."""

    query_redacted = _CREDENTIAL_TEXT_RE.sub(lambda match: f"{match.group(1)}=***", text)
    return _TILE_KEY_RE.sub(lambda match: f"{match.group(1)}***", query_redacted)


def request_params_from_url(url: str) -> dict[str, Any]:
    """URL에서 민감정보가 제거된 쿼리 매핑을 추출합니다."""

    query = urlsplit(url).query
    if not query:
        return {}
    return sanitize_request_params(dict(parse_qsl(query, keep_blank_values=True)))


def make_response_metadata(
    *,
    service_name: str,
    endpoint: str,
    request_params: Mapping[str, Any] | None = None,
    collected_at: datetime | None = None,
) -> VworldResponseMetadata:
    """VWorld 응답의 출처 메타데이터를 민감정보 없이 만듭니다."""

    return VworldResponseMetadata(
        service_name=service_name,
        endpoint=endpoint,
        request_params=sanitize_request_params(request_params or {}),
        collected_at=collected_at or datetime.now(timezone.utc),
    )


def make_cache_key(
    endpoint: str,
    params: Mapping[str, Any] | None = None,
    *,
    namespace: str = "pyvworld:v1",
) -> str:
    """엔드포인트와 정리된 요청값으로 안정적인 캐시 키를 만듭니다."""

    payload = {
        "endpoint": str(endpoint),
        "params": _canonical_jsonable(sanitize_request_params(params or {})),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"{namespace}:{digest}"


def to_json_safe_raw(value: Any) -> JsonValue:
    """원본 payload 값을 JSON 안전 dict/list 구조로 변환합니다."""

    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, datetime | date | time):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): to_json_safe_raw(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        return [to_json_safe_raw(item) for item in value]
    return str(value)


raw_to_json_safe = to_json_safe_raw


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return sanitize_request_params(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_value(item) for item in value)
    return value


def _canonical_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical_jsonable(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, list | tuple):
        return [_canonical_jsonable(item) for item in value]
    if isinstance(value, datetime | date | time):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value
