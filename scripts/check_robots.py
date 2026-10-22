"""robots.txt of each candidate: reachable, and which flight/search paths it closes to all agents."""

import re
import sys
import urllib.request

AGENT = "Mozilla/5.0 BookingResearch/0.1 (Universitaet Stuttgart; www.contact.com)"
WORDS = re.compile(r"flug|flight|vol|vuelo|voo|search|suche|book|result|offer|fare|air", re.I)

for host in sys.stdin.read().split():
    req = urllib.request.Request(f"https://{host}/robots.txt", headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:  # noqa: S310 - fixed https URLs
            text = r.read(300_000).decode("utf-8", "replace")
    except Exception as e:
        print(f"{host}\tERR {type(e).__name__} {str(e)[:50]}")
        continue
    star, rules = False, []
    for line in text.splitlines():
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            star = value == "*"
        elif star and key == "disallow" and value and WORDS.search(value):
            rules.append(value)
    everything = any(r == "/" for r in rules) or "Disallow: /\n" in text.replace("\r", "")
    print(f"{host}\t{'ALLES GESPERRT ' if everything else ''}{len(rules)} Sperren: {' '.join(rules[:12])[:400]}")
