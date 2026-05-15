"""디버그 UI 입력 preset을 JSON 파일로 저장하고 읽습니다."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .fixture_writer import jsonable, slugify


def save_preset(
    base_dir: str | Path,
    function_name: str,
    preset_name: str,
    values: dict[str, Any],
) -> Path:
    """함수별 preset 입력값을 저장합니다."""

    path = Path(base_dir) / slugify(function_name) / f"{slugify(preset_name)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(jsonable(values), file, ensure_ascii=False, indent=2)
        file.write("\n")
    return path


def load_presets(base_dir: str | Path, function_name: str) -> dict[str, dict[str, Any]]:
    """함수별 preset 목록을 읽어 이름과 입력값 매핑으로 반환합니다."""

    root = Path(base_dir) / slugify(function_name)
    if not root.exists():
        return {}
    presets: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as file:
                value = json.load(file)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            presets[path.stem] = value
    return presets
