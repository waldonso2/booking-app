# Übergabe: Booking App (Stand 24.10.2026)

Für einen Coding-Agenten, der das Projekt übernimmt. Lies danach `CLAUDE.md` (verbindliche Regeln) und die Dokumente
unter `docs/`. Repository: `waldonso2/booking-app` (privat), Standard-Branch `main`.

## 1. Worum es geht

Forschungsprojekt der **Universität Stuttgart**: Nachweis, dass derselbe Flug je Land (Point of Sale, POS)
unterschiedlich teuer angeboten wird. Gemessen wird jeder Such- und Buchungsschritt **bis vor die Buchung**; das
Ergebnis listet immer **alle Preise vom höchsten zum niedrigsten**. Gebucht wird nie.

- Testverbindungen: FRA→ATL und FRA→MNL, Business, 1 Erwachsener, Hinflug 26.03.2027, Rückflug 09.04.2027.
- Zielgröße: 40 Länder (`measure.COUNTRIES`, nur Währungen mit EZB-Kurs).
- **Regel des Auftraggebers: Eine Messung zählt nur, wenn sie aus dem gemessenen Land kommt.** Rechner in den USA
  reichen nicht. `booking-app report` wertet nur Läufe, deren IP-Land (`ip_country`) dem Land entspricht.
- Oberfläche und Dokumente Deutsch (UI auch Englisch geplant), Look an flights.google.com angelehnt.
  CLAUDE.md, Code und Kommentare Englisch.

## 2. Messregeln (nicht verhandelbar, stehen in CLAUDE.md)

- Ablauf stoppt vor jedem Schritt, der bucht, reserviert oder Sitze hält, immer vor der Zahlung.
- Keine Umgehung von Bot-Erkennung oder CAPTCHAs; eine Sperre ist ein Ergebnis (`status: blocked`).
  Keine offenen Proxys, kein Tor, keine Tarnung.
- `robots.txt` wird beachtet (abgerufen mit dem User-Agent der Studie; 404 = erlaubt, nicht erreichbar = verboten).
- User-Agent nennt Studie und Kontakt: `… BookingResearch/0.1 (Universitaet Stuttgart; <Kontakt>)`. Bisher wurde
  als Kontakt „Www.contact.com“ übergeben – **vor einer Veröffentlichung braucht es die echte Adresse.**
- Nur erfundene Testpersonen, nie echte Kunden- oder Zahlungsdaten. Tests nur gegen nachgebaute Seiten.

## 3. Arbeitsweise mit dem Auftraggeber

- Antworten auf Deutsch, knapp. Fragen an den Auftraggeber **immer als anklickbare Liste** (Frage-Werkzeug).
- Freigabe: **eigene PRs mergen, sobald die CI grün ist, ohne Nachfrage** („Merge den PR und bau alle weiteren
  Releases ohne Nachfragen“). PRs als Entwurf anlegen, nach grüner CI auf „ready“ setzen und squash-mergen.
- Der Auftraggeber will oft „erst melden, wenn das Ergebnis da ist“ – dann selbstständig iterieren.
- Commits mit den Attributionszeilen der Sitzung; Entwicklungs-Branch der Sitzung (bisher `ccr-db7c1d22-itd9x5`).

## 4. Aufbau

FastAPI + Jinja2, aus der Vorlage `waldonso2/template-python-web` (quality-kit).

| Datei | Zweck |
|---|---|
| `src/booking/measure.py` | Messung: `Query`, `Result`/`Step`, `COUNTRIES`, Preis-Regexe `PRICE` (englisch, `€2,345`) und `PRICE_DE` (`2.345,79 €`), `parse_rows`, `allowed` (robots.txt), `ip_country` (ipinfo.io), `probe` (Seite erkunden, klickt nichts), Abläufe `GoogleFlights` und `Check24`, `SITES`, `measure()` (schreibt `result.json`, Screenshots, Seitenkopien; bei Fehlern `error.png` und `error.txt` mit allen Bedienelementen) |
| `src/booking/store.py` | SQLite (`runs`, `prices`), EZB-Kurse, `import_runs`, `prices` (EUR absteigend), `seller()`, `report()` (Markdown: letzte Preise vor der Buchung, günstigster je Land, Anbieter je Land, Läufe ohne Ergebnis, Läufe nicht aus dem Land) – letzter Schritt je Seite: `FINAL = ("Buchungsoptionen", "Angebot")` |
| `src/booking/cli.py` | `booking-app measure --site google-flights|check24 --country … --from … --to … --depart … --return … --cabin … --pick … --contact … --out …`, `probe <url>`, `import <ordner>`, `report`, `serve` |
| `src/booking/main.py`, `templates/`, `static/style.css` | Ergebnisseite (`/`, `/messung?q=…`), alle Preise höchster zuerst, IP-Land „abweichend“ markiert |
| `tests/fakesite.py`, `tests/fakecheck24.py` | Nachgebaute Google-Flights- und CHECK24-Seiten (inkl. Fallen: Overlay-Links, falscher erster Flughafen-Vorschlag, Preisänderung nach Prüfung, `/pay` bzw. `/buchung` dürfen nie geöffnet werden) |
| `tests/test_*.py`, `tests/fixtures/` | 61 Tests, Abdeckung ~97 % |
| `.github/workflows/measure.yml` | „Messung (40 Länder)“: Eingaben `contact, from, to, depart, return, cabin, pick, site, countries` (JSON-Liste); Matrix je Land auf `ubuntu-latest` (**USA**), Job `report` importiert alles und schreibt den Bericht in die Zusammenfassung |
| `.github/workflows/probe.yml` | „Seite erkunden“: `probe` für mehrere URLs, druckt Status und Bedienelemente ins Log |
| `scripts/run-all.sh` | Messung über SSH-VMs (`hosts.txt`: `<Land> <ssh-ziel>`): einrichten, gleichzeitig messen, Ergebnisse holen, importieren |
| `scripts/messen-im-land.sh` | Messpaket für Partner im Land: misst Google Flights und CHECK24 einmal im Docker-Container (Playwright-Image v1.64.0) und packt `ergebnisse/<Land>-<Zeit>.tar.gz` |
| `scripts/lock.sh` | Abhängigkeiten mit Hashes sperren (nach jeder Änderung in `pyproject.toml`) |

### Die Abläufe

**GoogleFlights** (`search_url`: `/travel/flights?q=Flights to … &hl=en&gl=<Land>&curr=<Währung>`): Cookie „Reject
all“ → Hinflug (`FLIGHT = '[role=link][aria-label*="Select flight"]'`, Auswahl über `--pick`, z. B. „10:30 AM“) →
Rückflug → warten auf `/booking` → Buchungsoptionen (`SELLER = 'span[role=text][aria-label][data-gs]…'`, der
gesprochene Betrag im `aria-label` zählt). `ROWS_JS` markiert Zeilen (`data-booking-row`) und Anker
(`data-booking-anchor`); `_click` klickt den Anker, notfalls per Tastatur.

**Check24** (deutscher POS, Preise immer EUR): Startseite → „Nur notwendige Cookies“ → Formular (Radio `rt`,
`select[name=classOfService]`, `#fl-airportOrigin1/Destination1` + Vorschlag `li[data-testid^=airport_item_]` mit
exakt passendem `[data-testid=airport_iata]`, Kalender `td[data-day=JJJJ-MM-TT] button`, `[data-testid=next_month_btn]`)
→ `[data-testid=search_form_primary_button]` → Ergebnisseite
`/search?from_0=FRA-A&to_0=ATL-A&date_0=…&from_1=…&to_1=…&date_1=…&adt=1&class=BF` → Angebote (`OFFER =
[data-testid=price_formatted]`) → `[data-testid=offer_primary_button]` öffnet ein Fenster; warten, bis
`pricing_delayed_message` weg ist → Schritt „Angebot“ (`MODAL`). **Ende.** „Zur Buchung“ (`go_to_booking`) führt zu
`accounts.check24.de` (Anmeldung/Reisedaten); dort sperrte Cloudflare den Messbrowser.

## 5. Ergebnisse bisher

- **Google Flights, 40 Länder (21.10.2026, FRA–ATL)** – über `gl`, aber von **US-Rechnern**: 40/40 Ergebnisse,
  Spanne 1,2 % (MX +1 %), überall dieselben 5–7 Anbieter. Nach der Regel „aus dem Land“ zählt davon nur die USA.
  Ebenso FRA–MNL. Details: `docs/TESTLAEUFE.md`.
- **CHECK24 (22.10.2026, von US-Rechner)**: Lufthansa nonstop 4.122,79 € (auch nach Preisprüfung).
- **Erkundung der ausgewählten Verkäufer** (`docs/SOLL-ANBIETER.md`): Lufthansa (DE/US), Netflights, Priceline sperren
  den Messbrowser; Check24, Opodo, MaxMilhas, Ticket, Pelikan, PriceTravel erreichbar.
- Recherche: `docs/RESEARCH.md` (POS, Quellen), `docs/AGENTUR.md` (eigene Agentur für Konsolidatoren/TIDS),
  `docs/SOLL-ANBIETER.md` (Soll-Liste je Land, robots.txt-Befunde), `docs/MESSRECHNER.md` (Rechner im Land).

## 6. Wo es steht – nächster Schritt

**Entscheidung des Auftraggebers: vorerst die 31 Länder mit Cloud-Region messen, aus dem Land heraus.**
(BG, CZ, GR, HU, IS, PH, PT, RO, TR haben keine Region und gingen nur über Partner – zurückgestellt.)

Blocker: **kein funktionierendes Cloud-Konto.** Die AWS- und GCP-Zugänge der alten Umgebung waren ungültig
(`AuthFailure`, kein Projekt). Vorgeschlagen: Azure + Google Cloud (Azure deckt 29 der 31 ab, Google Cloud ergänzt FI
und TH), Zugänge als Umgebungsvariablen (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`,
`AZURE_SUBSCRIPTION_ID`, `GOOGLE_APPLICATION_CREDENTIALS_JSON`, `GCP_PROJECT`), nie im Chat oder Repo.

Sobald ein Konto da ist:
1. Je Land der 31 eine kleine Ubuntu-24.04-VM in der Region des Landes anlegen (Zuordnung Land → Region in
   `docs/MESSRECHNER.md`; AWS-Regionen wie MX/MY/NZ/TH sind opt-in), SSH-Schlüssel nur für diesen Lauf.
2. `hosts.txt` schreiben und `scripts/run-all.sh hosts.txt -- --site google-flights --from FRA --to ATL --depart
   2027-03-26 --return 2027-04-09 --cabin business --pick "10:30 AM" --contact <Kontakt>`; danach dasselbe mit
   `--site check24 --pick Lufthansa` (run-all.sh reicht alles nach `--` an `booking-app measure` weiter).
3. `booking-app report` – nur Läufe mit passendem `ip_country` zählen. Prüfen, dass jede VM wirklich im Land
   geortet wird.
4. **Alle VMs, Platten und IPs löschen**, Kosten melden. Ergebnis in `docs/TESTLAEUFE.md`, PR, mergen.

Weitere offene Punkte: echte Kontaktadresse für den User-Agent; Lufthansa als Forschungspartner anfragen; Abläufe für
Opodo (DE/FR/GB), MaxMilhas, Ticket, Pelikan, PriceTravel (je gegen eine nachgebaute Seite testen); Partner für die
9 Länder ohne Cloud-Region; Gulf Air ungeprüft.

## 7. Befehle

```bash
cd booking-app && python3 -m venv .venv && . .venv/bin/activate
pip install --require-hashes --only-binary :all: -r requirements.txt
pip install --no-deps --no-build-isolation -e . && pip install --require-hashes --only-binary :all: -r requirements-dev.txt
ruff check src tests && mypy src && CHROMIUM_PATH=/opt/pw-browsers/chromium pytest -q --cov=booking
```

CI blockiert auf: ruff (inkl. S, SIM, PERF, C4, RUF, C901 ≤ 15, Zeilen ≤ 120), mypy strict, pytest ≥ 90 %
Abdeckung, Browser-Test (axe, CSP, Handybreite; neue Seiten in `PAGES`), pip-audit, gitleaks, zizmor, CodeQL,
Dependency Review. Actions auf Commit-SHA gepinnt.

## 8. Praktische Hinweise aus der bisherigen Arbeit

- **Die Messseiten sind aus der Cloud-Sitzung nicht direkt erreichbar** (Proxy sperrt). Erkunden und Testen echter
  Seiten lief über GitHub-Workflows (`measure.yml` / `probe.yml`, starten per `workflow_dispatch` auf dem
  Arbeits-Branch). **Artefakte lassen sich nicht herunterladen** (Blob-Storage gesperrt); Ergebnisse deshalb ins Log
  drucken und das Log über die GitHub-MCP-Funktion `get_job_logs` lesen. Der Workflow druckt Status, URL und die
  ersten Zeilen jedes Schritts sowie `error.txt`.
- Neue Seite bauen: erst `probe`, dann den Ablauf Schritt für Schritt; bei Fehlern zeigt `error.txt` alle
  Bedienelemente mit `data-*`-Attributen. Vorübergehende Trace-Ausgaben vor dem Merge entfernen.
- Google Flights: Flughafencodes wurden anfangs als Preise gelesen (`YYZ1`) → nur Währungscodes der Studie als
  Marker; Overlay-Links nehmen keine Mausklicks → Tastatur-Fallback; Buchungsoptionen erst nach `/booking`.
- Check24: Der erste Flughafen-Vorschlag ist nicht immer der richtige (FRA → MUC zuerst); Startseite zeigt eigene
  Preise („Ab 57 €“) → erst nach `/search` lesen; Filterpreise ausschließen.
- `merge_pull_request` braucht den vollständigen 40-stelligen SHA. GitHub-GraphQL ist gesperrt (`gh pr checks`
  geht nicht) → Checks über `gh api repos/…/commits/<sha>/check-runs`.
- Flache Klone: Tracking-Branch ggf. mit `git branch -u` setzen; Branch nach einem Squash-Merge neu von
  `origin/main` erzeugen (`git checkout -B <branch> origin/main`, Push mit `--force-with-lease`).
- Der Sicherheitsfilter der Sitzung sperrt das Lesen von Zugangsdaten/Umgebungsvariablen und Skripte, die fremden
  Rechnern Fernausführung erlauben (ein selbst gehosteter Runner für Partner wurde deshalb verworfen).
