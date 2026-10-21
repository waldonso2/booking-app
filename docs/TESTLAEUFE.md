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

## Studie: 40 Länder (GitHub)

*Actions → Messung (40 Länder) → Run workflow* misst eine Verbindung für 40 Points of Sale gleichzeitig (je Land
ein Job, max. 20 parallel). Je Job werden Google Flights' Einstellung „Location“ (`gl`) und die Landeswährung
gesetzt; der Job `report` importiert alle Läufe (EUR über EZB-Kurs) und schreibt alle Preise der Buchungsoptionen,
vom höchsten zum niedrigsten, und den günstigsten Preis je Land auf die Zusammenfassungsseite.

**Grenze:** Die Runner stehen in den USA. Gemessen wird, was Google für das eingestellte Land anzeigt, nicht was
jemand aus dem Netz dieses Landes sähe – dafür braucht es VMs im Land (`scripts/run-all.sh`).

### Ergebnis 21.10.2026, FRA–ATL, Business, 26.03.–09.04.2027 (Hinflug 10:30 Uhr, Lufthansa nonstop)

- 40 von 40 Ländern mit Ergebnis, 239 Preise in den Buchungsoptionen (je Land 5–7 Anbieter).
- Höchster Preis: 4.184,04 EUR (Mexiko, Gotogate, 86.874 MXN); niedrigster: 4.014,90 EUR (Polen,
  business-class.com, 17.519 PLN).
- Günstigster Anbieter in **jedem** Land: business-class.com. Dessen Preis je Land liegt zwischen 4.014,90 EUR (PL)
  und 4.061,46 EUR (MX), Spanne 46,56 EUR (1,2 %); ohne Mexiko 15,45 EUR (0,4 %).
- Alle 12 Euro-Länder zeigen exakt denselben Preis (4.022 EUR). Die Abweichungen der übrigen Länder liegen in der
  Größenordnung der Wechselkursdifferenz zwischen Googles Umrechnung und dem EZB-Kurs.
- **Befund:** Über Googles Ländereinstellung zeigt sich für diese Verbindung keine nennenswerte Preisdifferenzierung
  je Point of Sale; Google rechnet offenbar einen Preis in die Landeswährung um. Mexiko (+1 %) ist der einzige
  Ausreißer. Ob sich das mit Zugriff aus dem jeweiligen Land ändert, prüft erst die Messung über VMs.

## Testlauf aus den USA (GitHub)

Ohne eigene VMs läuft eine Messung aus den USA auf einem GitHub-Runner: *Actions → Messung (USA) → Run workflow*
(Kontakt und `--pick` als Eingaben). Beide Testläufe laufen dort durch – Suche, Hinflug, Rückflug,
Buchungsoptionen –, Ergebnis auf der Zusammenfassungsseite des Laufs und als Artefakt `runs-<Ziel>`.

Erster erfolgreicher Lauf (21.10.2026, aus den USA, Preise in USD, Hinflug 26.03.2027, Rückflug 09.04.2027):

| Verbindung | Anbieter | Preis | beim Anbieter |
|---|---|---|---|
| FRA–ATL | business-class.com | 4.516 USD | 4.022 EUR |
| FRA–ATL | United (Markt USA) | 4.626 USD | – |
| FRA–ATL | Lufthansa | 4.630 USD | 4.123 EUR |
| FRA–ATL | United (Markt Deutschland) | 4.630 USD | 4.123 EUR |
| FRA–ATL | Tripado | 4.640 USD | 4.132 EUR |
| FRA–ATL | Gotogate | 4.653 USD | – |
| FRA–MNL | Gulf Air | 2.790 USD | 2.485 EUR |
| FRA–MNL | Logitravel | 2.790 USD | 2.485 EUR |
| FRA–MNL | business-class.com | 2.930 USD | 2.609 EUR |
| FRA–MNL | Travomint | 2.930 USD | 2.609 EUR |

Schon ein Land zeigt Unterschiede je Point of Sale: United bietet denselben Flug „nach US-Recht“ für 4.626 USD
und „nach deutschem Recht“ für 4.630 USD (4.123 EUR) an. Die Spalte „beim Anbieter“ ist der Preis in der Währung
der Buchungsseite (Google: „Equivalent to … on …“); er steht im Label jeder Zeile.

## Grenzen der ersten Version

- Die Schritte sind auf Google Flights abgestimmt (Fluglinks „Select flight“, Anbieterpreise mit `data-gs`);
  ändert Google das Layout, zeigen Bildschirmfoto, Seitenkopie und `*.rows.html`, wo es hakt.
- Der Lauf über GitHub misst nur aus den USA; der Ländervergleich braucht die VMs (oben).
- Die Euro-Umrechnung nutzt den EZB-Referenzkurs vom Tag des Imports.
- Nur Google Flights; Airline-Seiten mit Passagierdaten sind der nächste Schritt (Projektplan, Phase 1).
