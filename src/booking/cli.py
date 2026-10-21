"""`booking-app measure` (on a machine in the country), `booking-app import` and `booking-app serve` (centrally)."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from . import measure, store


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="booking-app")
    sub = p.add_subparsers(dest="command", required=True)
    m = sub.add_parser("measure", help="one run from this machine's country")
    m.add_argument("--country", required=True, choices=sorted(measure.COUNTRIES))
    m.add_argument("--from", dest="origin", required=True)
    m.add_argument("--to", dest="destination", required=True)
    m.add_argument("--depart", required=True, type=date.fromisoformat)
    m.add_argument("--return", dest="back", required=True, type=date.fromisoformat)
    m.add_argument("--cabin", default="economy", choices=measure.CABINS)
    m.add_argument("--adults", default=1, type=int)
    m.add_argument("--pick", default="", help="text of the outbound flight to continue with (e.g. 'Lufthansa')")
    m.add_argument("--contact", required=True, help="e-mail of the research group, sent in the user agent")
    m.add_argument("--out", required=True, type=Path)
    i = sub.add_parser("import", help="import result.json files into the database")
    i.add_argument("folder", type=Path)
    sub.add_parser("serve", help="the results page on http://127.0.0.1:8000")
    a = p.parse_args(argv)

    if a.command == "measure":
        try:
            q = measure.Query(a.origin.upper(), a.destination.upper(), a.depart, a.back, a.cabin, a.adults)
        except ValueError as e:
            p.error(str(e))
        r = measure.measure(measure.GoogleFlights(), q, a.country, a.out, a.contact, a.pick,
                            os.environ.get("CHROMIUM_PATH") or None)
        print(f"{r.country}: {r.status} {r.error}".rstrip())
        return 0 if r.status == "ok" else 1
    db = store.connect(Path(os.environ.get("BOOKING_DB", "data/messungen.db")))
    if a.command == "import":
        print(f"{store.import_runs(db, a.folder, store.ecb_rates())} Läufe importiert")
        return 0
    from .main import run

    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
