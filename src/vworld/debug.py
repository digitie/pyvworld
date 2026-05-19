"""VWorld REST 호출을 fixture 생성용으로 관찰하는 디버그 실행기."""

from __future__ import annotations

import traceback
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from time import perf_counter
from typing import Any
from urllib.parse import urlsplit

from .catalog import (
    ApiCatalogEntry,
    DataService,
    get_api_catalog_entry,
    get_data_service,
)
from .client import VworldClient
from .exceptions import VworldError
from .metadata import (
    raw_to_json_safe,
    redact_credentials_in_text,
    request_params_from_url,
    sanitize_request_params,
)
from .parser import (
    VworldParsedResponse,
    parse_data_feature_response,
    parse_geocode_response,
    parse_reverse_geocode_response,
    parse_search_response,
)
from .processor import (
    ProcessedVworldResponse,
    process_data_feature_response,
    process_geocode_response,
    process_reverse_geocode_response,
    process_search_response,
)

JsonObject = dict[str, Any]
JsonParser = Callable[[Mapping[str, Any]], VworldParsedResponse]
JsonProcessor = Callable[[VworldParsedResponse], ProcessedVworldResponse]
ClientCall = Callable[[VworldClient, Mapping[str, Any]], JsonObject]


@dataclass(frozen=True, slots=True)
class DebugRun:
    """디버그 UI와 fixture writer가 공유하는 실행 결과입니다."""

    function: str
    input: JsonObject
    request: JsonObject
    response: JsonObject
    parsed: VworldParsedResponse | None
    processed: ProcessedVworldResponse | None
    trace: list[str]
    catalog: ApiCatalogEntry | None = None
    data_service: DataService | None = None
    error: JsonObject | None = None


@dataclass(frozen=True, slots=True)
class _RecordedCall:
    request: JsonObject
    response: JsonObject


class _RecordingSession:
    """기존 httpx client/session을 감싸 요청과 응답을 저장합니다."""

    def __init__(self, session: Any) -> None:
        self._session = session
        self.calls: list[_RecordedCall] = []

    def get(self, *args: Any, **kwargs: Any) -> Any:
        started = perf_counter()
        response = self._session.get(*args, **kwargs)
        elapsed_ms = round((perf_counter() - started) * 1000, 3)
        self.calls.append(_record_call(response, elapsed_ms))
        return response


DEBUG_FUNCTION_LABELS: dict[str, str] = {
    "search": "Search API 2.0",
    "geocode": "Geocoder getcoord 2.0",
    "reverse_geocode": "Geocoder getaddress 2.0",
    "get_data_feature": "2D Data GetFeature 2.0",
}


def run_debug_function(
    client: VworldClient,
    function_name: str,
    input_data: Mapping[str, Any],
) -> DebugRun:
    """이름으로 등록된 디버그 함수를 실행합니다."""

    try:
        runner = _DEBUG_RUNNERS[function_name]
    except KeyError as exc:
        available = ", ".join(sorted(_DEBUG_RUNNERS))
        message = f"Unknown debug function: {function_name}. Available: {available}"
        raise ValueError(message) from exc
    return runner(client, input_data)


def debug_search(client: VworldClient, input_data: Mapping[str, Any]) -> DebugRun:
    """Search API 호출을 실행하고 요청/응답/처리 결과를 반환합니다."""

    return _invoke_json(
        "search",
        client,
        input_data,
        _call_search,
        parse_search_response,
        process_search_response,
    )


def debug_geocode(client: VworldClient, input_data: Mapping[str, Any]) -> DebugRun:
    """Geocoder ``getcoord`` 호출을 실행하고 디버그 결과를 반환합니다."""

    return _invoke_json(
        "geocode",
        client,
        input_data,
        _call_geocode,
        parse_geocode_response,
        process_geocode_response,
    )


def debug_reverse_geocode(client: VworldClient, input_data: Mapping[str, Any]) -> DebugRun:
    """Geocoder ``getaddress`` 호출을 실행하고 디버그 결과를 반환합니다."""

    return _invoke_json(
        "reverse_geocode",
        client,
        input_data,
        _call_reverse_geocode,
        parse_reverse_geocode_response,
        process_reverse_geocode_response,
    )


def debug_get_data_feature(client: VworldClient, input_data: Mapping[str, Any]) -> DebugRun:
    """2D Data ``GetFeature`` 호출을 실행하고 디버그 결과를 반환합니다."""

    return _invoke_json(
        "get_data_feature",
        client,
        input_data,
        _call_get_data_feature,
        parse_data_feature_response,
        process_data_feature_response,
    )


def _invoke_json(
    function_name: str,
    client: VworldClient,
    input_data: Mapping[str, Any],
    call: ClientCall,
    parser: JsonParser,
    processor: JsonProcessor,
) -> DebugRun:
    trace = [f"{function_name} debug run started"]
    catalog_entry = _catalog_entry(function_name)
    data_service = _data_service(function_name, input_data)
    if catalog_entry is not None:
        trace.append(
            f"Catalog: {catalog_entry.label} {catalog_entry.endpoint} "
            f"({catalog_entry.service}/{catalog_entry.request})"
        )
    if data_service is not None:
        trace.append(f"Dataset: {data_service.name} ({data_service.service_id})")
    normalized_input = raw_to_json_safe(dict(input_data))
    try:
        recorder = _install_recorder(client)
    except Exception as exc:
        trace.append(f"Exception captured: {type(exc).__name__}")
        input_value = (
            normalized_input if isinstance(normalized_input, dict) else {"value": normalized_input}
        )
        return DebugRun(
            function=function_name,
            input=input_value,
            request={},
            response={},
            parsed=None,
            processed=None,
            trace=trace,
            catalog=catalog_entry,
            data_service=data_service,
            error=_error_info(exc),
        )
    parsed: VworldParsedResponse | None = None
    processed: ProcessedVworldResponse | None = None
    error: JsonObject | None = None
    raw_response: JsonObject | None = None
    try:
        raw_response = call(client, input_data)
        trace.append("HTTP request completed")
    except Exception as exc:  # 디버그 도구는 예외도 결과로 보여줘야 합니다.
        trace.append(f"Exception captured: {type(exc).__name__}")
        error = _error_info(exc)
        raw_response = _last_response_body(recorder)
    finally:
        _restore_recorder(client, recorder)

    if raw_response is not None:
        try:
            parsed = parser(raw_response)
            processed = processor(parsed)
            trace.append("Response parsed and processed")
        except Exception as exc:  # 파싱 실패도 Validation Errors 탭에서 확인합니다.
            trace.append(f"Parse/process exception captured: {type(exc).__name__}")
            if error is None:
                error = _error_info(exc)

    record = recorder.calls[-1] if recorder.calls else None
    request_data = record.request if record else {}
    response_data = record.response if record else {}
    if raw_response is not None and "body" not in response_data:
        response_data = {**response_data, "body": raw_to_json_safe(raw_response)}

    return DebugRun(
        function=function_name,
        input=(
            normalized_input if isinstance(normalized_input, dict) else {"value": normalized_input}
        ),
        request=request_data,
        response=response_data,
        parsed=parsed,
        processed=processed,
        trace=trace,
        catalog=catalog_entry,
        data_service=data_service,
        error=error,
    )


def _install_recorder(client: VworldClient) -> _RecordingSession:
    http = client._require_http()
    recorder = _RecordingSession(http.session)
    http.session = recorder
    return recorder


def _restore_recorder(client: VworldClient, recorder: _RecordingSession) -> None:
    http = client._require_http()
    http.session = recorder._session


def _record_call(response: Any, elapsed_ms: float) -> _RecordedCall:
    url = _response_url(response)
    body = _response_body(response)
    return _RecordedCall(
        request={
            "method": "GET",
            "url": redact_credentials_in_text(url),
            "endpoint": urlsplit(url).path,
            "query": request_params_from_url(url),
            "headers": _headers(response.request.headers if response.request is not None else {}),
        },
        response={
            "status_code": int(getattr(response, "status_code", 0)),
            "headers": _headers(getattr(response, "headers", {})),
            "body": raw_to_json_safe(body),
            "elapsed_ms": elapsed_ms,
        },
    )


def _response_url(response: Any) -> str:
    request = getattr(response, "request", None)
    request_url = getattr(request, "url", None)
    if request_url is not None:
        return str(request_url)
    response_url = getattr(response, "url", "")
    return str(response_url)


def _response_body(response: Any) -> Any:
    try:
        return response.json()
    except ValueError:
        text = getattr(response, "text", "")
        return str(text)


def _last_response_body(recorder: _RecordingSession) -> JsonObject | None:
    if not recorder.calls:
        return None
    body = recorder.calls[-1].response.get("body")
    return body if isinstance(body, dict) else None


def _headers(headers: Any) -> dict[str, str]:
    if not isinstance(headers, Mapping):
        return {}
    result: dict[str, str] = {}
    for key, value in sanitize_request_params(headers).items():
        text_key = str(key)
        if text_key.lower() in {"authorization", "x-api-key"}:
            result[text_key] = "***"
        else:
            result[text_key] = str(value)
    return result


def _error_info(exc: Exception) -> JsonObject:
    return {
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exception(type(exc), exc, exc.__traceback__),
    }


def _catalog_entry(function_name: str) -> ApiCatalogEntry | None:
    try:
        return get_api_catalog_entry(function_name)
    except VworldError:
        return None


def _data_service(function_name: str, input_data: Mapping[str, Any]) -> DataService | None:
    if function_name != "get_data_feature":
        return None
    service_id = _optional_text(input_data.get("data"))
    if service_id is None:
        return None
    try:
        return get_data_service(service_id)
    except VworldError:
        return None


def _call_search(client: VworldClient, input_data: Mapping[str, Any]) -> JsonObject:
    query = _required_text(input_data, "query")
    search_type = _text(input_data.get("type")) or "place"
    return client.search(
        query,
        search_type,
        category=_optional_text(input_data.get("category")),
        size=_int_value(input_data.get("size"), 10),
        page=_int_value(input_data.get("page"), 1),
        bbox=_optional_text(input_data.get("bbox")),
        crs=_text(input_data.get("crs")) or "EPSG:4326",
        callback=_optional_text(input_data.get("callback")),
    )


def _call_geocode(client: VworldClient, input_data: Mapping[str, Any]) -> JsonObject:
    return client.geocode(
        _required_text(input_data, "address"),
        type=_text(input_data.get("type")) or "road",
        refine=_bool_value(input_data.get("refine"), True),
        simple=_bool_value(input_data.get("simple"), False),
        crs=_text(input_data.get("crs")) or "EPSG:4326",
        callback=_optional_text(input_data.get("callback")),
    )


def _call_reverse_geocode(client: VworldClient, input_data: Mapping[str, Any]) -> JsonObject:
    return client.reverse_geocode(
        _required_text(input_data, "point"),
        type=_text(input_data.get("type")) or "both",
        zipcode=_bool_value(input_data.get("zipcode"), True),
        simple=_bool_value(input_data.get("simple"), False),
        crs=_text(input_data.get("crs")) or "EPSG:4326",
        callback=_optional_text(input_data.get("callback")),
    )


def _call_get_data_feature(client: VworldClient, input_data: Mapping[str, Any]) -> JsonObject:
    return client.get_data_feature(
        _required_text(input_data, "data"),
        geom_filter=_optional_text(input_data.get("geom_filter")),
        attr_filter=_optional_text(input_data.get("attr_filter")),
        columns=_optional_text(input_data.get("columns")),
        geometry=_bool_value(input_data.get("geometry"), True),
        attribute=_bool_value(input_data.get("attribute"), True),
        buffer=_number_or_none(input_data.get("buffer")),
        size=_int_value(input_data.get("size"), 10),
        page=_int_value(input_data.get("page"), 1),
        crs=_text(input_data.get("crs")) or "EPSG:4326",
        callback=_optional_text(input_data.get("callback")),
        domain=_optional_text(input_data.get("domain")),
    )


def _required_text(input_data: Mapping[str, Any], name: str) -> str:
    value = _optional_text(input_data.get(name))
    if value is None:
        return ""
    return value


def _optional_text(value: Any) -> str | None:
    text = _text(value)
    return text if text != "" else None


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _int_value(value: Any, default: int) -> int:
    text = _text(value)
    if text == "":
        return default
    return int(text)


def _number_or_none(value: Any) -> int | float | None:
    text = _text(value)
    if text == "":
        return None
    number = float(text)
    return int(number) if number.is_integer() else number


def _bool_value(value: Any, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


_DEBUG_RUNNERS: dict[str, Callable[[VworldClient, Mapping[str, Any]], DebugRun]] = {
    "search": debug_search,
    "geocode": debug_geocode,
    "reverse_geocode": debug_reverse_geocode,
    "get_data_feature": debug_get_data_feature,
}
