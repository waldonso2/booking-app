"""Import of the runs, EUR conversion, the order of the results, the CLI."""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from booking import cli, measure, store
from booking.main import create_app

from .conftest import FIXTURES, QUERY, RATES, seeded

ECB_XML = """<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
 xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref"><Cube><Cube time="2026-10-21">
 <Cube currency="USD" rate="1.0850"/><Cube currency="PHP" rate="62.10"/></Cube></Cube></gesmes:Envelope>"""


def test_ecb_rates():
    assert store.ecb_rates(ECB_XML) == {"EUR": 1, "USD": Decimal("1.0850"), "PHP": Decimal("62.10")}


def test_prices_highest_first_in_eur_unknown_currency_last(tmp_path):
    db = store.connect(seeded(tmp_path / "m.db"))
    rows = [(p["country"], p["eur"]) for p in store.prices(db, QUERY)]
    assert rows == [("US", "4000.00"), ("US", "3900.00"), ("JP", "3500.00"), ("JP", None)]
    assert store.import_runs(db, FIXTURES, RATES) == 0  # imported once only
    (q,) = store.queries(db)
    assert (q["runs"], q["low"], q["high"]) == (2, 3500.0, 4000.0)


def test_pages(tmp_path):
    client = TestClient(create_app(seeded(tmp_path / "m.db")))
    assert "4000.00 €" in client.get("/").text
    page = client.get("/messung", params={"q": QUERY}).text
    assert page.index("4000.00") < page.index("3900.00") < page.index("3500.00")
    assert "SG (abweichend)" in page and "blocked: unusual traffic" in page
    assert client.get("/messung", params={"q": "nothing"}).status_code == 404


def test_empty_start_page(tmp_path):
    assert "Noch keine Messungen" in TestClient(create_app(tmp_path / "m.db")).get("/").text


def test_cli_measure_passes_the_query(monkeypatch, tmp_path, capsys):
    seen = {}

    def fake(site, q, country, out, contact, pick, chromium):
        seen.update(q=q, country=country, contact=contact)
        return measure.Result("x", country, "USD", {}, "", "", status="ok")

    monkeypatch.setattr(measure, "measure", fake)
    code = cli.main(["measure", "--country", "US", "--from", "fra", "--to", "atl", "--depart", "2027-03-26",
                     "--return", "2027-04-09", "--cabin", "business", "--contact", "a@example.org",
                     "--out", str(tmp_path)])
    assert code == 0 and seen["q"] == measure.Query("FRA", "ATL", date(2027, 3, 26), date(2027, 4, 9), "business")
    assert "US: ok" in capsys.readouterr().out


def test_cli_rejects_a_bad_query(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["measure", "--country", "US", "--from", "FRANKFURT", "--to", "ATL", "--depart", "2027-03-26",
                  "--return", "2027-04-09", "--contact", "a@example.org", "--out", str(tmp_path)])


def test_cli_import(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("BOOKING_DB", str(tmp_path / "m.db"))
    monkeypatch.setattr(store, "ecb_rates", lambda: RATES)
    assert cli.main(["import", str(FIXTURES)]) == 0
    assert "2 Läufe importiert" in capsys.readouterr().out


@pytest.mark.parametrize(("label", "name"), [
    ("Book with GotogateMX$86,874ContinueView options", "Gotogate"), ("Book with Gulf AirAirline · €2,485", "Gulf Air"),
    ("Book with GotogateCHF 3,837ContinueView options", "Gotogate"), ("Book with Tripado · €4,132", "Tripado"),
    ("Book with business-class.com · €4,022", "business-class.com"), ("Book with Gotogate₪14,374Continue", "Gotogate"),
    ("Book with MytripR$23,431ContinueView options", "Mytrip"), ("Book with UnitedAirline · Local price", "United"),
    ("Something else entirely", "Something else entirely"),
])
def test_seller_names_from_googles_labels(label, name):
    assert store.seller(label) == name


def test_report_lists_the_booking_options_highest_first_and_the_cheapest_per_country(tmp_path, capsys):
    db = store.connect(seeded(tmp_path / "m.db"))
    text = store.report(db)
    assert "| 1 | 3900.00 | 4231.50 USD | US | Testair |" in text
    assert "| US | 3900.00 | 4231.50 USD | Testair |" in text
    assert "ohne Ergebnis: JP (blocked)" in text
    assert "in allen Ländern: Testair" in text and "| US | – |" in text


def test_cli_report(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("BOOKING_DB", str(seeded(tmp_path / "m.db")))
    assert cli.main(["report"]) == 0
    assert "Günstigster Preis je Land" in capsys.readouterr().out


def test_cli_probe_passes_the_url(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(measure, "probe", lambda url, out, contact, chromium: {"status": "ok", "http": 200,
                                                                              "final_url": url, "error": ""})
    assert cli.main(["probe", "https://example.org/", "--contact", "a@example.org", "--out", str(tmp_path)]) == 0
    assert "ok 200 https://example.org/" in capsys.readouterr().out
