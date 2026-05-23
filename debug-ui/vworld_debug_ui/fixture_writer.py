"""디버그 실행 결과를 pytest replay fixture로 저장합니다."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel

SENSITIVE_KEYS = {
    "authorization",
    "x-api-key",
    "api_key",
    "apikey",
    "access_token",
    "authkey",
    "auth_key",
    "key",
    "refresh_token",
    "servicekey",
    "service_key",
}


def jsonable(obj: Any) -> Any:
    """Pydantic v2 객체와 일반 객체를 JSON 저장 가능한 값으로 변환합니다."""

    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if is_dataclass(obj) and not isinstance(obj, type):
        return jsonable(asdict(obj))
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Mapping):
        return {str(key): jsonable(value) for key, value in obj.items()}
    if isinstance(obj, list | tuple | set | frozenset):
        return [jsonable(value) for value in obj]
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    return obj


def redact_sensitive(obj: Any) -> Any:
    """fixture에 저장되면 안 되는 인증 관련 값을 마스킹합니다."""

    if isinstance(obj, Mapping):
        result: dict[str, Any] = {}
        for key, value in obj.items():
            text_key = str(key)
            if _sensitive_key(text_key):
                result[text_key] = "<REDACTED>"
            else:
                result[text_key] = redact_sensitive(value)
        return result
    if isinstance(obj, list):
        return [redact_sensitive(value) for value in obj]
    if isinstance(obj, str):
        return _redact_url_text(obj)
    return obj


def slugify(value: str) -> str:
    """case name을 파일명으로 쓸 수 있는 slug로 바꿉니다."""

    text = value.strip().lower()
    text = re.sub(r"[^0-9a-zA-Z가-힣._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._-")
    return text or "case"


def save_fixture(
    *,
    base_dir: str | Path,
    function_name: str,
    case_name: str,
    description: str,
    input_data: Mapping[str, Any],
    request_data: Mapping[str, Any],
    response_data: Mapping[str, Any],
    parsed_result: Any,
    processed_result: Any,
    assertion: Mapping[str, Any] | None = None,
    library_version: str | None = None,
    overwrite: bool = False,
) -> Path:
    """디버그 실행 결과를 표준 fixture JSON 파일로 저장합니다."""

    safe_case_name = slugify(case_name)
    safe_function_name = slugify(function_name)
    fixture_dir = Path(base_dir) / safe_function_name
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = fixture_dir / f"{safe_case_name}.json"
    if fixture_path.exists() and not overwrite:
        raise FileExistsError(f"Fixture already exists: {fixture_path}")

    fixture = {
        "name": safe_case_name,
        "function": function_name,
        "description": description,
        "input": redact_sensitive(jsonable(input_data)),
        "request": redact_sensitive(jsonable(request_data)),
        "response": redact_sensitive(jsonable(response_data)),
        "parsed": redact_sensitive(jsonable(parsed_result)),
        "processed": redact_sensitive(jsonable(processed_result)),
        "assertion": dict(assertion or _default_assertion()),
        "meta": {
            "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
            "library_version": library_version,
            "source": "debug_ui",
        },
    }
    with fixture_path.open("w", encoding="utf-8") as file:
        json.dump(fixture, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return fixture_path


def _default_assertion() -> dict[str, Any]:
    return {
        "mode": "snapshot",
        "exclude_fields": ["fetched_at", "request_id", "updated_at"],
        "required_fields": [],
    }


def _sensitive_key(key: str) -> bool:
    return key.replace("-", "_").lower() in SENSITIVE_KEYS


def _redact_url_text(value: str) -> str:
    query_pattern = (
        r"(?i)([?&](?:api_key|apikey|authkey|auth_key|key|servicekey|service_key"
        r"|access_token|refresh_token)=)"
        r"[^&#\s]+"
    )
    value = re.sub(query_pattern, r"\1<REDACTED>", value)
    tile_pattern = r"(?i)(/req/(?:wmts|tms)/1\.0\.0/)([^/?#]+)"
    return re.sub(tile_pattern, r"\1<REDACTED>", value)
