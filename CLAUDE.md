# Booking App

PLACEHOLDER: what it does. FastAPI + Jinja2 web app (`src/booking/`), built from `waldonso2/template-python-web`
(quality-kit). Docs and UI texts German, CLAUDE.md, code and comments English.

## Commands

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install --require-hashes --only-binary :all: -r requirements.txt
pip install --no-deps --no-build-isolation -e . && pip install --require-hashes --only-binary :all: -r requirements-dev.txt
ruff check src tests && mypy src && pytest -q --cov=booking   # what CI blocks on
pytest tests/perf_report.py -q                           # performance report, never blocking
scripts/lock.sh                                          # after changing a dependency (needs uv)
```

## Quality rules (quality-kit - keep them)

- **Blocking:** ruff (incl. `S` bandit, `SIM`, `PERF`, `C4`, `RUF`, C901 ≤ 15), mypy strict, pytest with coverage ≥ 90 %,
  pip-audit, dependency review, gitleaks, zizmor (≥ medium), and `tests/test_ui_browser.py`: every page in `PAGES`
  (`tests/conftest.py`) in Chromium, light and dark, phone and desktop - no axe-core violation (contrast included), no
  CSP violation, script error or failed load, nothing wider than the phone. **A new page goes into `PAGES`.**
- **Performance is only reported, never blocking** (owner's rule): `tests/perf_report.py` (no `test_` prefix) runs in
  the CI job `performance` with `continue-on-error` and writes its table to the run's summary. New measurements of
  the project's own main operations go there, with a reference value. `KENNZAHLEN.md` lists every KPI.
- A deliberate exception to a rule carries its reason: `# noqa: <code> - <why>`.
- **CSP without `unsafe-inline`:** no `style=` attributes or inline scripts in templates; colours as tokens in
  `static/style.css`, light and dark, each text colour ≥ 4.5:1. Tables have `<caption class="sr-only">`, `<thead>`,
  `<th scope="col">` and `data-label` on cells (they stack on phones).
- **Dependencies only locked with hashes** (`requirements*.txt` from `scripts/lock.sh`), installed with
  `--require-hashes --only-binary :all:`; a dependency change runs `scripts/lock.sh` in the same commit.
- **GitHub Actions and quality-kit workflows pinned to commit SHAs** with the version as a comment; Dependabot waits
  7 days (`cooldown`).
- **Secrets never in the repo**; test data is fabricated (allowed test values in `.gitleaks.toml`).
- Questions to the owner go as a clickable list (the question tool), never as free text.
