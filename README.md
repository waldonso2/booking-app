# quality-kit

Das gemeinsame Qualitäts-Paket aller Projekte: Sicherheit, Bedienbarkeit (UI/UX) und Leistung, geprüft in der CI.
Es besteht aus drei Teilen:

1. **Dieses Repo:** die Workflows, die nicht von der Programmiersprache abhängen. Jedes Projekt ruft sie auf.
2. **Vorlagen** (GitHub-Template-Repos, „Use this template“), eine pro Technik. Sie enthalten alles, was vom
   Code abhängt: Tests, Linter, Browser-Checks, Performance-Bericht, `KENNZAHLEN.md`.
3. **[`SETUP.md`](SETUP.md):** die Repo-Einstellungen, die keine Datei sind. Sie werden bei jedem neuen Repo einmal gesetzt.

## Vorlagen

| Vorlage | Für | Prüft zusätzlich |
|---|---|---|
| [`template-python-web`](https://github.com/waldonso2/template-python-web) | Web-Dienste in Python (FastAPI, Jinja) | ruff (inkl. Bandit), mypy, pytest ≥ 90 %, pip-audit, Abhängigkeiten mit Hashes, jede Seite in Chromium (axe, CSP, Handybreite), Performance-Bericht (Core Web Vitals) |
| [`template-python-cli`](https://github.com/waldonso2/template-python-cli) | Werkzeuge und Bibliotheken in Python | wie oben, ohne Browser; Performance-Bericht der Kernfunktionen |
| [`template-ts-react`](https://github.com/waldonso2/template-ts-react) | Web-Oberflächen in TypeScript/React | ESLint (inkl. jsx-a11y), tsc strict, Vitest ≥ 90 % mit axe, `pnpm audit --prod`, CodeQL, jede Seite in Chromium (axe, CSP, Handybreite), Performance-Bericht (Core Web Vitals, Paketgröße) |
| [`template-rust`](https://github.com/waldonso2/template-rust) | Dienste und Werkzeuge in Rust (statt Python) | clippy `-D warnings`, rustfmt, cargo test ≥ 90 % (cargo-llvm-cov), cargo-deny (Lücken, Lizenzen, Quellen), CodeQL, Performance-Bericht |

## Gemeinsame Workflows

| Workflow | Prüft | Art |
|---|---|---|
| `secrets.yml` | gitleaks über die ganze Historie; erlaubte Testwerte in `.gitleaks.toml` des Projekts | blockierend |
| `workflows.yml` | zizmor: die GitHub-Workflows selbst (Injection, Rechte, Cache Poisoning, ungepinnte Actions) | blockierend ab „medium“ |
| `dependency-review.yml` | bei Pull Requests: neue Abhängigkeiten mit bekannten Lücken | blockierend |

Aufruf im Projekt, an einen Commit gepinnt (Dependabot schlägt Updates vor):

```yaml
jobs:
  secrets:
    uses: waldonso2/quality-kit/.github/workflows/secrets.yml@<commit-sha> # v1
  workflows:
    uses: waldonso2/quality-kit/.github/workflows/workflows.yml@<commit-sha> # v1
  dependency-review:
    uses: waldonso2/quality-kit/.github/workflows/dependency-review.yml@<commit-sha> # v1
```

OpenSSF Scorecard bleibt eine Datei im Projekt (`scorecard.yml` in jeder Vorlage). Scorecard veröffentlicht seine
Ergebnisse nur aus einem Workflow, der im geprüften Repo selbst liegt.

## Regeln, die überall gelten

- **Actions nur an Commit-SHAs gepinnt**, mit der Version als Kommentar. Dependabot schlägt Updates erst vor, wenn
  sie 7 Tage alt sind (`cooldown`).
- **Performance hält die CI nie an.** Sie wird gemessen und als Tabelle auf der Zusammenfassungsseite des CI-Laufs
  gezeigt, mit Referenzwert und ✅/⚠️ (`continue-on-error`).
- **Barrierefreiheit, CSP, Sicherheit und Tests blockieren.** Eine bewusste Ausnahme steht im Code mit Begründung
  (`# noqa: <code> - <warum>`, `// eslint-disable-next-line <regel> -- <warum>`, `#[allow(...)] // warum`).
- **Kennzahlen** stehen in `KENNZAHLEN.md` jedes Projekts, gegliedert nach ISO/IEC 25010. Referenzen: OWASP ASVS 5.0
  Stufe 2, OWASP Top 10, OpenSSF Scorecard, SLSA, WCAG 2.2 AA, Core Web Vitals, Nielsens Antwortzeiten.

## Neues Projekt

1. Auf GitHub: Vorlage öffnen → **Use this template** → **Create a new repository**.
2. Die Punkte aus [`SETUP.md`](SETUP.md) setzen.
3. Im neuen Repo die Platzhalter ersetzen (`README.md`, `CLAUDE.md`, Paketname). Die Vorlage nennt sie in ihrem README.

## Versionen

Änderungen an den Workflows bekommen ein Tag `v<n>`. Projekte pinnen den Commit dieses Tags; ein Tag, das ein
bestehendes Verhalten ändert (strenger prüft), ist eine neue Hauptversion.
