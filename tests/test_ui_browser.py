"""Every page in a real browser: axe-core (accessibility incl. contrast, light and dark), no CSP violation, no
script error, no failed load, nothing wider than a phone. Blocking - a new page goes into PAGES (conftest.py)."""

import pytest

from .conftest import DESKTOP, PAGES, PHONE

axe_api = pytest.importorskip("axe_playwright_python.sync_playwright")


def _problems(page, url: str, phone: bool) -> list[str]:
    errors: list[str] = []
    # A failed load is reported with its URL below; the browser's own favicon request has no response event.
    page.on("console", lambda m: errors.append(m.text)
            if m.type == "error" and not m.text.startswith("Failed to load resource") else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("response", lambda r: errors.append(f"{r.status} {r.url}") if r.status >= 400 else None)
    page.goto(url)
    found = [f"{v['id']}: {n['target']} {n['failureSummary']}"
             for v in axe_api.Axe().run(page).response["violations"] for n in v["nodes"][:3]]
    found += [f"console: {e}" for e in errors]
    if phone and page.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
        found.append("wider than the phone screen")
    return found


@pytest.mark.parametrize("scheme", ["light", "dark"])
@pytest.mark.parametrize("viewport", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_every_page_passes_axe_csp_and_fits(site, browser, scheme, viewport):
    context = browser.new_context(color_scheme=scheme, viewport=viewport)
    page = context.new_page()
    report = {path: _problems(page, site + path, viewport is PHONE) for path in PAGES}
    context.close()
    assert not {p: f for p, f in report.items() if f}
