"""Streamlit 디버그 실행 이력을 JSON으로 저장합니다."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from vworld.debug import DebugRun

from .fixture_writer import jsonable, slugify


def append_history(base_dir: str | Path, debug_run: DebugRun) -> Path:
    """최근 실행 요약을 날짜별 history 파일로 저장합니다."""

    now = datetime.now(ZoneInfo("Asia/Seoul"))
    history_dir = Path(base_dir) / now.strftime("%Y-%m-%d")
    history_dir.mkdir(parents=True, exist_ok=True)
    path = history_dir / f"{now.strftime('%H%M%S')}_{slugify(debug_run.function)}.json"
    payload = {
        "created_at": now.isoformat(),
        "function": debug_run.function,
        "input": debug_run.input,
        "status_code": debug_run.response.get("status_code"),
        "error": debug_run.error,
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(jsonable(payload), file, ensure_ascii=False, indent=2)
        file.write("\n")
    return path


def load_recent_history(base_dir: str | Path, *, limit: int = 10) -> list[dict[str, Any]]:
    """최근 history 요약을 최신순으로 읽습니다."""

    root = Path(base_dir)
    if not root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/*.json"), reverse=True):
        try:
            with path.open("r", encoding="utf-8") as file:
                value = json.load(file)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            rows.append(value)
        if len(rows) >= limit:
            break
    return rows
