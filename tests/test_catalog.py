from __future__ import annotations

import pytest

from vworld import (
    DATA_SERVICE_BY_ID,
    DATA_SERVICES,
    VWORLD_AUTH_KEY_URL,
    data_service_label,
    get_api_catalog_entry,
    get_data_service,
    list_api_catalog,
)
from vworld.exceptions import VworldInvalidParameterError


def test_catalog_contains_current_official_2d_data_count():
    assert len(DATA_SERVICES) == 158
    assert len(DATA_SERVICE_BY_ID) == 158
    assert {service.version for service in DATA_SERVICES} == {"2.0"}


def test_catalog_lookup_is_case_insensitive():
    service = get_data_service("lt_c_ademd_info")

    assert service.service_id == "LT_C_ADEMD_INFO"
    assert service.slug == "ademd"
    assert service.updated_at == "2026-04-23"
    assert data_service_label(service) == "읍면동 (LT_C_ADEMD_INFO)"


def test_catalog_preserves_leading_letters_and_known_ids():
    ids = {service.service_id for service in DATA_SERVICES}

    assert "LP_PA_CBND_BUBUN" in ids
    assert "LT_C_UQ111" in ids
    assert "LT_L_N3A0020000" in ids


def test_unknown_catalog_id_raises():
    with pytest.raises(VworldInvalidParameterError):
        get_data_service("LT_C_DOES_NOT_EXIST")


def test_api_catalog_exposes_debug_functions_and_auth_key_url():
    catalog = list_api_catalog()
    functions = {entry.function for entry in catalog}
    data_entry = get_api_catalog_entry("get_data_feature")

    assert {"search", "geocode", "reverse_geocode", "get_data_feature"} <= functions
    assert data_entry.endpoint == "/req/data"
    assert data_entry.auth_key_url == VWORLD_AUTH_KEY_URL
    assert any(param.kind == "data_service" for param in data_entry.parameters)
