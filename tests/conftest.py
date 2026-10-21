"""Shared fixtures: the app served over HTTP, and Chromium for the browser checks."""

from __future__ import annotations

import os
import socket
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import uvicorn

from booking import store
from booking.main import create_app

FIXTURES = Path(__file__).parent / "fixtures"
QUERY = "FRA-ATL 2027-03-26/2027-04-09 business 1 Erw."
RATES = {"EUR": Decimal(1), "USD": Decimal("1.0850"), "JPY": Decimal("163.20")}
# Every page a user reaches: the browser test (axe, CSP, phone width) and the performance report open each one.
PAGES = ["/", "/messung?q=FRA-ATL%202027-03-26%2F2027-04-09%20business%201%20Erw."]
PHONE = {"width": 375, "height": 740}
DESKTOP = {"width": 1280, "height": 900}


def seeded(path: Path) -> Path:
    """A database with the fabricated runs of tests/fixtures imported."""
    store.import_runs(store.connect(path), FIXTURES, RATES)
    return path


@contextmanager
def serve(app: Any) -> Iterator[str]:
    """An ASGI app on a free local port (a real server: the browser needs one)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_config=None))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(5)


@pytest.fixture(scope="session")
def site(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """The app with the fabricated runs."""
    with serve(create_app(seeded(tmp_path_factory.mktemp("db") / "m.db"))) as url:
        yield url


@pytest.fixture(scope="session")
def browser():
    """Chromium from `python -m playwright install chromium` (CI); CHROMIUM_PATH points to another build.
    Without one the browser tests are skipped locally and fail in CI."""
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        except Exception as e:  # no browser installed
            if os.environ.get("CI"):
                raise
            pytest.skip(f"no Chromium for Playwright: {e}")
        yield b
        b.close()
