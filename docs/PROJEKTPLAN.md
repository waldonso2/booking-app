# Projektplan Booking App

**Ziel:** Für eine Flugverbindung den weltweit günstigsten buchbaren Preis über alle verfügbaren Points of Sale
finden und den Weg dorthin zeigen. Bedienung auf Deutsch oder Englisch, unabhängig von der Sprache des POS. Optik
nach dem Vorbild von Google Flights (eigene Umsetzung, keine Kopie von Marke oder Logo).

Grundlage: [RESEARCH.md](RESEARCH.md). Leitplanke: Die App bucht mit den echten Daten des Kunden und täuscht keinem
Verkäufer Wohnsitz oder Identität vor (Begründung dort, Abschnitt 3).

## Phase 0 – Lohnt es sich? (Messung, ca. 1–2 Wochen)

Die Kernannahme ist nicht belegt. Deshalb zuerst messen, ohne UI:

- [ ] 30 Strecken (Kurz-, Mittel-, Langstrecke, EU und außerhalb), je 3 Termine
- [ ] je Strecke dieselbe Abfrage in 20–40 Märkten (`gl`) einer Quelle, alles in EUR umgerechnet
- [ ] Ergebnis: Anteil der Abfragen mit ≥ 5 % / ≥ 10 % Ersparnis, Median, welche Märkte, welche Airlines
- [ ] **Entscheidung:** weiter, Fokus ändern (z. B. nur Währung, nur Selbst-Umstieg) oder stoppen

## Phase 1 – Datenquellen und Recht klären (parallel zu Phase 0)

- [ ] Duffel: lässt sich der Markt/POS steuern? Testkonto, eine Abfrage aus zwei Märkten
- [ ] GDS-Weg: Was kostet ein Partner mit Office-IDs in mehreren Ländern (Konsolidator)?
- [ ] Travelpayouts als Vorauswahl (Cache) testen
- [ ] Art. 23 Abs. 2 VO 1008/2008 und Geoblocking-VO im Wortlaut prüfen; anwaltliche Kurzprüfung des Modells
      (Vermittler oder Reisebüro? Pauschalreise- und Zahlungsrecht)

## Phase 2 – MVP (nach positiver Entscheidung)

- [ ] Suche: Von, Nach, Datum(e), Personen, Klasse – DE/EN (`i18n`), Formular serverseitig geprüft
- [ ] Ergebnisliste im Google-Flights-Stil: Verbindung, Dauer, Stopps, bester Preis und **in welchem Markt**,
      Ersparnis gegenüber dem Heimatmarkt
- [ ] Detailseite: Preise je Markt als Tabelle, Weg zur Buchung (Link zur Quelle im jeweiligen Markt)
- [ ] Cache und Ratenbegrenzung pro Quelle; Hintergrundjobs für die Marktabfragen
- [ ] Währungsumrechnung mit Tageskurs und Hinweis auf Zahlungsweise

## Phase 3 – Erweiterungen

- [ ] Kombinationen: Selbst-Umstieg, Positionierungsflug, Open Jaw – mit Risikohinweis
- [ ] Preisalarm (Benachrichtigung bei neuem Tiefstpreis)
- [ ] Buchung direkt in der App (nur über eine buchbare Quelle wie Duffel, mit Zahlungsanbieter)

## Technik (steht durch die Vorlage)

FastAPI + Jinja, serverseitig, keine Skripte im Browser, CSP ohne `unsafe-inline`; alle Qualitätsregeln aus
`CLAUDE.md` (Tests ≥ 90 %, axe in Chromium, Performance-Bericht).

## Risiken

| Risiko | Gegenmaßnahme |
|---|---|
| Ersparnis zu klein/selten | Phase 0 entscheidet, bevor gebaut wird |
| Keine Quelle mit POS-Steuerung zu tragbaren Kosten | früh mit Duffel und einem Konsolidator sprechen |
| AGB-Verstoß beim Scraping | Scraping nur in Phase 0 zur Messung, Produkt nur auf lizenzierten Quellen |
| Rechtliche Einordnung (Vermittler/Reisebüro) | anwaltliche Prüfung in Phase 1 |
| Preise ändern sich zwischen Suche und Buchung | Preis vor Buchung neu abfragen, Zeitstempel zeigen |
