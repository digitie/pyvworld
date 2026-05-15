from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from tests.runners import RUNNERS
from tests.utils import assert_case
from vworld.parser import VworldParsedResponse
from vworld.processor import ProcessedVworldResponse

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def all_fixture_files() -> list[Path]:
    return sorted(FIXTURE_DIR.glob("*/*.json"))


@pytest.mark.parametrize(
    "fixture_path",
    all_fixture_files(),
    ids=lambda path: f"{path.parent.name}/{path.stem}",
)
def test_generated_fixtures(fixture_path: Path) -> None:
    with fixture_path.open("r", encoding="utf-8") as file:
        case = json.load(file)

    function_name = case["function"]
    runner = RUNNERS[function_name]
    parse = cast(Any, runner["parse"])
    process = cast(Any, runner["process"])
    parsed = cast(VworldParsedResponse, parse(case["response"]["body"]))
    processed = cast(ProcessedVworldResponse, process(parsed))
    actual = processed.model_dump(mode="json")
    expected = case["processed"]
    assertion = case.get("assertion", {"mode": "snapshot"})
    assert_case(actual, expected, assertion)
