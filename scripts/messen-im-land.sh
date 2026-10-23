#!/usr/bin/env bash
# One measurement of the University of Stuttgart's flight price study from the country this computer stands in.
# For partners: run it once, then send the .tar.gz it names back to the study team. Needs only Docker; everything
# runs in a container that is deleted afterwards. A browser opens public flight search pages (Google Flights,
# CHECK24) up to the last price before booking - nothing is booked, no personal data is entered.
#
#   ./scripts/messen-im-land.sh <country code> <contact e-mail of the study>     e.g.  ./scripts/messen-im-land.sh PH study@uni-stuttgart.de
#
# The flight comes from FROM, TO, DEPART, RETURN, CABIN (defaults: FRA-ATL, 2027-03-26 to 2027-04-09, business).
set -euo pipefail
cd "$(dirname "$0")/.."
[ $# -eq 2 ] || { sed -n '2,9p' "$0"; exit 2; }
country=$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]')
[[ $country =~ ^[A-Z]{2}$ ]] || { echo "country code: two letters, e.g. PH" >&2; exit 2; }
command -v docker >/dev/null || { echo "Docker is needed: https://docs.docker.com/get-docker/" >&2; exit 1; }
name="$country-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "ergebnisse/$name"

# Playwright's own image (Chromium and its libraries); its version is the study's locked playwright.
docker run --rm -v "$PWD:/src:ro" -v "$PWD/ergebnisse/$name:/out" -e COUNTRY="$country" -e CONTACT="$2" \
  -e FROM="${FROM:-FRA}" -e TO="${TO:-ATL}" -e DEPART="${DEPART:-2027-03-26}" -e RETURN="${RETURN:-2027-04-09}" \
  -e CABIN="${CABIN:-business}" mcr.microsoft.com/playwright/python:v1.64.0-noble bash -c '
  set -euo pipefail
  cp -r /src /tmp/app && cd /tmp/app && rm -rf .venv
  python3 -m venv .venv 2>/dev/null || { apt-get update -qq && apt-get install -y -qq python3-venv >/dev/null
                                         python3 -m venv .venv; }
  .venv/bin/pip install -q --require-hashes --only-binary :all: -r requirements.txt
  .venv/bin/pip install -q --no-deps --no-build-isolation -e .
  q=(--country "$COUNTRY" --from "$FROM" --to "$TO" --depart "$DEPART" --return "$RETURN" --cabin "$CABIN"
     --contact "$CONTACT")
  .venv/bin/booking-app measure --site google-flights "${q[@]}" --pick "10:30 AM" --out /out/google-flights || true
  .venv/bin/booking-app measure --site check24 "${q[@]}" --pick Lufthansa --out /out/check24 || true'

tar czf "ergebnisse/$name.tar.gz" -C ergebnisse "$name"
echo "Done. Please send ergebnisse/$name.tar.gz to the study team."
