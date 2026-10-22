"""A fabricated stand-in for CHECK24 Flüge with the same steps: cookie banner, search form (airport suggestions,
calendar), result list, the offer with its price checked once more. "Zur Buchung" links to /buchung, which the flow
must never open. Prices and airlines are made up."""

from __future__ import annotations

from html import escape

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

PAGE = "<!doctype html><html lang='de'><body><main>{}</main></body></html>"
# The suggestions always start with another airport, as CHECK24's do ("FRA" → MUC second, here first).
FORM = """
<div><button onclick="this.parentElement.remove()">Nur notwendige Cookies</button></div>
<p>Flüge von Köln nach Palma de Mallorca · Ab 57 €</p>
<label><input type=radio name=flightType value=rt> Hin- und Rückflug</label>
<label><input type=radio name=flightType value=ow checked> Nur Hinflug</label>
<select name=classOfService><option>Economy</option><option>Premium Economy</option><option>Business</option>
<option>First Class</option></select>
<input id=fl-airportOrigin1 oninput="suggest(this)"> <input id=fl-airportDestination1 oninput="suggest(this)">
<ul id=suggest></ul>
<input type=button id=fl-day-picker-type-outbound value=Reisezeitraum onclick="show()">
<div id=cal hidden><button type=button data-testid=next_month_btn onclick="next()">›</button>
<table><tbody><tr id=days></tr></tbody></table></div>
<button type=button data-testid=search_form_primary_button onclick="search()">Suchen</button>
<script>
const chosen = {}, picked = [];
let month = new Date(2026, 9, 1);
function suggest(input) {
  const ul = document.getElementById("suggest");
  ul.innerHTML = ["MUC", input.value.toUpperCase()].map((c, i) =>
    `<li role=button data-testid=airport_item_${i}><strong data-testid=airport_iata>${c}</strong></li>`).join("");
  ul.querySelectorAll("li").forEach(li => li.onclick = () => {
    chosen[input.id] = li.innerText; input.value = ""; ul.innerHTML = ""; });
}
function show() { document.getElementById("cal").hidden = false; render(); }
function next() { month = new Date(month.getFullYear(), month.getMonth() + 1, 1); render(); }
function render() {
  const y = month.getFullYear(), m = month.getMonth(), n = new Date(y, m + 1, 0).getDate();
  const day = i => `${y}-${String(m + 1).padStart(2, "0")}-${String(i + 1).padStart(2, "0")}`;
  const row = document.getElementById("days");
  row.innerHTML = Array.from({length: n}, (_, i) =>
    `<td role=gridcell data-day="${day(i)}"><button type=button>${i + 1}</button></td>`).join("");
  row.querySelectorAll("td").forEach(td => td.querySelector("button").onclick = () => picked.push(td.dataset.day));
}
function search() {
  const o = chosen["fl-airportOrigin1"], d = chosen["fl-airportDestination1"];
  const rt = document.querySelector("input[value=rt]").checked;
  const cls = document.querySelector("select").value === "Business" ? "BF" : "Y";
  location = `/search?from_0=${o}-A&to_0=${d}-A&date_0=${picked[0]}&from_1=${d}-A&to_1=${o}-A`
    + `&date_1=${picked[1]}&adt=1&class=${cls}&rt=${rt}`;
}
</script>"""
OFFERS = [("Testair", "10:30", "4.122,79 €", "4.150,00 €"), ("Mockline", "12:00", "3.277,20 €", "3.277,20 €")]


def offer(n: int, airline: str, time: str, price: str, checked: str, origin: str) -> str:
    return (f"<div data-testid=offer_{n}><div data-testid=flight_0_info>{time} {origin} {airline}</div>"
            f"<div data-testid=price_panel><span data-testid=price_formatted>{price}</span></div>"
            f"<button type=button data-testid=offer_primary_button onclick=\"open_({n}, '{checked}')\">"
            "Zum Angebot</button></div>")


RESULTS = """<div data-testid=filter_transfer_count_box><span>Direktflug</span>
<span data-testid=filter_transfer_count_0_price>Ab 3.000 €</span></div>
{offers}
<div id=modal hidden><div data-testid=flight_details>Hinflug · <span id=airline></span> ·
<span data-testid=carrier_details_class_of_service>Business</span></div>
<div data-testid=pricing_delayed_message>Einen Moment bitte, das Angebot wird geprüft…</div>
<div data-testid=price_and_cta_row><span id=price></span> <a data-testid=go_to_booking href=/buchung>Zur Buchung</a>
</div></div>
<script>
function open_(n, checked) {{
  const offer = document.querySelector(`[data-testid=offer_${{n}}]`);
  document.getElementById("airline").innerText = offer.querySelector("[data-testid=flight_0_info]").innerText;
  document.getElementById("price").innerText = offer.querySelector("[data-testid=price_formatted]").innerText;
  document.getElementById("modal").hidden = false;
  setTimeout(() => {{
    document.querySelector("[data-testid=pricing_delayed_message]").remove();
    document.getElementById("price").innerText = checked; }}, 800);
}}
</script>"""


def create(requests: list[str]) -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def log(request: Request, call_next):  # type: ignore[no-untyped-def]
        requests.append(request.url.path + (f"?{request.url.query}" if request.url.query else ""))
        return await call_next(request)

    @app.get("/robots.txt", response_class=PlainTextResponse)
    def robots() -> str:
        return "User-agent: *\nDisallow: /buchung\n"

    @app.get("/", response_class=HTMLResponse)
    def form() -> str:
        return PAGE.format(FORM)

    @app.get("/search", response_class=HTMLResponse)
    def search(from_0: str) -> str:
        origin = escape(from_0.removesuffix("-A"))
        offers = "".join(offer(n, *o, origin) for n, o in enumerate(OFFERS))
        return PAGE.format(RESULTS.format(offers=offers))

    @app.get("/buchung", response_class=HTMLResponse)
    def booking() -> str:
        return PAGE.format("<p>Anmelden und Reisedaten eingeben</p>")

    return app
