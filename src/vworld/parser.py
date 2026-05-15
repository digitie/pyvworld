"""VWorld JSON 응답을 Pydantic v2 객체로 감싸는 파서."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VworldParsedResponse(BaseModel):
    """VWorld REST JSON 응답의 최상위 ``response`` 객체를 보존합니다."""

    model_config = ConfigDict(extra="allow")

    response: dict[str, Any] = Field(default_factory=dict)


def parse_vworld_json_response(raw: Mapping[str, Any]) -> VworldParsedResponse:
    """원본 JSON 매핑을 공통 Pydantic 응답 모델로 변환합니다."""

    return VworldParsedResponse.model_validate(dict(raw))


def parse_search_response(raw: Mapping[str, Any]) -> VworldParsedResponse:
    """Search API 응답을 파싱합니다."""

    return parse_vworld_json_response(raw)


def parse_geocode_response(raw: Mapping[str, Any]) -> VworldParsedResponse:
    """Geocoder ``getcoord`` 응답을 파싱합니다."""

    return parse_vworld_json_response(raw)


def parse_reverse_geocode_response(raw: Mapping[str, Any]) -> VworldParsedResponse:
    """Geocoder ``getaddress`` 응답을 파싱합니다."""

    return parse_vworld_json_response(raw)


def parse_data_feature_response(raw: Mapping[str, Any]) -> VworldParsedResponse:
    """2D Data ``GetFeature`` 응답을 파싱합니다."""

    return parse_vworld_json_response(raw)
