"""One measurement: a flight query on a booking site from the country this machine is in, step by step up to the
last price shown before booking. Nothing is booked: every flow ends on a page that only lists prices."""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.robotparser
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeout

# Country → the currency its point of sale shows. Only currencies with an ECB reference rate, so every price can
# be converted to EUR; each country needs a cloud region of its own (docs/TESTLAEUFE.md).
COUNTRIES = {
    "AU": "AUD", "BR": "BRL", "CA": "CAD", "CH": "CHF", "DE": "EUR", "ES": "EUR", "FR": "EUR", "GB": "GBP",
    "HK": "HKD", "ID": "IDR", "IE": "EUR", "IL": "ILS", "IN": "INR", "IT": "EUR", "JP": "JPY", "KR": "KRW",
    "MX": "MXN", "MY": "MYR", "NL": "EUR", "NO": "NOK", "NZ": "NZD", "PL": "PLN", "SE": "SEK", "SG": "SGD",
    "US": "USD", "ZA": "ZAR",
}
CABINS = ("economy", "premium economy", "business", "first")
AGENT = "BookingResearch/0.1"  # the token robots.txt rules are read for
# A price as the sites show it with language English: a currency marker, then digits with thousands commas.
# Only the study's currency codes count as a marker: any three capitals would take an airport ("YYZ1 stop") for one.
PRICE = re.compile(r"(?<![A-Za-z])(?:[A-Z]{1,3}\$|[€$£¥₹₩₪₱]|" + "|".join(sorted(set(COUNTRIES.values()))) + r"|R)\s?"
                   r"((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{2})?)(?![\d,:])")
BLOCKED = ("unusual traffic", "captcha", "not a robot")
WAIT_MS = 30_000


@dataclass(frozen=True)
class Query:
    origin: str
    destination: str
    depart: date
    back: date
    cabin: str = "economy"
    adults: int = 1

    def __post_init__(self) -> None:
        for code in (self.origin, self.destination):
            if not re.fullmatch(r"[A-Z]{3}", code):
                raise ValueError(f"not an IATA code: {code!r}")
        if self.cabin not in CABINS:
            raise ValueError(f"cabin must be one of {', '.join(CABINS)}")
        if not 1 <= self.adults <= 9:
            raise ValueError("adults: 1 to 9")
        if self.back < self.depart:
            raise ValueError("return before departure")

    @property
    def key(self) -> str:
        return (f"{self.origin}-{self.destination} {self.depart}/{self.back} {self.cabin} "
                f"{self.adults} Erw.")


@dataclass
class Step:
    name: str
    url: str
    screenshot: str
    rows: list[dict[str, str]] = field(default_factory=list)  # label, amount, currency


@dataclass
class Result:
    site: str
    country: str
    currency: str
    query: dict[str, Any]
    started: str
    user_agent: str
    ip_country: str = ""
    status: str = "ok"  # ok | robots | blocked | error
    error: str = ""
    cabin_shown: bool = False
    steps: list[Step] = field(default_factory=list)


def parse_rows(texts: list[str], currency: str, spoken: list[str] | None = None) -> list[dict[str, str]]:
    """A row's text → its price and a label (the rest of the row, one line). Where the row's price element names its
    amount for screen readers ("4630 US dollars"), that amount counts: the row may show others ("€4,123")."""
    rows = []
    for i, text in enumerate(texts):
        m = PRICE.search(text)
        said = re.search(r"\d[\d,]*(?:\.\d+)?", spoken[i]) if spoken and spoken[i] else None
        if not (m or said):
            continue
        rest = text[:m.start()] + text[m.end():] if m else text
        label = " · ".join(line.strip() for line in rest.splitlines() if line.strip())
        amount = (said.group() if said else m.group(1) if m else "").replace(",", "")
        rows.append({"label": label[:200], "amount": amount, "currency": currency})
    return rows


class GoogleFlights:
    """Search → outbound flights → return flights → booking options (the sellers and their prices). The flow stops
    there: the next click would leave for a seller's booking page."""

    name = "google-flights"

    def __init__(self, base: str = "https://www.google.com") -> None:
        self.base = base.rstrip("/")

    def search_url(self, q: Query, country: str, currency: str) -> str:
        text = (f"Flights to {q.destination} from {q.origin} on {q.depart} through {q.back} "
                f"{q.cabin} class {q.adults} adults")
        return f"{self.base}/travel/flights?q={quote(text)}&hl=en&gl={country}&curr={currency}"

    def run(self, page: Page, q: Query, result: Result, out: Path, pick: str = "") -> None:
        page.goto(self.search_url(q, result.country, result.currency))
        reject = page.get_by_role("button", name=re.compile(r"^Reject all$", re.I))
        if reject.count():  # the cookie consent of EU countries; the same choice everywhere
            reject.first.click()
            page.wait_for_load_state()
        result.cabin_shown = q.cabin in page.inner_text("body").lower()
        rows = _snapshot(page, result, out, "Hinflug", selector=FLIGHT)
        _click(page, _pick(rows, f"{q.origin}–{q.destination}", pick))
        rows = _snapshot(page, result, out, "Rückflug", rows, FLIGHT)
        back = _pick(rows, f"{q.destination}–{q.origin}")
        _click(page, back)
        # Return flights carry seller-like prices too: only the booking page has the booking options.
        try:
            page.wait_for_url(BOOKING, timeout=10_000)
        except PlaywrightTimeout:  # a click the page didn't take: once more from the keyboard
            _click(page, back, keyboard=True)
            page.wait_for_url(BOOKING, timeout=WAIT_MS)
        _snapshot(page, result, out, "Buchungsoptionen", rows, SELLER)


# Marks each row and returns its text and the spoken price. With a selector, each match anchors a row: the largest
# element around it holding no other match. Without, the rows are the largest elements holding exactly one price.
ROWS_JS = """([source, selector]) => {
  const rx = new RegExp(source, "g");
  const one = el => ((el.innerText || "").match(rx) || []).length === 1;
  const only = el => el.parentElement && el.parentElement !== document.body
    && el.parentElement.querySelectorAll(selector).length === 1;
  const grow = el => { while (only(el)) el = el.parentElement; return el; };
  const anchors = selector ? [...document.querySelectorAll(selector)] : [];
  const rows = selector ? anchors.map(grow) : [...document.querySelectorAll("body *")]
    .filter(el => one(el) && (el.parentElement === document.body || !one(el.parentElement)));
  for (const name of ["data-booking-row", "data-booking-anchor"])
    document.querySelectorAll(`[${name}]`).forEach(el => el.removeAttribute(name));
  rows.forEach((el, i) => el.setAttribute("data-booking-row", String(i)));
  anchors.forEach((el, i) => el.setAttribute("data-booking-anchor", String(i)));
  return rows.map((el, i) => ({text: el.innerText, spoken: anchors[i] ? anchors[i].getAttribute("aria-label") : ""}));
}"""
BOOKING = re.compile(r"/booking")
# A flight in Google Flights' lists: the link over its row, named "From 4293 US dollars ... Select flight".
FLIGHT = '[role=link][aria-label*="Select flight"]'
# A seller's price among the booking options, named "4630 US dollars" (price insights have no data-gs).
SELLER = 'span[role=text][aria-label][data-gs]:not([data-gs=""])'


ROWS_HTML = """(size) => [...document.querySelectorAll("[data-booking-row]")]
  .map(el => el.outerHTML.replace(/<svg[\\s\\S]*?<\\/svg>/g, "<svg/>")
    .replace(/ (jslog|jsaction|data-ved)="[^"]*"/g, "").slice(0, size)).join("\\n----\\n")"""


def _rows(page: Page, before: list[str] | None, selector: str) -> list[dict[str, str]]:
    """The page's priced rows, once there are some and they differ from the previous step's."""
    for _ in range(WAIT_MS // 500):
        rows: list[dict[str, str]] = page.evaluate(ROWS_JS, [PRICE.pattern, selector])
        if rows and [r["text"] for r in rows] != before:
            return rows
        body = page.inner_text("body").lower()
        if any(b in body for b in BLOCKED):
            raise Blocked(body[:200])
        page.wait_for_timeout(500)
    raise TimeoutError("no prices on the page")


def _snapshot(page: Page, result: Result, out: Path, name: str, before: list[str] | None = None,
              selector: str = "") -> list[str]:
    rows = _rows(page, before, selector)
    texts = [r["text"] for r in rows]
    n = len(result.steps) + 1
    shot = f"{n}-{name}.png"
    page.screenshot(path=out / shot, full_page=True)
    (out / f"{n}-{name}.html").write_text(page.content(), encoding="utf-8")
    (out / f"{n}-{name}.rows.html").write_text(page.evaluate(ROWS_HTML, 3000), encoding="utf-8")  # what was read
    result.steps.append(Step(name, page.url, shot, parse_rows(texts, result.currency, [r["spoken"] for r in rows])))
    return texts


def _pick(texts: list[str], route: str, pick: str = "") -> int:
    """The row to continue with: the first flight of the route (rows name it, e.g. "FRA–ATL") containing `pick` (the
    same flight in every country), else the route's first flight, else the first row."""
    flights = [i for i, t in enumerate(texts) if route in t]
    return next((i for i in flights if pick.lower() in texts[i].lower()), flights[0] if flights else 0)


def _click(page: Page, index: int, keyboard: bool = False) -> None:
    row = page.locator(f'[data-booking-row="{index}"]').first
    anchor = page.locator(f'[data-booking-anchor="{index}"]')  # the flight's own link, when a selector found it
    target = anchor if anchor.count() else row.locator("a, [role=link]")  # not buttons: they open details
    target = target.first if target.count() else row
    try:
        if keyboard:
            raise PlaywrightTimeout("keyboard")
        target.click(timeout=5000)
    except PlaywrightTimeout:  # a link laid over the row can be hidden from the mouse: the keyboard reaches it
        if row.count():  # unless the click went through after all and the page moved on
            target.focus()
            target.press("Enter")
    page.wait_for_timeout(2000)  # a pause like a reader's, and time for the next view


class Blocked(Exception):
    pass


def allowed(url: str) -> bool:
    """Whether the site's robots.txt lets this study fetch `url` (an unreachable robots.txt allows nothing)."""
    parts = urlsplit(url)
    robots = urllib.robotparser.RobotFileParser(f"{parts.scheme}://{parts.netloc}/robots.txt")
    try:
        robots.read()
    except OSError:
        return False
    return robots.can_fetch(AGENT, url)


def ip_country() -> str:
    """The country this machine's address is located in, as a geo-IP service sees it (recorded, not trusted)."""
    try:
        with urllib.request.urlopen("https://ipinfo.io/country", timeout=10) as r:
            return str(r.read().decode().strip())
    except OSError:
        return ""


def measure(site: GoogleFlights, q: Query, country: str, out: Path, contact: str, pick: str = "",
            chromium: str | None = None, locate: bool = True) -> Result:
    """Runs the site's flow from here and writes `result.json`, screenshots and page copies to `out`."""
    out.mkdir(parents=True, exist_ok=True)
    currency = COUNTRIES[country]
    result = Result(site.name, country, currency, {**asdict(q), "key": q.key},
                    datetime.now(UTC).isoformat(timespec="seconds"), "",
                    ip_country() if locate else "")
    if not allowed(site.search_url(q, country, currency)):
        result.status, result.error = "robots", "robots.txt der Seite verbietet den Abruf"
    else:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium)
            ua = browser.new_page().evaluate("navigator.userAgent")
            # The browser says who measures and how to reach them; the same everywhere.
            result.user_agent = f"{ua} {AGENT} (Universitaet Stuttgart; {contact})"
            page = browser.new_context(user_agent=result.user_agent, locale="en-US",
                                       viewport={"width": 1280, "height": 900}).new_page()
            try:
                site.run(page, q, result, out, pick)
            except Blocked as e:
                result.status, result.error = "blocked", str(e)
            except Exception as e:  # recorded with a screenshot: a failed step is a result too
                result.status, result.error = "error", f"{type(e).__name__}: {e}"[:1500]
                page.screenshot(path=out / "error.png", full_page=True)
            if result.status != "ok":  # what the page said and how its rows are built, to see why
                rows = page.evaluate(ROWS_HTML, 1500)
                (out / "error.txt").write_text(f"{page.url}\n\n{rows}\n\n{page.inner_text('body')}",
                                               encoding="utf-8")
            browser.close()
    text = json.dumps(asdict(result), ensure_ascii=False, indent=1, default=str)
    (out / "result.json").write_text(text, encoding="utf-8")
    return result
