#!/usr/bin/env bash
# One measurement from many countries at once. HOSTS lists one cloud VM per line: "<country> <ssh target>", e.g.
# "US ubuntu@203.0.113.10" (Ubuntu 24.04, any provider). Everything after -- goes to `booking-app measure`.
#
#   scripts/run-all.sh hosts.txt -- --from FRA --to ATL --depart 2027-03-26 --return 2027-04-09 \
#     --cabin business --contact studie@example.org
#
# 1. copies this checkout to every VM and installs it there (locked versions, Chromium) - in parallel
# 2. starts the measurement on all VMs at the same moment
# 3. fetches each VM's results to data/runs/<time>/<country>/ and imports them (booking-app import)
set -euo pipefail
cd "$(dirname "$0")/.."
hosts=$1; shift
[ "${1:-}" = "--" ] && shift
stamp=$(date -u +%Y%m%dT%H%M%SZ)
mapfile -t lines < <(grep -v '^\s*\(#\|$\)' "$hosts")
ssh_opts=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new)

setup() {
  rsync -a --delete --exclude .git --exclude .venv --exclude data -e "ssh ${ssh_opts[*]}" ./ "$1:booking-app/"
  # shellcheck disable=SC2016 # expanded on the VM
  ssh "${ssh_opts[@]}" "$1" 'set -e; cd booking-app
    command -v python3 >/dev/null && python3 -m venv --help >/dev/null 2>&1 || sudo apt-get install -y python3-venv
    [ -d .venv ] || python3 -m venv .venv
    .venv/bin/pip install -q --require-hashes --only-binary :all: -r requirements.txt
    .venv/bin/pip install -q --no-deps --no-build-isolation -e .
    sudo .venv/bin/python -m playwright install-deps chromium >/dev/null
    .venv/bin/python -m playwright install chromium >/dev/null'
}

echo "Einrichten: ${#lines[@]} VMs"
for line in "${lines[@]}"; do read -r _ target <<<"$line"; setup "$target" & done
wait

echo "Messen ($stamp)"
for line in "${lines[@]}"; do
  read -r country target <<<"$line"
  args=$(printf '%q ' "$@")
  # shellcheck disable=SC2029 # country, stamp and args are meant to expand here
  ssh "${ssh_opts[@]}" "$target" "cd booking-app && .venv/bin/booking-app measure --country $country \
    --out runs/$stamp/$country $args" || true &
done
wait

for line in "${lines[@]}"; do
  read -r country target <<<"$line"
  mkdir -p "data/runs/$stamp"
  rsync -a -e "ssh ${ssh_opts[*]}" "$target:booking-app/runs/$stamp/$country" "data/runs/$stamp/" || \
    echo "$country: keine Ergebnisse" >&2
done
booking-app import "data/runs/$stamp"
