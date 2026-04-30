from __future__ import annotations

import pytest

from pyvworld import TileLayer
from pyvworld._params import (
    bbox,
    clean_params,
    csv,
    pixel_size,
    point,
    validate_page,
    validate_page_size,
    validate_static_size,
)
from pyvworld.exceptions import VworldInvalidParameterError


def test_clean_params_converts_bool_enum_and_lists():
    params = clean_params({"a": True, "b": False, "c": None, "d": [1, False, TileLayer.BASE]})

    assert params == {"a": "true", "b": "false", "d": [1, "false", "Base"]}


def test_csv_preserves_strings_and_joins_iterables():
    assert csv("LT_C_UQ111") == "LT_C_UQ111"
    assert csv(["a", "b", "c"]) == "a,b,c"
    assert csv(None) is None


def test_point_bbox_and_size_format_numbers_without_trailing_zeroes():
    assert point((126.0, 37.5)) == "126,37.5"
    assert bbox((1.0, 2.25, 3.0, 4.5)) == "1,2.25,3,4.5"
    assert pixel_size((400, 300)) == "400,300"
    assert pixel_size("400,300") == "400,300"


@pytest.mark.parametrize(
    "value",
    [
        (1.0,),
        (float("nan"), 1.0),
        "127 37",
    ],
)
def test_point_rejects_malformed_values(value):
    with pytest.raises(VworldInvalidParameterError):
        point(value)


@pytest.mark.parametrize("value", [(0, 1), (1, 0), (1025, 512), "400"])
def test_static_size_validation(value):
    with pytest.raises(VworldInvalidParameterError):
        validate_static_size(value)


@pytest.mark.parametrize(
    "func,args",
    [
        (bbox, ((1.0, 2.0, 3.0),)),
        (pixel_size, ((1,),)),
        (pixel_size, ((0, 1),)),
        (validate_page_size, (0,)),
        (validate_page, (0,)),
        (validate_static_size, ("a,b",)),
    ],
)
def test_more_invalid_params(func, args):
    with pytest.raises(VworldInvalidParameterError):
        func(*args)
