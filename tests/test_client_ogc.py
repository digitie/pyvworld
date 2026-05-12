from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
import responses

from vworld.exceptions import VworldInvalidParameterError

BASE = "https://api.vworld.kr"


def _query(call) -> dict[str, list[str]]:
    return parse_qs(urlparse(call.request.url).query, keep_blank_values=True)


@responses.activate
def test_wms_get_map_params(client):
    responses.add(responses.GET, BASE + "/req/wms", body=b"png", content_type="image/png")

    response = client.wms_get_map(
        layers=["lp_pa_cbnd_bonbun", "lp_pa_cbnd_bubun"],
        styles=["line1", "line2"],
        bbox=(14133818.022824, 4520485.8511757, 14134123.770937, 4520791.5992888),
        width=256,
        height=256,
        transparent=True,
        domain="example.com",
    )

    assert response.content == b"png"
    query = _query(responses.calls[0])
    assert query["SERVICE"] == ["WMS"]
    assert query["REQUEST"] == ["GetMap"]
    assert query["VERSION"] == ["1.3.0"]
    assert query["LAYERS"] == ["lp_pa_cbnd_bonbun,lp_pa_cbnd_bubun"]
    assert query["STYLES"] == ["line1,line2"]
    assert query["CRS"] == ["EPSG:900913"]
    assert query["WIDTH"] == ["256"]
    assert query["HEIGHT"] == ["256"]
    assert query["TRANSPARENT"] == ["true"]
    assert query["domain"] == ["example.com"]


@responses.activate
def test_wms_get_feature_info_params(client):
    responses.add(responses.GET, BASE + "/req/wms", body="<info/>", content_type="text/xml")

    result = client.wms_get_feature_info(
        layers="lt_c_uq111",
        query_layers="lt_c_uq111",
        bbox="1,2,3,4",
        width=512,
        height=512,
        i=10,
        j=20,
        feature_count=5,
    )

    assert result.text == "<info/>"
    query = _query(responses.calls[0])
    assert query["REQUEST"] == ["GetFeatureInfo"]
    assert query["I"] == ["10"]
    assert query["J"] == ["20"]
    assert query["FEATURE_COUNT"] == ["5"]


@responses.activate
def test_wfs_get_feature_params(client):
    responses.add(responses.GET, BASE + "/req/wfs", body="<gml/>", content_type="text/xml")

    result = client.wfs_get_feature(
        "lt_c_uq111",
        bbox=(13987670, 3912271, 14359383, 4642932),
        property_name=["mnum", "sido_cd"],
        max_features=40,
        filter="<ogc:Filter/>",
    )

    assert result.text == "<gml/>"
    query = _query(responses.calls[0])
    assert query["SERVICE"] == ["WFS"]
    assert query["REQUEST"] == ["GetFeature"]
    assert query["TYPENAME"] == ["lt_c_uq111"]
    assert query["MAXFEATURES"] == ["40"]
    assert query["PROPERTYNAME"] == ["mnum,sido_cd"]
    assert query["SRSNAME"] == ["EPSG:900913"]
    assert query["OUTPUT"] == ["GML2"]
    assert query["FILTER"] == ["<ogc:Filter/>"]


@responses.activate
def test_capabilities_and_describe_feature_type(client):
    responses.add(responses.GET, BASE + "/req/wms", body="<wms/>")
    responses.add(responses.GET, BASE + "/req/wfs", body="<wfs/>")
    responses.add(responses.GET, BASE + "/req/wfs", body="<schema/>")

    assert client.wms_get_capabilities().text == "<wms/>"
    assert client.wfs_get_capabilities().text == "<wfs/>"
    assert client.wfs_describe_feature_type(["lt_c_uq111", "lt_c_uq112"]).text == "<schema/>"

    assert _query(responses.calls[0])["REQUEST"] == ["GetCapabilities"]
    assert _query(responses.calls[1])["SERVICE"] == ["WFS"]
    assert _query(responses.calls[2])["REQUEST"] == ["DescribeFeatureType"]
    assert _query(responses.calls[2])["TYPENAME"] == ["lt_c_uq111,lt_c_uq112"]


@responses.activate
def test_ogc_accepts_explicit_blank_domain(client):
    responses.add(responses.GET, BASE + "/req/wms", body="<wms/>")

    assert client.wms_get_capabilities(domain="").text == "<wms/>"

    assert _query(responses.calls[0])["domain"] == [""]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"width": 0, "height": 256},
        {"width": 256, "height": -1},
    ],
)
def test_wms_map_rejects_bad_dimensions(client, kwargs):
    with pytest.raises(VworldInvalidParameterError):
        client.wms_get_map(layers="x", bbox="1,2,3,4", **kwargs)


def test_wms_url_builder_and_feature_info_validation(client):
    assert "REQUEST=GetMap" in client.wms_get_map_url(
        layers="x",
        bbox="1,2,3,4",
        width=256,
        height=256,
    )
    with pytest.raises(VworldInvalidParameterError):
        client.wms_get_feature_info(
            layers="x",
            query_layers="x",
            bbox="1,2,3,4",
            width=0,
            height=1,
            i=0,
            j=0,
        )
    with pytest.raises(VworldInvalidParameterError):
        client.wms_get_feature_info(
            layers="x",
            query_layers="x",
            bbox="1,2,3,4",
            width=1,
            height=1,
            i=-1,
            j=0,
        )


def test_wfs_get_feature_rejects_bad_max_features(client):
    with pytest.raises(VworldInvalidParameterError):
        client.wfs_get_feature("lt_c_uq111", max_features=0)
