"""The study's data: the measurements' `result.json` files imported into SQLite, prices converted to EUR."""

from __future__ import annotations

import json
import re
import sqlite3
import urllib.request
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from typing import Any

ECB = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY, dir TEXT UNIQUE, query TEXT, site TEXT, country TEXT, currency TEXT, started TEXT,
  ip_country TEXT, status TEXT, error TEXT, cabin_shown INTEGER, user_agent TEXT);
CREATE TABLE IF NOT EXISTS prices (
  run INTEGER REFERENCES runs(id), step TEXT, position INTEGER, label TEXT, amount TEXT, currency TEXT,
  eur TEXT, rate TEXT);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def ecb_rates(xml: str | None = None) -> dict[str, Decimal]:
    """Units of each currency per EUR, from the ECB's daily reference rates (EUR itself is 1)."""
    if xml is None:
        with urllib.request.urlopen(ECB, timeout=20) as r:
            xml = r.read().decode()
    root = ET.fromstring(xml)  # noqa: S314 - trusted source, no entities
    rates = {el.attrib["currency"]: Decimal(el.attrib["rate"]) for el in root.iter() if "currency" in el.attrib}
    return {"EUR": Decimal(1), **rates}


def import_runs(db: sqlite3.Connection, folder: Path, rates: dict[str, Decimal]) -> int:
    """Imports every `result.json` below `folder` not imported before; returns how many were new."""
    new = 0
    for file in sorted(folder.rglob("result.json")):
        if db.execute("SELECT 1 FROM runs WHERE dir = ?", (str(file.parent),)).fetchone():
            continue
        r: dict[str, Any] = json.loads(file.read_text(encoding="utf-8"))
        run = db.execute(
            "INSERT INTO runs (dir, query, site, country, currency, started, ip_country, status, error, cabin_shown,"
            " user_agent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(file.parent), r["query"]["key"], r["site"], r["country"], r["currency"], r["started"],
             r["ip_country"], r["status"], r["error"], int(r["cabin_shown"]), r["user_agent"])).lastrowid
        for step in r["steps"]:
            for i, row in enumerate(step["rows"]):
                rate = rates.get(row["currency"])
                eur = None if rate is None else str((Decimal(row["amount"]) / rate).quantize(Decimal("0.01")))
                db.execute("INSERT INTO prices VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (run, step["name"], i, row["label"], row["amount"], row["currency"], eur,
                            None if rate is None else str(rate)))
        new += 1
    db.commit()
    return new


def queries(db: sqlite3.Connection) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT query, COUNT(DISTINCT runs.id) AS runs, MIN(CAST(eur AS REAL)) AS low, MAX(CAST(eur AS REAL)) AS high"
        " FROM runs LEFT JOIN prices ON prices.run = runs.id GROUP BY query ORDER BY query").fetchall()


def runs(db: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
    return db.execute("SELECT * FROM runs WHERE query = ? ORDER BY country", (query,)).fetchall()


def prices(db: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
    """Every price measured for the query, highest first (in EUR; prices without a rate last)."""
    return db.execute(
        "SELECT runs.country, runs.started, step, label, amount, prices.currency, eur FROM prices"
        " JOIN runs ON prices.run = runs.id WHERE query = ?"
        " ORDER BY eur IS NULL, CAST(eur AS REAL) DESC, country", (query,)).fetchall()


# "Book with GotogateMX$86,874ContinueView options" → "Gotogate": the name ends where Google's labels run on.
SELLER = re.compile(r"Book with (.+?)(?=Airline\b|Continue|[A-Z]{1,3}[$€£¥₹₩₪₱]|[$€£¥₹₩₪₱]|[A-Z]{3} \d| ·|$)")


def seller(label: str) -> str:
    m = SELLER.match(label)
    return m.group(1).strip() if m else label.split(" · ")[0][:60]


def report(db: sqlite3.Connection, step: str = "Buchungsoptionen") -> str:
    """Markdown per query: every price of the last step highest first, the cheapest per country, and failed runs."""
    out = []
    for q in queries(db):
        rows = [p for p in prices(db, q["query"]) if p["step"] == step]
        out += [f"## {q['query']}", "", "| # | EUR | Preis | Land | Anbieter |", "|---|---|---|---|---|"]
        out += [f"| {i} | {p['eur'] or '–'} | {p['amount']} {p['currency']} | {p['country']} | "
                f"{seller(p['label'])} |" for i, p in enumerate(rows, 1)]
        cheapest: dict[str, sqlite3.Row] = {}
        for p in rows:  # highest first, so the last one per country is its cheapest
            cheapest[p["country"]] = p
        best = sorted(cheapest.values(), key=lambda p: float(p["eur"] or "inf"))
        out += ["", "Günstigster Preis je Land:", "", "| Land | EUR | Preis | Anbieter |", "|---|---|---|---|"]
        out += [f"| {p['country']} | {p['eur'] or '–'} | {p['amount']} {p['currency']} | "
                f"{seller(p['label'])} |" for p in best]
        sellers: dict[str, set[str]] = {}
        for p in rows:
            sellers.setdefault(p["country"], set()).add(seller(p["label"]))
        everywhere = set.intersection(*sellers.values()) if sellers else set()
        out += ["", f"Anbieter je Land (in allen Ländern: {', '.join(sorted(everywhere)) or 'keiner'}):", "",
                "| Land | weitere Anbieter |", "|---|---|"]
        out += [f"| {c} | {', '.join(sorted(names - everywhere)) or '–'} |" for c, names in sorted(sellers.items())]
        failed = [f"{r['country']} ({r['status']})" for r in runs(db, q["query"]) if r["status"] != "ok"]
        out += ["", f"Läufe: {len(runs(db, q['query']))}, ohne Ergebnis: {', '.join(failed) or 'keine'}", ""]
    return "\n".join(out)
