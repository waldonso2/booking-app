"""The web app: pages from Jinja templates, security headers with a strict CSP (no inline styles or scripts)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

HERE = Path(__file__).parent

# Nothing from outside, no inline style or script: the browser test fails on any CSP violation.
CSP = ("default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; form-action 'self'; "
       "frame-ancestors 'none'; base-uri 'none'")
HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def create_app() -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    templates = Jinja2Templates(directory=HERE / "templates")  # autoescape is on for .html
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        response.headers.update(HEADERS)
        return response

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "index.html", {"title": "Start"})

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
