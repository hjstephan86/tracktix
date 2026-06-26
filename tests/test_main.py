"""Tests for main app wiring: static files, SPA fallback, startup."""


def test_index_html(client):
    """/ should return the SPA HTML."""
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "TrackTix" in r.text


def test_spa_fallback(client):
    """Unknown paths should be served as the SPA for client-side routing."""
    r = client.get("/some/deep/route")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_static_css(client):
    r = client.get("/static/css/style.css")
    assert r.status_code == 200
    assert "text/css" in r.headers["content-type"]


def test_static_js(client):
    r = client.get("/static/js/app.js")
    assert r.status_code == 200


def test_openapi_schema(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "TrackTix" in r.json()["info"]["title"]


def test_docs_endpoint(client):
    r = client.get("/docs")
    assert r.status_code == 200
