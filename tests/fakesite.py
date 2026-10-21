"""A fabricated stand-in for Google Flights with the same steps: consent, outbound, return, booking options. The
booking options link to /pay, which the flow must never open. Prices and airlines are made up."""

from __future__ import annotations

from html import escape

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse

PAGE = "<!doctype html><html lang='en'><body><main>{}</main></body></html>"
OUTBOUND = [("Testair", "10:15 AM – 2:50 PM", "FRA–ATL", "Nonstop", "2,345"),
            ("Mockline", "1:05 PM – 9:30 PM", "FRA–ATL", "1 stop", "1 hr 35 min YYZ", "1,999")]
RETURN = [("Testair", "5:40 PM – 8:10 AM+1", "ATL–FRA", "2,345")]
SELLERS = [("Book with Testair", "2,345"), ("Book with Example Travel", "2,290.50")]


def rows(items: list[tuple[str, ...]], href: str, currency: str, mouse: str = "", flights: bool = True) -> str:
    """List items as Google Flights builds them: a link over the row, named "... Select flight". `mouse`: "hidden"
    takes no clicks at all, "ignored" takes them but does nothing; the keyboard reaches both."""
    link = "role='link' aria-label='From {} euros round trip total. Select flight'" if flights else ""
    keys = " onclick='event.preventDefault()' onkeydown='if (event.key === \"Enter\") location = this.href'"
    link += {"": "", "hidden": " style='pointer-events: none'", "ignored": keys}[mouse]
    said = "" if flights else " role='text' data-gs='x' aria-label='{} euros'"  # sellers' prices, as Google marks them
    return "".join(f"<li><button>Details</button><div>{' </div><div>'.join(i[:-1])}</div>"
                   f"<div><span{said.format(i[-1].replace(',', ''))}>{currency}{i[-1]}</span></div>"
                   f"<a {link.format(i[-1])} href='{href}&amp;row={n}'>Weiter</a></li>" for n, i in enumerate(items))


def create(requests: list[str], robots: str = "User-agent: *\nAllow: /\n") -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def log(request: Request, call_next):  # type: ignore[no-untyped-def]
        requests.append(request.url.path + (f"?{request.url.query}" if request.url.query else ""))
        return await call_next(request)

    @app.get("/robots.txt", response_class=PlainTextResponse)
    def robots_txt() -> str:
        return robots

    @app.get("/travel/flights", response_class=HTMLResponse)
    def search(request: Request, q: str, curr: str) -> HTMLResponse:
        if "consent" not in request.cookies:
            return HTMLResponse(PAGE.format("<form method='post' action='/consent'><button>Reject all</button></form>"))
        return HTMLResponse(PAGE.format(f"<p>{escape(q)}</p><select><option>Business</option></select>"
                                        "<p>Cheapest</p><p>from €1,999</p>"
                                        f"<ul>{rows(OUTBOUND, '/return?curr=' + escape(curr), '€', 'hidden')}</ul>"))

    @app.post("/consent")
    def consent(request: Request) -> RedirectResponse:
        r = RedirectResponse(request.headers.get("referer", "/"), status_code=303)
        r.set_cookie("consent", "rejected")
        return r

    @app.get("/return", response_class=HTMLResponse)
    def back(curr: str) -> str:
        return PAGE.format(f"<ul>{rows(RETURN, '/booking?curr=' + escape(curr), '€', 'ignored')}</ul>")

    @app.get("/booking", response_class=HTMLResponse)
    def booking(curr: str) -> str:
        insight = "<div><span>€2,290</span> is <strong>typical</strong></div><div>€1,600</div><div>€5,300</div>"
        return PAGE.format(f"<ul>{rows(SELLERS, '/pay?', '€', flights=False)}</ul>{insight}")

    @app.get("/pay", response_class=HTMLResponse)
    def pay() -> str:
        return PAGE.format("<p>payment</p>")

    @app.get("/blocked/travel/flights", response_class=HTMLResponse)
    def blocked() -> str:
        return PAGE.format("<p>Our systems have detected unusual traffic from your computer network.</p>")

    return app
