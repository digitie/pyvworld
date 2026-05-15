from __future__ import annotations

from typing import Any


def remove_fields(obj: Any, exclude_fields: list[str]) -> Any:
    if isinstance(obj, dict):
        return {
            key: remove_fields(value, exclude_fields)
            for key, value in obj.items()
            if key not in exclude_fields
        }
    if isinstance(obj, list):
        return [remove_fields(value, exclude_fields) for value in obj]
    return obj


def assert_case(actual: Any, expected: Any, assertion: dict[str, Any]) -> None:
    mode = assertion.get("mode", "snapshot")
    if mode == "snapshot":
        exclude_fields = list(assertion.get("exclude_fields", []))
        assert remove_fields(actual, exclude_fields) == remove_fields(expected, exclude_fields)
    elif mode == "required_fields":
        for field in assertion.get("required_fields", []):
            assert _has_field(actual, str(field))
    elif mode == "schema_only":
        assert actual is not None
    else:
        raise ValueError(f"Unknown assertion mode: {mode}")


def _has_field(actual: Any, field: str) -> bool:
    current = actual
    for part in field.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True
