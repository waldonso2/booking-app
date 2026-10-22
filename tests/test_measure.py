"""The measurement flow against the fabricated site, price parsing, and the query checks."""

import json
import os
from datetime import date

import pytest

from booking import measure
from booking.measure import GoogleFlights, Query, parse_rows

from . import fakesite
from .conftest import serve

Q = Query("FRA", "ATL", date(2027, 3, 26), date(2027, 4, 9), "business")


@pytest.fixture
def fake():
    requests: list[str] = []
    with serve(fakesite.create(requests)) as url:
        yield url, requests


def run(site_url, tmp_path, **kw):
    pytest.importorskip("playwright.sync_api")
    try:
        return measure.measure(GoogleFlights(site_url), Q, "US", tmp_path, "study@example.org",
                               chromium=os.environ.get("CHROMIUM_PATH") or None, locate=False, **kw)
    except Exception as e:  # no browser installed
        if os.environ.get("CI") or "Executable doesn't exist" not in str(e):
            raise
        pytest.skip(f"no Chromium for Playwright: {e}")


def test_flow_measures_every_step_and_never_opens_the_payment(fake, tmp_path):
    url, requests = fake
    r = run(url, tmp_path, pick="Mockline")
    assert r.status == "ok", r.error
    assert [s.name for s in r.steps] == ["Hinflug", "Rückflug", "Buchungsoptionen"]
    assert [row["amount"] for row in r.steps[0].rows] == ["2345", "1999"]  # flights only, not the summary
    assert any(p.startswith("/return?") and p.endswith("row=1") for p in requests)  # the picked flight
    assert len(r.steps[2].rows) == 2  # the sellers, not the price insight below them
    assert r.steps[2].rows[1] == {"label": "Details · Book with Example Travel · Weiter", "amount": "2290.50",
                                  "currency": "USD"}
    assert r.cabin_shown and "Universitaet Stuttgart; study@example.org" in r.user_agent
    assert not any(p.startswith(("/pay", "/help")) for p in requests) and "/consent" in requests
    saved = json.loads((tmp_path / "result.json").read_text())
    assert saved["query"]["key"] == Q.key and (tmp_path / saved["steps"][0]["screenshot"]).exists()


def test_robots_txt_that_disallows_stops_before_the_browser(tmp_path):
    requests: list[str] = []
    with serve(fakesite.create(requests, robots="User-agent: *\nDisallow: /travel/\n")) as url:
        r = measure.measure(GoogleFlights(url), Q, "US", tmp_path, "x@example.org", locate=False)
    assert r.status == "robots" and requests == ["/robots.txt"]


def test_robots_txt_is_fetched_under_the_studys_name_and_a_missing_one_closes_nothing():
    with serve(fakesite.create([])) as url:
        assert measure.allowed(url + "/travel/flights")
    with serve(fakesite.create([], robots=None)) as url:
        assert measure.allowed(url + "/travel/flights")


def test_unreachable_robots_txt_allows_nothing():
    assert not measure.allowed("http://127.0.0.1:9/travel/flights")
    assert not measure.allowed("file:///etc/passwd")


def test_a_block_page_is_a_result(fake, tmp_path):
    url, _ = fake
    r = run(url + "/blocked", tmp_path)
    assert r.status == "blocked" and "unusual traffic" in r.error


def test_a_page_without_prices_is_an_error_with_screenshot(fake, tmp_path, monkeypatch):
    url, _ = fake
    monkeypatch.setattr(measure, "WAIT_MS", 1000)
    r = run(url + "/nothing-here", tmp_path)
    assert r.status == "error" and (tmp_path / "error.png").exists()
    assert "/nothing-here" in (tmp_path / "error.txt").read_text()


def test_search_url_carries_country_currency_and_cabin():
    u = GoogleFlights().search_url(Q, "JP", "JPY")
    assert u.startswith("https://www.google.com/travel/flights?q=Flights%20to%20ATL%20from%20FRA%20on%202027-03-26")
    assert "business%20class" in u and u.endswith("&hl=en&gl=JP&curr=JPY")


@pytest.mark.parametrize(("text", "amount"), [
    ("Lufthansa\n10:15 AM – 2:50 PM\n€2,345", "2345"), ("US$3,210.99 round trip", "3210.99"),
    ("JPY 512,300", "512300"), ("₱150,000\nPAL", "150000"), ("R$ 9,870", "9870"), ("CA$4,100", "4100"),
])
def test_prices_as_shown_with_english(text, amount):
    assert parse_rows([text], "X")[0]["amount"] == amount


def test_times_durations_flight_numbers_and_airports_are_no_prices():
    assert parse_rows(["FRA 10:15 AM\n10 hr 35 min\nLH 400\n1 stop in YYZ1 stop\nORD2 hr"], "EUR") == []


def test_label_is_the_row_without_its_price():
    assert parse_rows(["Testair\n 10:15 AM \n€2,345\nround trip"], "EUR")[0]["label"] == \
        "Testair · 10:15 AM · round trip"


@pytest.mark.parametrize("bad", [{"origin": "Fra"}, {"cabin": "luxury"}, {"adults": 0},
                                 {"back": date(2027, 3, 1)}])
def test_query_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        Query(**{"origin": "FRA", "destination": "ATL", "depart": date(2027, 3, 26), "back": date(2027, 4, 9),
                 **bad})


def test_ip_country_without_network_is_empty(monkeypatch):
    def fail(*a, **k):
        raise OSError

    monkeypatch.setattr(measure.urllib.request, "urlopen", fail)
    assert measure.ip_country() == ""



def test_pick_prefers_the_route_and_the_picked_flight():
    rows = ["from $4,293", "Lufthansa FRA–ATL $4,293", "Delta FRA–ATL $4,580"]
    assert measure._pick(rows, "FRA–ATL") == 1
    assert measure._pick(rows, "FRA–ATL", "delta") == 2
    assert measure._pick(rows, "FRA–ATL", "Condor") == 1
    assert measure._pick(["Book with Delta $4,580"], "ATL–FRA") == 0


def test_the_spoken_amount_wins_over_other_prices_in_the_row():
    rows = parse_rows(["Book with Lufthansa\n$4,630\n€4,123", "no price"], "USD", ["4630 US dollars", ""])
    assert rows == [{"label": "Book with Lufthansa · €4,123", "amount": "4630", "currency": "USD"}]


def test_probe_keeps_the_page_and_its_controls(fake, tmp_path):
    url, requests = fake
    pytest.importorskip("playwright.sync_api")
    found = measure.probe(url + "/travel/flights?q=x&curr=EUR", tmp_path, "x@example.org",
                          os.environ.get("CHROMIUM_PATH") or None)
    assert found["status"] == "ok" and found["http"] == 200
    assert {"tag": "button", "role": "", "type": "", "id": "", "name": "", "label": "Reject all"} in found["controls"]
    assert (tmp_path / "page.png").exists() and "Reject all" in (tmp_path / "page.txt").read_text()
    assert not any(p.startswith("/consent") for p in requests)  # nothing clicked


def test_probe_stops_at_robots_txt(tmp_path):
    requests: list[str] = []
    with serve(fakesite.create(requests, robots="User-agent: *\nDisallow: /\n")) as url:
        assert measure.probe(url + "/", tmp_path, "x@example.org")["status"] == "robots"
    assert requests == ["/robots.txt"]


def test_probe_sees_a_block_page(fake, tmp_path):
    url, _ = fake
    pytest.importorskip("playwright.sync_api")
    assert measure.probe(url + "/blocked/travel/flights", tmp_path, "x@example.org",
                         os.environ.get("CHROMIUM_PATH") or None)["status"] == "blocked"
