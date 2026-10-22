#!/usr/bin/env bash
# Fetches release manifest from the artifact store (simulated for local runs).
set -euo pipefail
echo "fetching manifest for release ${RELEASE:-latest}..."
roll=$(( $(od -An -N2 -tu2 /dev/urandom) % 100 ))
sleep 0.05
if [ "$roll" -lt 22 ]; then
  echo "curl: (56) Recv failure: Connection reset by peer (attempt 1, host artifacts-$((roll%3)).internal)" >&2
  exit 56
fi
if [ "$roll" -lt 27 ]; then
  echo "error: manifest checksum mismatch (expected sha256:ab12..., got sha256:$(printf '%04x' $roll)...)" >&2
  exit 3
fi
echo "ok: manifest 4 entries"
