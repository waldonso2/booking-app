"""One GET per seller site: reachable, where it ends up, its title, and whether it mentions flights."""

import re
import sys
import urllib.error
import urllib.request

AGENT = "Mozilla/5.0 BookingResearch/0.1 (Universitaet Stuttgart; www.contact.com)"
FLIGHT = re.compile(r"flight|flug|vol\b|vols|vuelo|voo|voli|volo|loty|lot\b|letenk|repül|zbor|πτήσ|flyg|fly\b|flybillet|"
                    r"lento|uçuş|ucak|טיס|航空券|航空|항공|pesawat|penerbangan|เที่ยวบิน|vlucht|airfare|air ticket", re.I)
SITES = [line.split() for line in sys.stdin.read().splitlines() if line.strip()]

for country, url in SITES:
    req = urllib.request.Request(f"https://{url}", headers={"User-Agent": AGENT, "Accept-Language": "en,de;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:  # noqa: S310 - fixed https URLs
            body = r.read(400_000).decode("utf-8", "replace")
            title = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
            text = re.sub(r"\s+", " ", title.group(1)).strip()[:70] if title else ""
            print(f"{country}\t{url}\t{r.status}\t{r.url[:60]}\t{'Flug' if FLIGHT.search(body) else '-'}\t{text}")
    except urllib.error.HTTPError as e:
        print(f"{country}\t{url}\t{e.code}\t-\t-\t(blockt oder Fehler)")
    except Exception as e:
        print(f"{country}\t{url}\tERR\t-\t-\t{type(e).__name__}: {str(e)[:60]}")
