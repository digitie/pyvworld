from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "debug-ui"))

from vworld_debug_ui.fixture_writer import save_fixture, slugify  # noqa: E402


def test_slugify_preserves_korean_case_names() -> None:
    assert slugify("판교 정상 검색") == "판교_정상_검색"


def test_save_fixture_redacts_sensitive_values_and_blocks_overwrite(tmp_path: Path) -> None:
    path = save_fixture(
        base_dir=tmp_path,
        function_name="search",
        case_name="normal",
        description="fixture writer test",
        input_data={"query": "판교", "api_key": "secret"},
        request_data={
            "url": "https://api.vworld.kr/req/search?query=x&key=secret",
            "query": {"query": "x", "key": "secret"},
            "headers": {"Authorization": "Bearer secret"},
        },
        response_data={"status_code": 200, "body": {"response": {"status": "OK"}}},
        parsed_result={"response": {"status": "OK"}},
        processed_result={"status": "OK", "items": []},
        library_version="0.1.0",
    )

    text = path.read_text(encoding="utf-8")
    assert "secret" not in text
    fixture = json.loads(text)
    assert fixture["input"]["api_key"] == "<REDACTED>"
    assert fixture["request"]["query"]["key"] == "<REDACTED>"
    assert fixture["meta"]["source"] == "debug_ui"
    with pytest.raises(FileExistsError):
        save_fixture(
            base_dir=tmp_path,
            function_name="search",
            case_name="normal",
            description="fixture writer test",
            input_data={},
            request_data={},
            response_data={},
            parsed_result={},
            processed_result={},
        )
