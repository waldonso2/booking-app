# Research: günstigster Point of Sale für eine Flugverbindung

Stand: 21.10.2026, erste Runde. Quellen am Ende; was noch nicht an der Primärquelle geprüft ist, steht als
**offen** da.

## 1. Die Annahme: Der Preis hängt vom Point of Sale ab

- Airlines steuern Tarife ausdrücklich nach Point of Sale (POS): Das Revenue-Management prognostiziert die Nachfrage
  nach Strecke, POS und Buchungsklasse, die Preisabteilung nutzt den POS als eigene Dimension (IATA).
- Wie groß die Unterschiede für dieselbe Verbindung sind, ist **nicht belastbar gemessen**. Was es gibt, stammt
  meist von VPN-Anbietern (Eigeninteresse): „5–30 %“, „meist 1–5 %“, teils *höhere* Preise in ärmeren Ländern.
  Ein Hochschulprofessor (NYIT) hält den reinen IP-Trick für weitgehend tot, weil Anbieter den echten Standort
  anders erkennen.
- Am ehesten lohnt es sich bei Regional- und Inlandsflügen, bei Airlines, die im Abflugmarkt günstiger verkaufen,
  und über die Währung (Zahlung in der Landeswährung des POS).

**Folgerung:** Bevor wir eine App bauen, messen wir selbst (Phase 0 im Projektplan). Ohne messbare Ersparnis auf
genug Strecken gibt es kein Produkt.

## 2. Datenquellen

| Quelle | POS/Markt wählbar? | Zugang | Bewertung |
|---|---|---|---|
| Google Flights (über SerpApi o. ä.) | ja, `gl` (Land) und `hl` (Sprache) | kein offizielles API; Drittanbieter scrapen | schnellster Weg für die Messung in Phase 0; laut Google-AGB nicht erlaubt → nur Prototyp, kein Produkt darauf |
| Travelpayouts / Aviasales Data API | ja, `market` | frei mit Partnerkonto | Cache-Preise, nicht live; gut für Vorauswahl |
| Duffel (NDC, buchbar) | **offen** – Doku zum POS nicht gefunden | Self-Service, Kosten pro Buchung | einziger frei zugänglicher Weg, der auch bucht; POS-Steuerung klären |
| Amadeus Self-Service | – | **am 17.07.2026 abgeschaltet** | entfällt; Enterprise nur mit Freigabe |
| Amadeus Enterprise / Sabre / Travelport (GDS) | ja: Office-ID bzw. Pseudo City Code = POS | Vertrag, IATA-Agentur o. Ä. | „echter“ Weg zu POS-Preisen, aber nur mit Partner/Lizenz pro Land |
| Kiwi Tequila | **offen** | Suche Self-Service, Buchung mit Vertrag (laut Drittquelle) | virtuelles Interlining (Selbst-Umstieg) |

**Wichtig:** Ein POS ist in der Branche kein Standort einer IP-Adresse, sondern der Ort der verkaufenden Agentur
(GDS: Office-ID/PCC) bzw. der Markt der Airline-Website. Der saubere Weg zu „allen POS“ ist eine Quelle, die den
Markt als Parameter nimmt, nicht eine vorgetäuschte Herkunft.

## 3. Recht und Regeln

- **EU, Art. 23 Abs. 2 VO (EG) 1008/2008** (Inhalt aus eigener Kenntnis, Wortlaut **offen**): Für Flüge ab einem
  EU-Flughafen muss der Zugang zu öffentlich angebotenen Tarifen ohne Diskriminierung nach Staatsangehörigkeit,
  Wohnort des Kunden oder Sitz des Verkäufers in der EU gewährt werden. Für EU-Abflüge darf also jeder EU-Kunde
  jeden EU-Marktpreis buchen, ohne etwas vorzutäuschen. Das ist unser stärkster legaler Hebel.
- **Geoblocking-VO (EU) 2018/302:** nimmt Verkehrsdienste aus (Art. 1 Abs. 3, Wortlaut **offen**); die Kommission
  verweist auf die Branchenregeln oben. Evaluation 2025 läuft, Ergebnis **offen**.
- **Was die Airline bindet:** Beförderungsbedingungen definieren u. a. das *Land der Zahlung* (wo die Zahlung
  angenommen wird) und das *Land des Reisebeginns*. Tarife können daran gebunden sein.
- **Hidden City:** Lufthansa hat 2019 ihre Berufung gegen einen Passagier zurückgezogen, der die letzte Teilstrecke
  verfallen ließ (AG/LG Berlin). Kein bindender Präzedenzfall; die Airline kann weiter Folgecoupons streichen und
  Gepäck geht bis zum Endziel.

### Grenze für das Produkt

„Dem POS glaubhaft versichern, dass die Buchung aus dem Land erfolgt“ hat zwei Teile, die wir trennen müssen:

1. **Preise eines Marktes sehen:** Über eine Quelle mit Marktparameter ist das unproblematisch. Über Scraping mit
   Proxys im Zielland ist es ein AGB-Verstoß gegenüber der jeweiligen Seite (Sperren, Unterlassung).
2. **Buchen:** Falsche Angaben im Buchungsvorgang (Wohnsitz, Rechnungsadresse, Ausweis für Einwohnertarife) sind
   eine Täuschung des Verkäufers. Folgen: Storno, Nachforderung, Beförderungsverweigerung, im Ernstfall Betrug.
   Das baut die App nicht. Sie bucht mit den echten Daten des Kunden und nutzt nur Hebel, die damit funktionieren.
   Bot-Erkennung zu umgehen, gehört nicht zum Produkt.

## 4. Hebel, die mit echten Daten funktionieren („neue Wege“)

| Hebel | Idee | Prüfen |
|---|---|---|
| POS-Vergleich über Marktparameter | dieselbe Verbindung in allen Märkten einer Quelle abfragen | Phase 0: wie oft und wie viel billiger |
| EU-Nichtdiskriminierung | EU-Abflug: jeden EU-Markt mit echten Daten buchen; wird man abgewiesen, ist das ein Verstoß | Wortlaut, Durchsetzung |
| Währung | im POS-Markt in Landeswährung zahlen, mit Karte ohne Auslandsgebühr; Wechselkurs der Airline vs. Marktkurs | Spread messen |
| Selbst-Umstieg / getrennte Tickets | zwei günstige Tickets statt eines durchgehenden | Risiko Anschluss anzeigen |
| Positionierungsflug | ab einem nahen Flughafen/Land starten, wo der Langstreckentarif billiger ist | Kosten + Zeit |
| Open Jaw / Gabelflug | anderer Rück- als Hinflughafen | Tarifregeln |
| Hidden City | nur als Hinweis mit klaren Risiken, nie Standard | Rechtslage pro Land |
| Einwohner-/Sondertarife | nur wenn der Kunde berechtigt ist (Profil: Wohnsitz, Alter, Studium) | Nachweise |

## Quellen

- [IATA: Dynamic pricing of airline offers](https://www.iata.org/contentassets/0688c780d9ad4a4fadb461b479d64e0d/dynamic-pricing--of-airline-offers.pdf)
- [NYIT: Professor: Don't Rely on VPN Travel Trick](https://www.nyit.edu/?p=57282)
- [Windscribe: VPN for Cheaper Flights (Anbieter)](https://windscribe.com/blog/vpn-for-cheaper-flights/)
- [VPNHub: Cheap flights (Anbieter)](https://vpnhub.it.com/blog/traveling/how-to-get-cheap-flights-and-save-money/)
- [SerpApi: Google Flights API](https://serpapi.com/google-flights-api)
- [Travelpayouts: Aviasales Data API](https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API)
- [Duffel: Getting an accurate price before booking](https://duffel.com/docs/guides/getting-an-accurate-price-before-booking)
- [PhocusWire: Amadeus shuts down self-service APIs portal](https://www.phocuswire.com/amadeus-shut-down-self-service-apis-portal-developers)
- [Sabre: Flight Search API](https://developer.sabre.com/rest-api/flightsearch-api)
- [Kiwi Tequila (Drittquelle)](https://supergood.ai/api-report-card/kiwi)
- [EU-Kommission: Geo-blocking](https://digital-strategy.ec.europa.eu/en/policies/geo-blocking)
- [Slaughter and May: Evaluation der Geoblocking-VO](https://thelens.slaughterandmay.com/post/102k0cd/geo-blocking-in-the-spotlight-european-commission-launches-evaluation-of-legal-f)
- [Hawaiian Airlines: Definitionen (Land der Zahlung)](https://www.hawaiianairlines.co.nz/legal/international-contract-of-carriage/001-definitions)
- [Live and Let's Fly: Lufthansa loses lawsuit](https://liveandletsfly.com/lufthansa-loses-lawsuit/)
- [Aryal, Murry, Williams: Price discrimination in international airline markets (NBER)](https://www.nber.org/system/files/working_papers/w28989/w28989.pdf)
