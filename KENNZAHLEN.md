# Kennzahlen

Woran dieses Projekt Sicherheit, Bedienbarkeit und Leistung misst, gegliedert nach **ISO/IEC 25010**.
**Blockierend:** Die CI scheitert, wenn der Wert nicht erreicht wird. Diese Jobs sind die Pflicht-Checks des
Branch-Schutzes ([`SETUP.md`](https://github.com/waldonso2/quality-kit/blob/main/SETUP.md)). **Bericht:** Der Wert
wird gemessen und auf der Zusammenfassungsseite des CI-Laufs gezeigt (Job `performance`), hält die CI aber nie an.

## Sicherheit

| Kennzahl | Ziel | Referenz | Wo gemessen | Art |
|---|---|---|---|---|
| Anforderungen an die Anwendung | Stufe 2 | OWASP ASVS 5.0 | Reviews, Tests | Leitlinie |
| Häufigste Risiken abgedeckt | alle 10 | OWASP Top 10 (2025) | Reviews, CodeQL | Leitlinie |
| Funde der Code-Analyse | 0 offen | CodeQL (`codeql.yml`, security-extended) | Security → Code scanning | Bericht |
| Funde in den Workflows | 0 ab „medium“ | zizmor | Job `workflows` | blockierend |
| Bekannte Lücken in Abhängigkeiten | 0 | pip-audit, Dependency Review | Jobs `audit`, `dependency-review` | blockierend |
| Abhängigkeiten | nur gesperrte Versionen mit Hashes, nur Wheels | eigene Regel | `requirements*.txt`, Job `test` | blockierend |
| Sicherheitsregeln im Code | 0 Funde | ruff `S` (Bandit) | Job `test` | blockierend |
| Geheimnisse im Repository | 0 | gitleaks | Job `secrets` | blockierend |
| Sicherheits-Header, CSP ohne `unsafe-inline` | gesetzt | OWASP Secure Headers | `tests/test_app.py`, Browser-Test | blockierend |
| Sicherheit des Repositorys | ≥ 7 von 10 | OpenSSF Scorecard | `scorecard.yml` | Bericht |
| Zeit bis zur Behebung einer Lücke | kritisch ≤ 7 Tage, hoch ≤ 30 Tage | übliche Fristen | Dependabot, Advisories | Leitlinie |

## Bedienbarkeit

| Kennzahl | Ziel | Referenz | Wo gemessen | Art |
|---|---|---|---|---|
| Barrierefreiheit | 0 Verstöße | WCAG 2.2 AA (EN 301 549, BFSG), axe-core | `tests/test_ui_browser.py`: jede Seite, hell/dunkel, Handy/Desktop | blockierend |
| Farbkontrast | ≥ 4,5 : 1 (Text) | WCAG 2.2 AA | axe-core im selben Test | blockierend |
| CSP-Verstöße, Skriptfehler, fehlgeschlagene Ladevorgänge | 0 | eigene Regel | Konsole im selben Test | blockierend |
| Handy zuerst | keine Seite breiter als 375 px | eigene Regel | selber Test | blockierend |
| Rückmeldung | sofort ≤ 0,1 s, ohne Unterbrechung ≤ 1 s, ab 10 s Fortschritt | Nielsen | Gestaltung | Leitlinie |

axe findet automatisch etwa die Hälfte der WCAG-Probleme; Tastatur und Screenreader bei größeren Änderungen von Hand prüfen.

## Leistung

Gemessen in `tests/perf_report.py` auf dem CI-Runner; entscheidend ist die Entwicklung von Lauf zu Lauf.

| Kennzahl | Ziel | Referenz | Art |
|---|---|---|---|
| TTFB, langsamste Seite | ≤ 800 ms | Core Web Vitals | Bericht |
| LCP, schlechteste Seite | ≤ 2,5 s | Core Web Vitals | Bericht |
| CLS, schlechteste Seite | ≤ 0,1 | Core Web Vitals | Bericht |
| Übertragene Daten, größte Seite | ≤ 500 KiB | Seitengewicht | Bericht |
| Antwortzeit des Servers, Median | ≤ 100 ms | Nielsen 0,1 s | Bericht |
| PLATZHALTER: die Kernoperation des Projekts | … | … | Bericht |

## Wartbarkeit

| Kennzahl | Ziel | Wo gemessen | Art |
|---|---|---|---|
| Testabdeckung | ≥ 90 % | pytest-cov, Job `test` | blockierend |
| Komplexität je Funktion | ≤ 15 | ruff C901 | blockierend |
| Typen | mypy strict ohne Fehler | Job `test` | blockierend |
