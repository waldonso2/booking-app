"""A fabricated stand-in for Google Flights with the same steps: consent, outbound, return, booking options. The
booking options link to /pay, which the flow must never open. Prices and airlines are made up."""

from __future__ import annotations

from html import escape

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse

PAGE = "<!doctype html><html lang='en'><body><main>{}</main></body></html>"
OUTBOUND = [("Testair", "10:15 AM – 2:50 PM", "2,345"), ("Mockline", "1:05 PM – 9:30 PM", "1,999")]
RETURN = [("Testair", "5:40 PM – 8:10 AM+1", "2,345")]
SELLERS = [("Book with Testair", "2,345"), ("Book with Example Travel", "2,290.50")]


def rows(items: list[tuple[str, ...]], href: str, currency: str) -> str:
    return "".join(f"<li><a href='{href}'><div>{' </div><div>'.join(i[:-1])}</div><div>{currency}{i[-1]}</div></a>"
                   "</li>" for i in items)


def create(requests: list[str], robots: str = "User-agent: *\nAllow: /\n") -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def log(request: Request, call_next):  # type: ignore[no-untyped-def]
        requests.append(request.url.path)
        return await call_next(request)

    @app.get("/robots.txt", response_class=PlainTextResponse)
    def robots_txt() -> str:
        return robots

    @app.get("/travel/flights", response_class=HTMLResponse)
    def search(request: Request, q: str, curr: str) -> HTMLResponse:
        if "consent" not in request.cookies:
            return HTMLResponse(PAGE.format("<form method='post' action='/consent'><button>Reject all</button></form>"))
        return HTMLResponse(PAGE.format(f"<p>{escape(q)}</p><select><option>Business</option></select>"
                                        f"<ul>{rows(OUTBOUND, '/return?curr=' + escape(curr), '€')}</ul>"))

    @app.post("/consent")
    def consent(request: Request) -> RedirectResponse:
        r = RedirectResponse(request.headers.get("referer", "/"), status_code=303)
        r.set_cookie("consent", "rejected")
        return r

    @app.get("/return", response_class=HTMLResponse)
    def back(curr: str) -> str:
        return PAGE.format(f"<ul>{rows(RETURN, '/booking?curr=' + escape(curr), '€')}</ul>")

    @app.get("/booking", response_class=HTMLResponse)
    def booking(curr: str) -> str:
        return PAGE.format(f"<ul>{rows(SELLERS, '/pay', '€')}</ul>")

    @app.get("/pay", response_class=HTMLResponse)
    def pay() -> str:
        return PAGE.format("<p>payment</p>")

    @app.get("/blocked/travel/flights", response_class=HTMLResponse)
    def blocked() -> str:
        return PAGE.format("<p>Our systems have detected unusual traffic from your computer network.</p>")

    return app
