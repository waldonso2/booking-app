# Messrechner im Land

Regel der Studie: Eine Messung zählt nur, wenn sie aus dem Land kommt, dessen Point of Sale gemessen wird. Jeder
Lauf hält fest, wo seine Adresse liegt (`ip_country`, laut ipinfo.io); `booking-app report` wertet nur Läufe, deren
Adresse im gemessenen Land liegt, und führt die anderen unter „Nicht aus dem Land gemessen (nicht gewertet)“ auf.
Die bisherigen Läufe von GitHub (Rechner in den USA) zählen damit nur für die USA.

## Wege zu Rechnern im Land

| Weg | Länder | Aufwand | Anmerkung |
|---|---|---|---|
| **Partner im Land** (Uni, Kolleg:innen) führen das Messpaket einmal aus | alle 40 | ein Befehl, Docker | kein Konto, keine Kosten, echter Anschluss im Land; Ergebnis kommt als Datei zurück |
| **Cloud-VMs** (Azure, AWS, Google Cloud, Vultr) über ein Konto der Uni | 31 von 40 | Konto mit Bezahlweg; `scripts/run-all.sh` | Rechenzentrums-Adressen; manche Seiten behandeln sie anders als Privatanschlüsse |
| Browser-Testdienste mit IP-Standort (BrowserStack, LambdaTest/TestMu) | 45–60 Länder | Vertrag | Standortwahl bei BrowserStack nur im Enterprise-Tarif, bei LambdaTest nicht im Testkonto |
| Proxy-Netze (z. B. Bright Initiative, Programm für Hochschulen) | viele | Antrag | nur mit Einwilligung der Anschlussinhaber vertretbar; Freischaltung und Umfang beim Anbieter klären |

Nicht genutzt werden offene Proxys und Tor: Offene Proxys laufen oft über fremde, gekaperte Rechner, Tor verschleiert
die Herkunft. Beides passt nicht zu den Messregeln (Studie offen benennen, keine Sperren umgehen).

**Empfehlung:** die 9 Länder ohne Cloud-Region (BG, CZ, GR, HU, IS, PH, PT, RO, TR) über Partner im Land; die übrigen
31 über Partner oder, wenn die Uni ein Cloud-Konto bereitstellt, über VMs. Ansprechpartner für Partner sind z. B. das
Internationale Büro (Erasmus- und Austauschpartner) und die eigenen Fachkontakte; für ein Cloud-Konto das TIK
(Rahmenverträge wie GÉANT OCRE).

### Cloud-Regionen je Land (Stand 23.10.2026, laut den Regionslisten der Anbieter – vor Buchung prüfen)

| Land | Anbieter mit Region im Land |
|---|---|
| AT | Azure |
| AU, BR, CA, DE, ES, FR, GB, IN, IT, JP, KR, SE, SG, US, ZA | AWS, Google Cloud, Azure (meist auch Vultr) |
| BE | Google Cloud, Azure |
| CH, HK, ID, IL | AWS, Google Cloud, Azure |
| DK, NO | Azure |
| FI | Google Cloud |
| IE, MY, NZ | AWS, Azure |
| MX | AWS, Azure, Vultr |
| NL, PL | Google Cloud, Azure, Vultr |
| TH | AWS, Google Cloud |
| **BG, CZ, GR, HU, IS, PH, PT, RO, TR** | **keiner** (Griechenland: Azure und Google angekündigt; Türkei: Google angekündigt) |

AWS-Regionen in MX, MY, NZ, TH und weiteren müssen im Konto erst freigeschaltet werden (opt-in).

## Messpaket für Partner

1. Paket erzeugen (im Repository): `git archive --format=zip -o messpaket.zip HEAD` und an den Partner schicken.
2. Partner (braucht nur Docker):

   ```bash
   unzip messpaket.zip -d messpaket && cd messpaket
   ./scripts/messen-im-land.sh PH studie@uni-stuttgart.de
   ```

   Das misst Google Flights und CHECK24 für die Standardverbindung (FRA–ATL, Business, 26.03.–09.04.2027; andere
   über `FROM`, `TO`, `DEPART`, `RETURN`, `CABIN`) in einem Container, der danach gelöscht wird, und legt
   `ergebnisse/<Land>-<Zeit>.tar.gz` an.
3. Partner schickt die Datei zurück; wir entpacken sie nach `data/runs/` und rufen `booking-app import data/runs`
   und `booking-app report` auf.

Damit die Preise vergleichbar sind, sollten alle Partner am selben Tag messen (Flugpreise ändern sich laufend).

### Text für Partner (Englisch)

> We are a research group at the University of Stuttgart studying whether airlines and travel sites show different
> prices for the same flight depending on the country a customer is in. Could you run one measurement from your
> computer? It needs Docker and takes about five minutes: unzip the attached package and run
> `./scripts/messen-im-land.sh <your country code> <our e-mail>`. A browser in a temporary container opens public
> flight search pages up to the last price before booking; nothing is booked and no personal data is entered. Please
> send us the `.tar.gz` file it creates. The container is deleted afterwards.

## Quellen

- [Azure: List of regions](https://learn.microsoft.com/en-us/azure/reliability/regions-list)
- [AWS: Regions](https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html)
- [Google Cloud: Region Bangkok (21.01.2026)](https://cloud.google.com/blog/products/infrastructure/google-cloud-launches-new-region-in-bangkok-thailand),
  [Standorte](https://dgtlinfra.com/google-cloud-data-center-locations/)
- [Vultr: Rechenzentren](https://www.vultr.com/features/datacenter-regions/)
- [BrowserStack: IP-Geolocation mit Playwright](https://www.browserstack.com/docs/automate/playwright/ip-geolocation)
- [TestMu AI (LambdaTest): Standorte](https://www.testmuai.com/list-of-geolocation/)
- [Bright Initiative](https://www.thesilab.com/vendor-directory/bright-initiative-by-bright-data)
