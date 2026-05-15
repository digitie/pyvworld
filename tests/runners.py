from __future__ import annotations

from collections.abc import Callable
from typing import Any

from vworld.parser import (
    VworldParsedResponse,
    parse_data_feature_response,
    parse_geocode_response,
    parse_reverse_geocode_response,
    parse_search_response,
)
from vworld.processor import (
    ProcessedVworldResponse,
    process_data_feature_response,
    process_geocode_response,
    process_reverse_geocode_response,
    process_search_response,
)

Runner = dict[
    str,
    Callable[[Any], VworldParsedResponse]
    | Callable[[VworldParsedResponse], ProcessedVworldResponse],
]

RUNNERS: dict[str, Runner] = {
    "search": {
        "parse": parse_search_response,
        "process": process_search_response,
    },
    "geocode": {
        "parse": parse_geocode_response,
        "process": process_geocode_response,
    },
    "reverse_geocode": {
        "parse": parse_reverse_geocode_response,
        "process": process_reverse_geocode_response,
    },
    "get_data_feature": {
        "parse": parse_data_feature_response,
        "process": process_data_feature_response,
    },
}
