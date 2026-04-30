from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
import responses

from pyvworld import VworldClient
from pyvworld.exceptions import VworldAuthError, VworldInvalidParameterError

BASE = "https://api.vworld.kr"


def _query(call) -> dict[str, list[str]]:
    return parse_qs(urlparse(call.request.url).query)


@responses.activate
def test_search_place_query_params(client, ok_payload):
    responses.add(responses.GET, BASE + "/req/search", json=ok_payload)

    client.search_place(
        "공간정보산업진흥원",
        size=20,
        page=2,
        bbox=(14140071.146077, 4494339.6527027, 14160071.146077, 4496339.6527027),
        crs="EPSG:900913",
    )

    query = _query(responses.calls[0])
    assert query["service"] == ["search"]
    assert query["request"] == ["search"]
    assert query["version"] == ["2.0"]
    assert query["type"] == ["place"]
    assert query["query"] == ["공간정보산업진흥원"]
    assert query["size"] == ["20"]
    assert query["page"] == ["2"]
    assert "14140071.146077" in query["bbox"][0]
    assert "1.0" not in responses.calls[0].request.url


def test_search_requires_category_for_address_and_district(client):
    with pytest.raises(VworldInvalidParameterError):
        client.search("판교로 242", "address", category=None)

    with pytest.raises(VworldInvalidParameterError):
        client.search("삼평동", "district", category=None)


def test_search_more_helpers_and_validation(client, monkeypatch):
    monkeypatch.setenv("VWORLD_API_KEY", "env-key")
    assert VworldClient.from_env().api_key == "env-key"

    with pytest.raises(VworldInvalidParameterError):
        client.search("", "place")
    with pytest.raises(VworldInvalidParameterError):
        client.search("판교", "unknown")
    with pytest.raises(VworldInvalidParameterError):
        client.geocode("", type="road")
    with pytest.raises(VworldInvalidParameterError):
        client.geocode("판교로 242", type="both")
    with pytest.raises(VworldInvalidParameterError):
        client.reverse_geocode((127, 37), type="unknown")
    with pytest.raises(VworldInvalidParameterError):
        client.get_data_feature("")
    with pytest.raises(VworldInvalidParameterError):
        client.get_data_feature_type("")


def test_from_env_file_loads_key_and_domain(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'VWORLD_API_KEY="file-key"\nVWORLD_DOMAIN=example.com\n# ignored\n',
        encoding="utf-8",
    )

    client = VworldClient.from_env_file(env_file)

    assert client.api_key == "file-key"
    assert client.domain == "example.com"


@responses.activate
def test_search_address_helper_adds_default_category(client, ok_payload):
    responses.add(responses.GET, BASE + "/req/search", json=ok_payload)

    client.search_address("성남시 분당구 판교로 242")

    query = _query(responses.calls[0])
    assert query["type"] == ["address"]
    assert query["category"] == ["road"]


@responses.activate
def test_geocode_query_params(client, ok_payload):
    responses.add(responses.GET, BASE + "/req/address", json=ok_payload)

    client.geocode("판교로 242", type="road", refine=False, simple=True)

    query = _query(responses.calls[0])
    assert query["service"] == ["address"]
    assert query["request"] == ["getcoord"]
    assert query["version"] == ["2.0"]
    assert query["address"] == ["판교로 242"]
    assert query["type"] == ["road"]
    assert query["refine"] == ["false"]
    assert query["simple"] == ["true"]


@responses.activate
def test_reverse_geocode_query_params(client, ok_payload):
    responses.add(responses.GET, BASE + "/req/address", json=ok_payload)

    client.reverse_geocode((127.101313354, 37.402352535), type="both", zipcode=False)

    query = _query(responses.calls[0])
    assert query["request"] == ["getaddress"]
    assert query["point"] == ["127.101313354,37.402352535"]
    assert query["type"] == ["both"]
    assert query["zipcode"] == ["false"]


@responses.activate
def test_data_feature_query_params_and_domain(client, ok_payload):
    responses.add(responses.GET, BASE + "/req/data", json=ok_payload)

    client.get_data_feature(
        "LT_C_ADEMD_INFO",
        attr_filter=["emd_cd:=:11650108", "emd_kor_nm:like:서초"],
        columns=["emd_cd", "full_nm"],
        geometry=False,
        attribute=True,
        buffer=10,
        domain="example.com",
    )

    query = _query(responses.calls[0])
    assert query["service"] == ["data"]
    assert query["request"] == ["GetFeature"]
    assert query["data"] == ["LT_C_ADEMD_INFO"]
    assert query["attrFilter"] == ["emd_cd:=:11650108|emd_kor_nm:like:서초"]
    assert query["columns"] == ["emd_cd,full_nm"]
    assert query["geometry"] == ["false"]
    assert query["attribute"] == ["true"]
    assert query["buffer"] == ["10"]
    assert query["domain"] == ["example.com"]


@responses.activate
def test_data_feature_type_query_params(client, ok_payload):
    responses.add(responses.GET, BASE + "/req/data", json=ok_payload)

    client.get_data_feature_type("LT_C_ADEMD_INFO")

    query = _query(responses.calls[0])
    assert query["request"] == ["GetFeatureType"]
    assert query["version"] == ["2.0"]


def test_missing_key_raises_before_network(monkeypatch):
    monkeypatch.delenv("VWORLD_API_KEY", raising=False)
    monkeypatch.delenv("VWORLD_KEY", raising=False)
    with pytest.raises(VworldAuthError):
        VworldClient(api_key=None).search_place("판교")


@responses.activate
def test_search_district_and_road_helpers(client, ok_payload):
    responses.add(responses.GET, BASE + "/req/search", json=ok_payload)
    responses.add(responses.GET, BASE + "/req/search", json=ok_payload)

    client.search_district("삼평동")
    client.search_road("판교로")

    assert _query(responses.calls[0])["type"] == ["district"]
    assert _query(responses.calls[0])["category"] == ["L4"]
    assert _query(responses.calls[1])["type"] == ["road"]
