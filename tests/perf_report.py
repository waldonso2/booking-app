"""Performance report (KENNZAHLEN.md): measured, compared with the reference values, never failing.

Not collected by `pytest` (no `test_` prefix); the CI job `performance` runs it on its own with continue-on-error:
`pytest tests/perf_report.py -q`. The table goes to $GITHUB_STEP_SUMMARY (the run's summary page) and to
$PERF_REPORT (default perf-report.md). Add the project's own measurements below (its main operation, its data).
"""

from __future__ import annotations

import os
import statistics
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from booking.main import create_app

from .conftest import PAGES, PHONE

ROWS: list[tuple[str, str, str, str, str]] = []  # area, measure, value, reference, verdict


def record(area: str, measure: str, value: float, unit: str, good: float | None = None, source: str = "") -> None:
    verdict = "–" if good is None else ("✅" if value <= good else "⚠️")
    reference = "" if good is None else f"≤ {good:g} {unit} ({source})"
    ROWS.append((area, measure, f"{value:,.1f} {unit}", reference, verdict))


@pytest.fixture(scope="module", autouse=True)
def report():
    yield
    lines = ["## Performance (nur Bericht, hält die CI nicht an)", "",
             "| Bereich | Messung | Wert | Referenz | |", "|---|---|---|---|---|"]
    lines += [f"| {' | '.join(r)} |" for r in ROWS]
    text = "\n".join(lines) + "\n"
    print("\n" + text)
    Path(os.environ.get("PERF_REPORT", "perf-report.md")).write_text(text, encoding="utf-8")
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as f:
            f.write(text)


VITALS = """() => new Promise(done => {
  const nav = performance.getEntriesByType('navigation')[0];
  let lcp = 0, cls = 0;
  new PerformanceObserver(l => l.getEntries().forEach(e => lcp = e.startTime))
    .observe({type: 'largest-contentful-paint', buffered: true});
  new PerformanceObserver(l => l.getEntries().forEach(e => { if (!e.hadRecentInput) cls += e.value; }))
    .observe({type: 'layout-shift', buffered: true});
  const bytes = performance.getEntriesByType('resource').reduce((s, r) => s + r.encodedBodySize, nav.encodedBodySize);
  setTimeout(() => done({ttfb: nav.responseStart - nav.requestStart, lcp, cls, bytes}), 300);
})"""


def test_web_vitals(site, browser):
    context = browser.new_context(viewport=PHONE)
    page = context.new_page()
    vitals = {}
    for path in PAGES:
        page.goto(site + path)
        vitals[path] = page.evaluate(VITALS)
    context.close()
    worst = {k: max(v[k] for v in vitals.values()) for k in ("ttfb", "lcp", "cls", "bytes")}
    # Core Web Vitals "good" (web.dev) - here on the CI runner, without a real network.
    record("Web-UI", "TTFB, langsamste Seite", worst["ttfb"], "ms", 800, "Core Web Vitals")
    record("Web-UI", "LCP, schlechteste Seite", worst["lcp"], "ms", 2500, "Core Web Vitals")
    record("Web-UI", "CLS, schlechteste Seite", worst["cls"], "", 0.1, "Core Web Vitals")
    record("Web-UI", "Übertragen, größte Seite", worst["bytes"] / 1024, "KiB", 500, "Seitengewicht")


def test_server_response():
    client = TestClient(create_app())
    times = []
    for _ in range(50):
        began = time.perf_counter()
        client.get("/")
        times.append((time.perf_counter() - began) * 1000)
    record("Server", "Antwortzeit der Startseite, Median", statistics.median(times), "ms", 100, "Nielsen 0,1 s")
