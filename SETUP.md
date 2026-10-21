# Einstellungen für ein neues Repo

Diese Einstellungen stecken in keiner Datei. Sie werden bei jedem neuen Repo einmal gesetzt, unter
*Settings* des Repos. Bei einer Vorlage selbst zusätzlich: *Settings → General → Template repository*.

## Sicherheit (Settings → Advanced Security bzw. Code security)

- [ ] **Private vulnerability reporting**: an. `SECURITY.md` verweist darauf.
- [ ] **Dependabot alerts** und **Dependabot security updates**: an.
- [ ] **Secret scanning** und **Push protection**: an.
- [ ] **Code scanning / CodeQL**: Entweder das **Default setup** einschalten **oder** die Datei `codeql.yml`
      der Vorlage behalten, **nicht beides**. Sonst lehnt GitHub die Ergebnisse der Datei ab („advanced
      configurations cannot be processed when the default setup is enabled“). Die Vorlagen bringen `codeql.yml`
      mit den Abfragen `security-extended` mit; beim Default setup diese Abfragen unter *Query suite → Extended* wählen.

## Branch `main` (Settings → Rules → Rulesets)

- [ ] Ein Ruleset für `main`: **Pull Request vor dem Merge**, **keine Force-Pushes**, **nicht löschen**.
- [ ] **Pflicht-Checks** (*Require status checks to pass*): die blockierenden Jobs der CI. Welche das sind,
      steht in `KENNZAHLEN.md` des Projekts. Der Job `performance` gehört **nicht** dazu.
- [ ] **Require linear history** nur, wenn Pull Requests gesquasht werden.

## Actions (Settings → Actions → General)

- [ ] **Workflow permissions**: *Read repository contents and packages permissions* (die Workflows fordern mehr nur
      dort an, wo sie es brauchen).
- [ ] **Allow GitHub Actions to create and approve pull requests**: aus.

## Nach dem ersten Merge

- [ ] Die Scorecard läuft (`scorecard.yml`, Tab *Actions*), Ergebnis unter *Security → Code scanning*.
- [ ] Auf der Zusammenfassungsseite des ersten CI-Laufs steht der Performance-Bericht.
