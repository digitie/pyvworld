from __future__ import annotations

from typing import Any

import pytest

from vworld import VworldClient


@pytest.fixture
def client() -> VworldClient:
    return VworldClient("test-key", retry_backoff=0)


@pytest.fixture
def ok_payload() -> dict[str, Any]:
    return {"response": {"status": "OK", "result": {"items": []}}}
