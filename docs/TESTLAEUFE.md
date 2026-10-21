# Testläufe

Zwei Testläufe, beide Business, ein Erwachsener, Hinflug Ende März, Rückflug zwei Wochen später:

| Lauf | Verbindung | Hinflug | Rückflug |
|---|---|---|---|
| 1 | Frankfurt (FRA) → Atlanta (ATL) | 26.03.2027 | 09.04.2027 |
| 2 | Frankfurt (FRA) → Manila (MNL) | 26.03.2027 | 09.04.2027 |

## Was ein Lauf macht

Je Land auf einer VM in diesem Land (`src/booking/measure.py`, Seite: Google Flights):

1. `robots.txt` der Seite lesen; verbietet sie den Abruf, endet der Lauf mit Status `robots` (kein Browser).
2. Suche öffnen (`hl=en` überall gleich, `gl` = Land, `curr` = Landeswährung); Cookie-Abfrage mit „Reject all“.
3. **Hinflug:** alle Flüge mit Preis; weiter mit dem Flug, der den Text von `--pick` enthält (sonst dem ersten).
4. **Rückflug:** alle Rückflüge mit Preis; weiter mit dem ersten.
5. **Buchungsoptionen:** alle Anbieter mit Preis. **Hier endet der Lauf** – der nächste Klick führte zur Buchung.

Jeder Schritt: Preise, URL, Bildschirmfoto und Kopie der Seite in `runs/<Zeit>/<Land>/`. Eine Sperrseite
(„unusual traffic“, CAPTCHA) beendet den Lauf mit Status `blocked`, ein Fehler mit `error` und Bildschirmfoto.
Gespeichert wird auch, in welchem Land ein Geo-IP-Dienst die VM sieht, und ob die Seite die Klasse „business“
anzeigt (sonst stimmt die Suche nicht).

Der Browser meldet sich mit `BookingResearch/0.1 (Universitaet Stuttgart; <Kontakt>)` im User-Agent.

## Vorbereitung

1. **VMs:** je Land eine kleine VM (2 vCPU, 4 GB, Ubuntu 24.04) in einer Region dieses Landes, SSH-Zugang mit
   Schlüssel und `sudo`. Mögliche Länder stehen in `COUNTRIES` (`measure.py`); welche Region bei welchem Anbieter
   in welchem Land liegt, steht in deren Regionslisten. Für die Testläufe reichen 3–5 Länder, z. B. DE, US, GB, JP,
   SG.
2. **`hosts.txt`** (nicht im Repo) im Projektordner, eine Zeile je VM:

   ```text
   DE ubuntu@198.51.100.10
   US ubuntu@203.0.113.20
   JP ubuntu@192.0.2.30
   ```

3. Lokal: `rsync`, `ssh` und das Projekt installiert (README, „Entwickeln“).

## Durchführen

```bash
# Lauf 1: einmal aus DE, um den Flug für --pick zu wählen (z. B. "Lufthansa" oder "Delta")
scripts/run-all.sh hosts.txt -- --from FRA --to ATL --depart 2027-03-26 --return 2027-04-09 \
  --cabin business --contact <e-mail der Gruppe> --pick "Lufthansa"

# Lauf 2
scripts/run-all.sh hosts.txt -- --from FRA --to MNL --depart 2027-03-26 --return 2027-04-09 \
  --cabin business --contact <e-mail der Gruppe> --pick "<Airline>"

booking-app serve     # Ergebnis: http://127.0.0.1:8000 – je Verbindung alle Preise von max bis min
```

`--pick` sorgt dafür, dass in jedem Land derselbe Hinflug weiterverfolgt wird; ohne ihn nimmt jedes Land seinen
ersten Treffer, und die Buchungsoptionen gehören dann zu verschiedenen Flügen.

## Grenzen der ersten Version

- Gegen die echte Seite ist der Ablauf noch **nicht** gelaufen (aus der Entwicklungsumgebung nicht erreichbar).
  Die Schritte erkennen Preise am Text (`PRICE`) und klicken die Zeile mit dem gewählten Flug; ändert die Seite ihr
  Layout, zeigen Bildschirmfoto und Seitenkopie, wo es hakt.
- Die Euro-Umrechnung nutzt den EZB-Referenzkurs vom Tag des Imports.
- Nur Google Flights; Airline-Seiten mit Passagierdaten sind der nächste Schritt (Projektplan, Phase 1).
