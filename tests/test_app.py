"""The app's pages and its security headers."""

from pathlib import Path

from fastapi.testclient import TestClient

from booking.main import CSP, create_app

TEMPLATES = Path(__file__).parents[1] / "src" / "booking" / "templates"


def test_index_page_and_security_headers():
    r = TestClient(create_app()).get("/")
    assert r.status_code == 200
    assert "<h1>Start</h1>" in r.text
    assert r.headers["content-security-policy"] == CSP
    assert "unsafe-inline" not in CSP
    assert r.headers["x-content-type-options"] == "nosniff"


def test_no_api_docs_exposed():
    client = TestClient(create_app())
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_templates_have_no_inline_styles_or_scripts():
    for template in TEMPLATES.glob("*.html"):
        text = template.read_text(encoding="utf-8")
        assert "style=" not in text and "<script" not in text, template.name


def test_tables_are_semantic():
    for template in TEMPLATES.glob("*.html"):
        text = template.read_text(encoding="utf-8")
        if "<table" in text:
            assert '<caption class="sr-only">' in text and "<thead>" in text and 'scope="col"' in text, template.name
