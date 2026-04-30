from __future__ import annotations

import pytest

from pyvworld import DATA_SERVICE_BY_ID, DATA_SERVICES, get_data_service
from pyvworld.exceptions import VworldInvalidParameterError


def test_catalog_contains_current_official_2d_data_count():
    assert len(DATA_SERVICES) == 158
    assert len(DATA_SERVICE_BY_ID) == 158
    assert {service.version for service in DATA_SERVICES} == {"2.0"}


def test_catalog_lookup_is_case_insensitive():
    service = get_data_service("lt_c_ademd_info")

    assert service.service_id == "LT_C_ADEMD_INFO"
    assert service.slug == "ademd"
    assert service.updated_at == "2026-04-23"


def test_catalog_preserves_leading_letters_and_known_ids():
    ids = {service.service_id for service in DATA_SERVICES}

    assert "LP_PA_CBND_BUBUN" in ids
    assert "LT_C_UQ111" in ids
    assert "LT_L_N3A0020000" in ids


def test_unknown_catalog_id_raises():
    with pytest.raises(VworldInvalidParameterError):
        get_data_service("LT_C_DOES_NOT_EXIST")
