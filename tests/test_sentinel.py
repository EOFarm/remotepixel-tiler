"""tests remotepixel_tiler.sentinel."""

import os
import json
import numpy

import pytest
from mock import patch

from remotepixel_tiler.sentinel import APP

metadata_results = os.path.join(
    os.path.dirname(__file__), "fixtures", "metadata_sentinel2.json"
)
with open(metadata_results, "r") as f:
    metadata_results = json.loads(f.read())


@pytest.fixture(autouse=True)
def testing_env_var(monkeypatch):
    """Set fake env to make sure we don't hit AWS services."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "jqt")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "rde")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setenv("AWS_CONFIG_FILE", "/tmp/noconfigheere")
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", "/tmp/noconfighereeither")
    monkeypatch.setenv("TOKEN", "YO")


@pytest.fixture()
def event():
    """Event fixture."""
    return {
        "path": "/",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }


@patch("remotepixel_tiler.sentinel.sentinel2")
def test_bounds(sentinel2, event):
    """Should work as expected (get bounds)."""
    sentinel2.bounds.return_value = {
        "sceneid": "S2A_tile_20161202_16SDG_0",
        "bounds": [
            -88.13852907879543,
            36.952925382758686,
            -86.88936926390103,
            37.9475895350879,
        ],
    }

    event["path"] = "/s2/bounds/S2A_tile_20161202_16SDG_0"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"access_token": "YO"}

    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "max-age=3600",
        "Content-Type": "application/json",
    }
    statusCode = 200

    res = APP(event, {})
    assert res["headers"] == headers
    assert res["statusCode"] == statusCode
    result = json.loads(res["body"])
    assert result["bounds"]


@patch("remotepixel_tiler.sentinel.sentinel2")
def test_metadata(sentinel2, event):
    """Should work as expected (get metadata)."""
    sentinel2.metadata.return_value = metadata_results

    event["path"] = "/s2/metadata/S2A_tile_20161202_16SDG_0"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"access_token": "YO"}

    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "max-age=3600",
        "Content-Type": "application/json",
    }
    statusCode = 200

    res = APP(event, {})
    assert res["headers"] == headers
    assert res["statusCode"] == statusCode
    result = json.loads(res["body"])
    assert result["bounds"]
    assert result["statistics"]
    assert len(result["statistics"].keys()) == 13

    event["path"] = "/s2/metadata/S2A_tile_20161202_16SDG_0"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"pmin": "5", "pmax": "95", "access_token": "YO"}
    res = APP(event, {})
    assert res["headers"] == headers
    assert res["statusCode"] == statusCode
    result = json.loads(res["body"])
    assert result["bounds"]
    assert result["statistics"]


@patch("remotepixel_tiler.sentinel.sentinel2")
@patch("remotepixel_tiler.sentinel.expression")
def test_tiles_error(expression, sentinel2, event):
    """Should work as expected (raise error)."""
    event["path"] = "/s2/tiles/S2A_tile_20161202_16SDG_0/10/262/397.png"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"access_token": "YO", "bands": "01", "expr": "01"}

    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
    }
    statusCode = 500

    res = APP(event, {})
    assert res["headers"] == headers
    assert res["statusCode"] == statusCode
    result = json.loads(res["body"])
    assert result["errorMessage"] == "Cannot pass bands and expression"
    sentinel2.assert_not_called()
    expression.assert_not_called()

    event["path"] = "/s2/tiles/S2A_tile_20161202_16SDG_0/10/262/397.png"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"access_token": "YO"}

    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
    }
    statusCode = 500

    res = APP(event, {})
    assert res["headers"] == headers
    assert res["statusCode"] == statusCode
    result = json.loads(res["body"])
    assert result["errorMessage"] == "No bands nor expression given"
    sentinel2.assert_not_called()
    expression.assert_not_called()


@patch("remotepixel_tiler.sentinel.sentinel2")
@patch("remotepixel_tiler.sentinel.expression")
def test_tiles_expr(expression, sentinel2, event):
    """Should work as expected (get tile)."""
    tilesize = 256
    tile = numpy.random.rand(1, tilesize, tilesize)
    mask = numpy.full((tilesize, tilesize), 255)

    expression.return_value = (tile, mask)

    event["path"] = "/s2/tiles/S2A_tile_20161202_16SDG_0/10/262/397.png"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {
        "expr": "(b5-b4)/(b5+b4)",
        "rescale": "-1,1",
        "color_map": "cfastie",
        "access_token": "YO",
    }

    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "max-age=3600",
        "Content-Type": "image/png",
    }
    statusCode = 200

    res = APP(event, {})
    assert res["headers"] == headers
    assert res["statusCode"] == statusCode
    assert res["isBase64Encoded"]
    assert res["body"]
    sentinel2.assert_not_called()

    event["path"] = "/s2/tiles/S2A_tile_20161202_16SDG_0/10/262/397.png"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {
        "expr": "(b04-b03)/(b03+b04)",
        "rescale": "-1,1",
        "color_map": "cfastie",
        "access_token": "YO",
    }
    event["headers"]["Accept-Encoding"] = "gzip, deflate"

    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "max-age=3600",
        "Content-Encoding": "gzip",
        "Content-Type": "image/png",
    }
    statusCode = 200

    res = APP(event, {})
    assert res["headers"] == headers
    assert res["statusCode"] == statusCode
    assert res["isBase64Encoded"]
    assert res["body"]
    sentinel2.assert_not_called()


@patch("remotepixel_tiler.sentinel.sentinel2")
@patch("remotepixel_tiler.sentinel.expression")
def test_tiles_bands(expression, sentinel2, event):
    """Should work as expected (get tile)."""
    tilesize = 256
    tile = numpy.random.rand(3, tilesize, tilesize) * 10000
    mask = numpy.full((tilesize, tilesize), 255)

    sentinel2.tile.return_value = (tile.astype(numpy.uint16), mask)

    event["path"] = "/s2/tiles/S2A_tile_20161202_16SDG_0/10/262/397.png"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {
        "bands": "04,03,02",
        "color_formula": "gamma RGB 3",
        "access_token": "YO",
    }
    event["headers"]["Accept-Encoding"] = "gzip, deflate"

    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "max-age=3600",
        "Content-Encoding": "gzip",
        "Content-Type": "image/png",
    }
    statusCode = 200

    res = APP(event, {})
    assert res["headers"] == headers
    assert res["statusCode"] == statusCode
    assert res["isBase64Encoded"]
    assert res["body"]
    expression.assert_not_called()
