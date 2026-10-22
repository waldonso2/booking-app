# Projektplan Booking App (Forschungsprojekt der Universität Stuttgart)

**Forschungsfrage:** Zeigen Airlines und Buchungsportale derselben Kundin für dieselbe Flugverbindung zur selben
Zeit je nach Land (Point of Sale) andere Preise an, und wie groß sind die Unterschiede?

**Was gemessen wird:** jeder Schritt von der Suche bis zur letzten Preisanzeige vor der Zahlung, je Land. Gebucht
wird nichts. **Ergebnis:** für jede Verbindung alle gemessenen Preise je Land, sortiert vom höchsten zum niedrigsten,
in Originalwährung und in EUR, mit Zeitpunkt und Schritt.

Bedienung auf Deutsch oder Englisch, unabhängig von der Sprache des POS; Optik nach dem Vorbild von Google Flights
(eigene Umsetzung, keine Marke, kein Logo). Grundlage: [RESEARCH.md](RESEARCH.md).

## Messregeln (gelten für jeden Lauf)

- **Halt vor jeder Reservierung:** Der Lauf endet vor dem Schritt, der eine Buchung, eine Reservierung (PNR) oder
  das Halten von Plätzen auslöst, und immer vor der Zahlung. Ist das bei einer Seite nicht sicher erkennbar, endet
  er nach der Preisanzeige mit Passagierdaten.
- **Testpersonen statt echter Daten:** Formulare werden mit erfundenen, als solche erkennbaren Daten gefüllt, die
  keiner echten Person gehören; nie mit echten Kundendaten, nie mit Zahlungsdaten.
- **Nur das Land ändert sich:** Je Messung sind Zeitpunkt (gleichzeitig ±1 min), Verbindung, Personen und Browser
  gleich, auch die Sprache (Englisch); variiert werden Ausgangsstandort, Markt und Währung des Landes. Kontrolle: dieselbe Abfrage zweimal aus
  demselben Land (Rauschen durch schwankende Preise, vgl. Vissers et al.).
- **Transparent und schonend:** Abfragen mit niedriger Rate, `robots.txt` beachten, eine Kennung der
  Forschungsgruppe mit Kontaktadresse, wo das geht. Keine Umgehung von Bot-Erkennung oder CAPTCHAs; wird ein Lauf
  geblockt, wird das als Ergebnis protokolliert.
- **Nachvollziehbar:** Jeder Schritt wird mit Zeitstempel, Land, URL, angezeigtem Preis und Bildschirmfoto
  gespeichert; Steuern und Gebühren getrennt, wo die Seite sie zeigt (Unterschiede durch Steuern sind keine
  Preisdiskriminierung).

## Phase 0 – Vorbereitung (Recht, Ethik, Quellen)

- [x] Forschungseinrichtung: Universität Stuttgart (Forschungsorganisation im Sinne von § 60d UrhG)
- [ ] Zweck schriftlich festhalten; klären, ob ein Ethikvotum nötig ist
- [ ] Rechtliche Kurzprüfung: AGB der Seiten vs. § 60d UrhG, Art. 23 Abs. 2 VO 1008/2008 im Wortlaut
- [ ] Liste der Seiten: 5–10 Airlines, 2–3 Portale, Google Flights; je Seite die Schritte bis zum Halt beschreiben
- [ ] Länderzugang über **Cloud-Server**: je Land eine kleine VM in einer Region von AWS, Google Cloud oder Azure
      (zusammen ca. 35 Länder), nur während eines Laufs gestartet; Liste der Länder und Kosten je Messwoche.
      Grenze: Rechenzentrums-Adressen, keine Privatanschlüsse – manche Seiten behandeln sie anders; das wird je Lauf
      protokolliert (Sperre, CAPTCHA, abweichender Markt) und im Bericht genannt
- [ ] Ergänzend: Quellen mit Länderparameter (SerpApi `gl`, Travelpayouts `market`) als Gegenprobe

## Phase 1 – Messwerkzeug

- [x] Playwright-Ablauf für Google Flights (Suche → Hinflug → Rückflug → Buchungsoptionen → Halt), Testläufe:
      [TESTLAEUFE.md](TESTLAEUFE.md)
- [ ] Abläufe für Airline-Seiten (mit Passagierdaten der Testpersonen bis zur Preisübersicht)
- [x] Dasselbe Messwerkzeug auf jeder VM (`scripts/run-all.sh`); ein zentraler Auftrag startet alle gleichzeitig und sammelt die Schritte
      ein (Datenbank + Bildschirmfotos)
- [x] Umrechnung in EUR mit dem Tageskurs zum Messzeitpunkt (Quelle: EZB-Referenzkurse)
- [x] Tests mit nachgebauten Seiten (keine echten Seiten in der CI)

## Phase 1b – Die richtigen Anbieter je Markt

Google Flights zeigt in allen 40 Ländern fast dieselben 5–7 Anbieter (Ergebnis 21.10.2026); lokale Verkäufer fehlen.

- [x] Bericht: Anbieter je Land (`booking-app report`)
- [x] Soll-Liste: je Land die wichtigsten Verkäufer und Vergleich mit Google ([SOLL-ANBIETER.md](SOLL-ANBIETER.md))
- [x] Auswahl für die direkte Messung (Lufthansa-Länderseiten, Opodo, Check24, Netflights, Priceline, PriceTravel,
      MaxMilhas, Ticket, Pelikan)
- [ ] Direkte Messung einzelner Verkäufer (Airline-Länderseiten, ein lokales Reisebüro je Region), Halt vor der Zahlung
- [ ] Konsolidator-Tarife über eine eigene Agentur: [AGENTUR.md](AGENTUR.md)

## Phase 2 – Oberfläche

- [ ] Suche: Von, Nach, Datum(e), Personen, Klasse, Auswahl der Länder – DE/EN
- [ ] Ergebnis: je Verbindung alle Preise je Land von max bis min, Spanne und Abstand zum Median
- [ ] Detail je Land: alle Schritte mit Preis und Bildschirmfoto
- [ ] Export (CSV) für die Auswertung

## Phase 3 – Studie und Auswertung

- [ ] 30 Strecken × 3 Termine × alle Länder, über mehrere Wochen wiederholt
- [ ] Auswertung: Anteil der Verbindungen mit Unterschieden > Rauschen, Größe, betroffene Seiten und Länder,
      Ursachen (Steuern, Währung, Tarif)
- [ ] Bericht

## Technik

FastAPI + Jinja (Oberfläche), Playwright (Messung), serverseitig, keine Skripte im Browser, CSP ohne
`unsafe-inline`; alle Qualitätsregeln aus `CLAUDE.md`.

## Risiken

| Risiko | Gegenmaßnahme |
|---|---|
| Unterschiede gehen im Rauschen unter | Kontrollmessungen aus demselben Land, gleichzeitiger Start |
| Seiten blocken die Messung | protokollieren, Rate senken, Betreiber kontaktieren; nicht umgehen |
| Ein Schritt löst unbemerkt eine Reservierung aus | Halt-Regel je Seite vorab prüfen und dokumentieren |
| AGB-Verstoß | Prüfung in Phase 0, § 60d UrhG, Kontakt zu Betreibern |
| Ausgangsadresse wird nicht als Land erkannt | Standort je Lauf mit einem Geo-IP-Dienst prüfen und speichern |
