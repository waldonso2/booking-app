"""Shared fixtures: the app served over HTTP, and Chromium for the browser checks."""

from __future__ import annotations

import os
import socket
import threading
import time
from collections.abc import Iterator

import pytest
import uvicorn

from booking.main import create_app

# Every page a user reaches: the browser test (axe, CSP, phone width) and the performance report open each one.
PAGES = ["/"]
PHONE = {"width": 375, "height": 740}
DESKTOP = {"width": 1280, "height": 900}


@pytest.fixture(scope="session")
def site() -> Iterator[str]:
    """The app served on a free local port (a real server: the browser needs one)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(), host="127.0.0.1", port=port, log_config=None))
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
