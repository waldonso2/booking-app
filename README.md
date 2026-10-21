# Booking App

PLATZHALTER: was das Projekt macht, in zwei Sätzen.

Aus der Vorlage [`template-python-web`](https://github.com/waldonso2/template-python-web) des
[quality-kit](https://github.com/waldonso2/quality-kit): Sicherheit, Barrierefreiheit und Leistung werden in der CI
geprüft, die Kennzahlen stehen in [`KENNZAHLEN.md`](KENNZAHLEN.md).

## Nach „Use this template“ ersetzen

- [x] Name und Paketname (`booking`)
- [ ] `PLATZHALTER` (Beschreibung) in `README.md`, `CLAUDE.md`, `KENNZAHLEN.md`, `pyproject.toml` und `src/booking/`
- [ ] `scripts/lock.sh` laufen lassen, sobald eigene Abhängigkeiten dazukommen
- [ ] die Einstellungen aus [`SETUP.md`](https://github.com/waldonso2/quality-kit/blob/main/SETUP.md) setzen

## Entwickeln

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install --require-hashes --only-binary :all: -r requirements.txt
pip install --no-deps --no-build-isolation -e .
pip install --require-hashes --only-binary :all: -r requirements-dev.txt
python -m playwright install chromium   # einmal, für die Browser-Checks
ruff check src tests && mypy src && pytest -q --cov=booking
pytest tests/perf_report.py -q          # Performance-Bericht (perf-report.md)
booking-app                             # startet die App auf http://127.0.0.1:8000
```
