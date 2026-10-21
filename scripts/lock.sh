#!/usr/bin/env bash
# Regenerates requirements.txt (every runtime dependency of pyproject.toml and the build backend, at an exact
# version with its hashes, for every supported Python and platform) and requirements-dev.txt (the CI's tools,
# constrained to those versions). Run after changing a dependency; `--upgrade` moves everything to the newest.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null || { echo "uv is needed: pip install uv" >&2; exit 1; }
uv pip compile pyproject.toml requirements-build.in --universal --python-version 3.11 \
  --generate-hashes --no-header --annotation-style line --quiet "$@" -o requirements.txt
uv pip compile requirements-dev.in -c requirements.txt --universal --python-version 3.11 \
  --generate-hashes --no-header --annotation-style line --quiet "$@" -o requirements-dev.txt
