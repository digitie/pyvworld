"""파싱된 VWorld 응답을 회귀 테스트에 쓰기 쉬운 형태로 정규화합니다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .exceptions import VworldError
from .pagination import response_items
from .parser import VworldParsedResponse


class ProcessedVworldResponse(BaseModel):
    """VWorld 응답의 공통 관찰값입니다."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: str | None = None
    page: dict[str, Any] | None = None
    record: dict[str, Any] | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    result: Any = None
    error: dict[str, Any] | None = None


def process_vworld_response(parsed: VworldParsedResponse) -> ProcessedVworldResponse:
    """파싱 결과에서 상태, 페이지 정보, 아이템 목록을 추출합니다."""

    payload = parsed.model_dump(mode="json")
    root = payload.get("response")
    if not isinstance(root, Mapping):
        return ProcessedVworldResponse()

    status_value = root.get("status")
    result = root.get("result")
    error = root.get("error")
    return ProcessedVworldResponse(
        status=str(status_value) if status_value is not None else None,
        page=_dict_or_none(root.get("page")),
        record=_dict_or_none(root.get("record")),
        items=_safe_items(payload),
        result=result,
        error=_dict_or_none(error),
    )


def process_search_response(parsed: VworldParsedResponse) -> ProcessedVworldResponse:
    """Search API 파싱 결과를 처리합니다."""

    return process_vworld_response(parsed)


def process_geocode_response(parsed: VworldParsedResponse) -> ProcessedVworldResponse:
    """Geocoder ``getcoord`` 파싱 결과를 처리합니다."""

    return process_vworld_response(parsed)


def process_reverse_geocode_response(parsed: VworldParsedResponse) -> ProcessedVworldResponse:
    """Geocoder ``getaddress`` 파싱 결과를 처리합니다."""

    return process_vworld_response(parsed)


def process_data_feature_response(parsed: VworldParsedResponse) -> ProcessedVworldResponse:
    """2D Data ``GetFeature`` 파싱 결과를 처리합니다."""

    return process_vworld_response(parsed)


def _safe_items(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    try:
        return response_items(payload)
    except VworldError:
        return []


def _dict_or_none(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    return {str(key): item for key, item in value.items()}
